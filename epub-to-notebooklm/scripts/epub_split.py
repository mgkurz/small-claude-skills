#!/usr/bin/env python3
"""epub_split.py — EPUB für NotebookLM aufbereiten (Stdlib-only).

Liest ein DRM-freies EPUB, säubert es nach Markdown und gibt es entweder als
eine Quelle (Einzeldatei) oder nach Abschnitten gesplittet aus.

Keine externen Abhängigkeiten: nur die Python-Standardbibliothek.

Strategie der Abschnittsfindung (robust, nach Verlags-TOC):
1. Wahrheit ist die TOC des EPUB, nicht Überschriften im Fließtext.
   EPUB3: nav.xhtml (epub:type="toc"), bevorzugt. EPUB2: toc.ncx, Fallback.
2. Lesereihenfolge kommt aus dem OPF-Spine.
3. Front-/Back-Matter (Cover, Copyright, Inhaltsverzeichnis, Index, Notes,
   Danksagung) wird per nav-Landmarks / epub:type / Dateinamen erkannt und
   per Default weggefiltert, um Rauschen in NotebookLM zu vermeiden.

NotebookLM-Limits (Stand Juni 2026): 500.000 Wörter pro Quelle,
50 Quellen (Free) / 100 (Plus). Das Skript warnt bei Annäherung.
"""

from __future__ import annotations

import argparse
import os
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

# --- Konstanten -----------------------------------------------------------

# NotebookLM-Grenzwerte (Juni 2026).
WORDS_PER_SOURCE = 500_000
FREE_SOURCE_LIMIT = 50
# Unterhalb dieser Gesamtwortzahl empfiehlt sich eine einzige Quelle.
SINGLE_SOURCE_THRESHOLD = WORDS_PER_SOURCE

# epub:type-Werte, die als Rauschen gelten und per Default gedroppt werden.
DROP_TYPES = {
    "cover", "titlepage", "halftitlepage", "copyright-page", "copyright",
    "dedication", "toc", "contents", "landmarks", "page-list", "index",
    "endnotes", "notes", "footnotes", "imprint", "colophon",
    "acknowledgments", "acknowledgements", "other-credits",
}

# Dateinamen-Präfixe als Fallback, wenn kein epub:type bekannt ist.
DROP_NAME_PREFIXES = (
    "cover", "toc", "copy", "ded", "index", "notes", "note",
    "title", "half", "nav", "also", "colophon", "ack",
)

# Inline-Tags und ihre Markdown-Umrandung.
INLINE_WRAP = {"em": "*", "i": "*", "strong": "**", "b": "**", "code": "`"}

# Tags, deren Inhalt komplett verworfen wird.
DROP_TAGS = {"script", "style", "svg", "head", "title", "link", "meta", "figure"}

# Void- / selbstschließende Tags ohne eigenes End-Tag (zählen nicht für Tiefe).
VOID_TAGS = {"img", "br", "hr", "meta", "link", "input", "col", "area",
             "base", "source", "wbr", "track", "embed", "param"}

HEADING_LEVEL = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


# --- XML-Helfer -----------------------------------------------------------

def _strip_ns(tag: str) -> str:
    """'{namespace}local' -> 'local'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _local_attrs(el: ET.Element) -> dict:
    """Attribute mit von Namespaces befreiten Schlüsseln (lowercase)."""
    return {_strip_ns(k).lower(): v for k, v in el.attrib.items()}


def _parse_xml(data: bytes) -> ET.Element:
    return ET.fromstring(data)


# --- EPUB-Modell ----------------------------------------------------------

class Epub:
    """Minimaler EPUB-Leser auf Basis von zipfile + ElementTree."""

    def __init__(self, path: str):
        self.path = path
        self.zip = zipfile.ZipFile(path)
        self.opf_path = self._find_opf()
        self.opf_dir = posixpath.dirname(self.opf_path)
        root = _parse_xml(self.zip.read(self.opf_path))
        self.version = root.attrib.get("version", "")
        self.meta = self._read_metadata(root)
        self.manifest = self._read_manifest(root)   # id -> {href, type, props}
        self.spine = self._read_spine(root)          # Liste resolved hrefs (Zip-Pfade)
        # file (Zip-Pfad) -> epub:type aus Landmarks
        self.landmark_types: dict[str, str] = {}
        # file -> (label, depth) aus der TOC
        self.toc: dict[str, tuple[str, int]] = {}
        self._read_toc()

    # -- Zip / Pfade --

    def read_text(self, zip_path: str) -> str:
        return self.zip.read(zip_path).decode("utf-8", errors="replace")

    def _resolve(self, href: str) -> str:
        """href relativ zum OPF (oder TOC-Dir) -> normalisierter Zip-Pfad, ohne Fragment."""
        href = href.split("#", 1)[0]
        return posixpath.normpath(posixpath.join(self.opf_dir, href))

    # -- OPF --

    def _find_opf(self) -> str:
        container = _parse_xml(self.zip.read("META-INF/container.xml"))
        for el in container.iter():
            if _strip_ns(el.tag) == "rootfile":
                return _local_attrs(el)["full-path"]
        raise ValueError("Keine OPF-Datei in container.xml gefunden.")

    def _read_metadata(self, root: ET.Element) -> dict:
        meta = {"title": "", "author": "", "identifier": "", "language": ""}
        for el in root.iter():
            name = _strip_ns(el.tag)
            text = (el.text or "").strip()
            if name == "title" and not meta["title"]:
                meta["title"] = text
            elif name == "creator" and not meta["author"]:
                meta["author"] = text
            elif name == "identifier" and not meta["identifier"]:
                meta["identifier"] = text
            elif name == "language" and not meta["language"]:
                meta["language"] = text
        return meta

    def _read_manifest(self, root: ET.Element) -> dict:
        manifest = {}
        for el in root.iter():
            if _strip_ns(el.tag) != "item":
                continue
            a = _local_attrs(el)
            manifest[a.get("id", "")] = {
                "href": a.get("href", ""),
                "type": a.get("media-type", ""),
                "props": a.get("properties", ""),
            }
        return manifest

    def _read_spine(self, root: ET.Element) -> list[str]:
        order = []
        for el in root.iter():
            if _strip_ns(el.tag) != "itemref":
                continue
            a = _local_attrs(el)
            item = self.manifest.get(a.get("idref", ""))
            if item and item["href"]:
                order.append(self._resolve(item["href"]))
        return order

    # -- TOC + Landmarks --

    def _nav_href(self) -> str | None:
        for item in self.manifest.values():
            if "nav" in item.get("props", "").split():
                return self._resolve(item["href"])
        return None

    def _ncx_href(self) -> str | None:
        for item in self.manifest.values():
            if item["type"] == "application/x-dtbncx+xml":
                return self._resolve(item["href"])
        return None

    def _read_toc(self) -> None:
        nav = self._nav_href()
        if nav:
            try:
                self._parse_nav(nav)
                if self.toc:
                    return
            except ET.ParseError:
                pass
        ncx = self._ncx_href()
        if ncx:
            try:
                self._parse_ncx(ncx)
            except ET.ParseError:
                pass

    def _parse_nav(self, nav_path: str) -> None:
        base = posixpath.dirname(nav_path)
        root = _parse_xml(self.zip.read(nav_path))
        for nav in root.iter():
            if _strip_ns(nav.tag) != "nav":
                continue
            ntype = _local_attrs(nav).get("type", "")
            if ntype == "toc":
                self._walk_nav_ol(nav, base, depth=0)
            elif ntype == "landmarks":
                self._walk_landmarks(nav, base)

    def _walk_nav_ol(self, container: ET.Element, base: str, depth: int) -> None:
        # Direkte <ol> finden, dann deren <li>.
        for child in container:
            if _strip_ns(child.tag) == "ol":
                for li in child:
                    if _strip_ns(li.tag) != "li":
                        continue
                    a = self._first_anchor(li)
                    if a is not None:
                        href = _local_attrs(a).get("href", "")
                        label = _text_of(a)
                        if href and label:
                            f = posixpath.normpath(posixpath.join(base, href.split("#", 1)[0]))
                            self.toc.setdefault(f, (label, depth))
                    # tiefer absteigen für verschachtelte Listen
                    self._walk_nav_ol(li, base, depth + 1)

    def _walk_landmarks(self, nav: ET.Element, base: str) -> None:
        for a in nav.iter():
            if _strip_ns(a.tag) != "a":
                continue
            at = _local_attrs(a)
            href, etype = at.get("href", ""), at.get("type", "")
            if href and etype:
                f = posixpath.normpath(posixpath.join(base, href.split("#", 1)[0]))
                self.landmark_types.setdefault(f, etype.lower())

    @staticmethod
    def _first_anchor(li: ET.Element) -> ET.Element | None:
        for el in li:
            if _strip_ns(el.tag) == "a":
                return el
        return None

    def _parse_ncx(self, ncx_path: str) -> None:
        base = posixpath.dirname(ncx_path)
        root = _parse_xml(self.zip.read(ncx_path))
        nav_map = None
        for el in root.iter():
            if _strip_ns(el.tag) == "navMap":
                nav_map = el
                break
        if nav_map is not None:
            self._walk_navpoints(nav_map, base, depth=0)

    def _walk_navpoints(self, parent: ET.Element, base: str, depth: int) -> None:
        for np in parent:
            if _strip_ns(np.tag) != "navPoint":
                continue
            label, src = "", ""
            for el in np:
                tag = _strip_ns(el.tag)
                if tag == "navLabel":
                    label = _text_of(el)
                elif tag == "content":
                    src = _local_attrs(el).get("src", "")
            if src and label:
                f = posixpath.normpath(posixpath.join(base, src.split("#", 1)[0]))
                self.toc.setdefault(f, (label, depth))
            # verschachtelte navPoints
            self._walk_navpoints(np, base, depth + 1)

    # -- Klassifikation --

    def type_of(self, zip_path: str) -> str:
        """Bekannter epub:type (aus Landmarks) oder ''."""
        return self.landmark_types.get(zip_path, "")

    def is_dropped(self, zip_path: str, keep_front_back: bool) -> bool:
        if keep_front_back:
            return False
        etype = self.type_of(zip_path)
        if etype:
            return etype in DROP_TYPES
        # Fallback: Dateiname
        name = posixpath.basename(zip_path).lower()
        return any(name.startswith(p) for p in DROP_NAME_PREFIXES)

    def is_part(self, zip_path: str) -> bool:
        if self.type_of(zip_path) == "part":
            return True
        return posixpath.basename(zip_path).lower().startswith("part")

    def label_of(self, zip_path: str) -> str | None:
        entry = self.toc.get(zip_path)
        return entry[0] if entry else None


def _text_of(el: ET.Element) -> str:
    """Gesamten Textinhalt eines Elements einsammeln, Whitespace normalisiert."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


# --- HTML -> Markdown -----------------------------------------------------

class MarkdownConverter(HTMLParser):
    """Wandelt XHTML-Body in schlankes Markdown. Bewusst tolerant."""

    def __init__(self, keep_images: bool = False):
        super().__init__(convert_charrefs=True)
        self.keep_images = keep_images
        self.blocks: list[str] = []   # fertige Markdown-Blöcke
        self.buf: list[str] = []      # Inline-Puffer des aktuellen Blocks
        self.skip_depth = 0           # >0: Inhalt verwerfen
        self.quote_depth = 0
        self.list_stack: list[list] = []  # je Ebene: ["ul"| "ol", counter]
        self.heading = 0              # aktuelles Heading-Level oder 0
        self.in_body = False

    # -- Hilfen --

    def _flush(self, prefix: str = "") -> None:
        text = re.sub(r"[ \t]+", " ", "".join(self.buf)).strip()
        self.buf = []
        if not text:
            return
        if self.quote_depth:
            prefix = "> " * self.quote_depth + prefix
        self.blocks.append(prefix + text)

    def _list_prefix(self) -> str:
        indent = "  " * (len(self.list_stack) - 1)
        kind, counter = self.list_stack[-1]
        if kind == "ol":
            self.list_stack[-1][1] += 1
            return f"{indent}{counter}. "
        return f"{indent}- "

    # -- Parser-Callbacks --

    def handle_starttag(self, tag, attrs):
        if tag == "body":
            self.in_body = True
            return
        if self.skip_depth:
            # Innerhalb eines gedroppten Teilbaums: Tiefe nur für echte
            # Container-Tags erhöhen, Void-Tags zählen nicht.
            if tag not in VOID_TAGS:
                self.skip_depth += 1
            return
        if tag in DROP_TAGS:
            self.skip_depth = 1
            return
        if tag == "a":
            # Fußnoten-/Endnoten-Verweise verwerfen (Marker ohne Ziel nach Filter).
            a = dict(attrs)
            etype = (a.get("epub:type", "") + " " + a.get("role", "")).lower()
            if "noteref" in etype:
                self.skip_depth = 1
            return  # normaler Link: Text fließt, kein Markup
        if tag in HEADING_LEVEL:
            self._flush()
            self.heading = HEADING_LEVEL[tag]
        elif tag in ("p", "div", "section", "article", "header", "aside",
                     "figcaption", "tr"):
            self._flush()
        elif tag == "blockquote":
            self._flush()
            self.quote_depth += 1
        elif tag in ("ul", "ol"):
            self._flush()
            self.list_stack.append([tag, 1])
        elif tag == "li":
            self._flush()
        elif tag == "br":
            self.buf.append("\n")
        elif tag == "img" and self.keep_images:
            alt = dict(attrs).get("alt", "").strip()
            if alt:
                self.buf.append(f"![{alt}]()")
        elif tag in INLINE_WRAP:
            self.buf.append(INLINE_WRAP[tag])

    def handle_startendtag(self, tag, attrs):
        # Selbstschließende Tags (<img/>, <br/>, <span .../>): kein Tiefenwechsel.
        if self.skip_depth:
            return
        if tag == "br":
            self.buf.append("\n")
        elif tag == "img" and self.keep_images:
            alt = dict(attrs).get("alt", "").strip()
            if alt:
                self.buf.append(f"![{alt}]()")
        # andere selbstschließende Tags (z. B. pagebreak-span) tragen keinen Text

    def handle_endtag(self, tag):
        if tag == "body":
            self.in_body = False
            return
        if self.skip_depth:
            if tag not in VOID_TAGS:
                self.skip_depth -= 1
            return
        if tag in HEADING_LEVEL:
            self._flush("#" * self.heading + " ")
            self.heading = 0
        elif tag in ("p", "div", "section", "article", "header", "aside",
                     "figcaption", "tr"):
            self._flush()
        elif tag == "blockquote":
            self._flush()
            if self.quote_depth:
                self.quote_depth -= 1
        elif tag in ("ul", "ol"):
            self._flush()
            if self.list_stack:
                self.list_stack.pop()
        elif tag == "li":
            prefix = self._list_prefix() if self.list_stack else "- "
            self._flush(prefix)
        elif tag in INLINE_WRAP:
            self.buf.append(INLINE_WRAP[tag])

    def handle_data(self, data):
        if self.skip_depth or not self.in_body:
            return
        self.buf.append(data)

    # -- Ergebnis --

    def result(self) -> str:
        self._flush()
        # Blöcke mit Leerzeile trennen, Mehrfach-Leerzeilen kollabieren.
        md = "\n\n".join(self.blocks)
        md = re.sub(r"\n{3,}", "\n\n", md)
        # Aneinandergrenzende gleiche Emphasis-Marker aufheben (**...****...**).
        md = md.replace("****", "").replace("**``**", "")
        return md.strip()


def html_to_markdown(html: str, keep_images: bool = False) -> str:
    conv = MarkdownConverter(keep_images=keep_images)
    conv.feed(html)
    return conv.result()


def word_count(text: str) -> int:
    return len(text.split())


# --- Abschnitts-Aufbau ----------------------------------------------------

class Section:
    def __init__(self, title: str, part: str | None, markdown: str):
        self.title = title
        self.part = part
        self.markdown = markdown
        self.words = word_count(markdown)


def build_sections(epub: Epub, keep_images: bool, keep_front_back: bool) -> list[Section]:
    """Spine in Abschnitte zerlegen, Front/Back filtern, Parts als Gruppen führen."""
    sections: list[Section] = []
    current_part: str | None = None
    for zp in epub.spine:
        if epub.is_dropped(zp, keep_front_back):
            continue
        try:
            html = epub.read_text(zp)
        except KeyError:
            continue
        md = html_to_markdown(html, keep_images=keep_images)
        title = epub.label_of(zp) or _first_heading(md) or _stem(zp)
        if epub.is_part(zp):
            current_part = title
            if word_count(md) < 200:   # reine Titelseite: nur als Gruppe merken
                continue
        if word_count(md) == 0:
            continue
        sections.append(Section(title, current_part, md))
    return sections


def group_by_part(sections: list[Section]) -> list[Section]:
    """Kapitel je Part zu einem Abschnitt zusammenfassen (level=part)."""
    grouped: list[Section] = []
    bucket: list[Section] = []
    bucket_part: str | None = "\0"  # Sentinel
    for sec in sections:
        key = sec.part
        if key != bucket_part and bucket:
            grouped.append(_merge_bucket(bucket, bucket_part))
            bucket = []
        bucket_part = key
        bucket.append(sec)
    if bucket:
        grouped.append(_merge_bucket(bucket, bucket_part))
    return grouped


def _merge_bucket(bucket: list[Section], part: str | None) -> Section:
    if len(bucket) == 1 and not part:
        return bucket[0]
    title = part or bucket[0].title
    body = "\n\n".join(f"## {s.title}\n\n{s.markdown}" for s in bucket)
    return Section(title, None, body)


def _first_heading(md: str) -> str | None:
    m = re.search(r"^#{1,6}\s+(.+)$", md, re.MULTILINE)
    return m.group(1).strip() if m else None


def _stem(zip_path: str) -> str:
    return posixpath.splitext(posixpath.basename(zip_path))[0]


# --- Slug / Frontmatter / Ausgabe ----------------------------------------

def slugify(text: str, maxlen: int = 60) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:maxlen].strip("-") or "abschnitt"


def _yaml(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if v:
            v = str(v).replace('"', "'")
            lines.append(f'{k}: "{v}"')
    lines.append("---")
    return "\n".join(lines)


def write_single(epub: Epub, sections: list[Section], outdir: str) -> list[tuple[str, int]]:
    meta = epub.meta
    parts_out = [_yaml({
        "title": meta["title"], "author": meta["author"],
        "identifier": meta["identifier"], "source": "epub-to-notebooklm",
    }), "", f"# {meta['title']}", ""]
    last_part = None
    for sec in sections:
        if sec.part and sec.part != last_part:
            parts_out += [f"## {sec.part}", ""]
            last_part = sec.part
        level = "###" if sec.part else "##"
        parts_out += [f"{level} {sec.title}", "", sec.markdown, ""]
    fname = slugify(meta["title"]) + ".md"
    path = os.path.join(outdir, fname)
    text = "\n".join(parts_out).strip() + "\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return [(fname, word_count(text))]


def write_split(epub: Epub, sections: list[Section], outdir: str) -> list[tuple[str, int]]:
    meta = epub.meta
    written = []
    width = max(2, len(str(len(sections))))
    for i, sec in enumerate(sections, 1):
        num = str(i).zfill(width)
        fname = f"{num}_{slugify(sec.title)}.md"
        front = _yaml({
            "title": sec.title, "book": meta["title"], "author": meta["author"],
            "part": sec.part or "", "order": num, "source": "epub-to-notebooklm",
        })
        text = f"{front}\n\n# {sec.title}\n\n{sec.markdown}\n"
        with open(os.path.join(outdir, fname), "w", encoding="utf-8") as f:
            f.write(text)
        written.append((fname, sec.words))
    return written


# --- Analyse / Empfehlung -------------------------------------------------

def recommend_mode(total_words: int, n_sections: int) -> str:
    if total_words < SINGLE_SOURCE_THRESHOLD:
        return "single"
    return "split"


def print_analysis(epub: Epub, sections: list[Section]) -> int:
    total = sum(s.words for s in sections)
    parts = sorted({s.part for s in sections if s.part})
    print(f"  Titel        : {epub.meta['title']}")
    print(f"  Autor        : {epub.meta['author']}")
    print(f"  EPUB-Version : {epub.version or 'unbekannt'}")
    print(f"  Abschnitte   : {len(sections)} (Kapitel-Ebene)")
    if parts:
        print(f"  Teile        : {len(parts)} -> {', '.join(parts)}")
    print(f"  Wörter gesamt: {total:,}")
    print("  Abschnitte im Detail:")
    for i, s in enumerate(sections, 1):
        part = f"  [{s.part}]" if s.part else ""
        print(f"    {i:>2}. {s.title}{part} — {s.words:,} Wörter")
    rec = recommend_mode(total, len(sections))
    if rec == "single":
        print(f"\n  Empfehlung   : EINE Quelle (single). {total:,} < {WORDS_PER_SOURCE:,} "
              f"Wörter passen in eine NotebookLM-Quelle.")
        print("                 Splitten nur, wenn du gezielt nach Kapiteln fragen willst.")
    else:
        print(f"\n  Empfehlung   : SPLITTEN. {total:,} Wörter überschreiten das "
              f"Limit von {WORDS_PER_SOURCE:,} pro Quelle.")
    return total


def sanity_checks(written: list[tuple[str, int]]) -> None:
    print(f"\n  Geschrieben  : {len(written)} Datei(en)")
    for name, words in written:
        flag = "  ⚠ über Limit!" if words > WORDS_PER_SOURCE else ""
        print(f"    {name} — {words:,} Wörter{flag}")
    if len(written) >= FREE_SOURCE_LIMIT:
        print(f"  ⚠ {len(written)} Dateien erreichen/überschreiten das Free-Limit "
              f"von {FREE_SOURCE_LIMIT} Quellen. Erwäge level=part.")
    elif len(written) >= FREE_SOURCE_LIMIT - 5:
        print(f"  ⚠ Nahe am Free-Limit ({FREE_SOURCE_LIMIT} Quellen).")


# --- CLI ------------------------------------------------------------------

def process(path: str, args) -> None:
    print(f"\n=== {os.path.basename(path)} ===")
    epub = Epub(path)
    sections = build_sections(epub, args.keep_images, args.keep_front_back)
    if not sections:
        print("  Keine verwertbaren Abschnitte gefunden.")
        return
    total = print_analysis(epub, sections)

    if args.dry_run:
        print("\n  (dry-run: nichts geschrieben)")
        return

    mode = args.mode
    if mode == "auto":
        mode = recommend_mode(total, len(sections))

    outdir = args.outdir or os.path.join(
        os.path.dirname(os.path.abspath(path)),
        slugify(epub.meta["title"]) + "_notebooklm",
    )
    os.makedirs(outdir, exist_ok=True)
    print(f"\n  Ausgabe nach : {outdir}")
    print(f"  Modus        : {mode}")

    split_sections = sections
    if args.level == "part":
        split_sections = group_by_part(sections)

    written: list[tuple[str, int]] = []
    if mode in ("single", "both"):
        written += write_single(epub, sections, outdir)
    if mode in ("split", "both"):
        written += write_split(epub, split_sections, outdir)
    sanity_checks(written)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        description="EPUB für NotebookLM aufbereiten (Markdown, optional gesplittet).")
    p.add_argument("epubs", nargs="+", metavar="EPUB", help="ein oder mehrere .epub")
    p.add_argument("-o", "--outdir", help="Ausgabeverzeichnis (Default: neben dem EPUB)")
    p.add_argument("--mode", choices=["auto", "single", "split", "both"],
                   default="auto", help="Ausgabemodus (Default: auto nach Wortzahl)")
    p.add_argument("--level", choices=["chapter", "part"], default="chapter",
                   help="Split-Granularität (Default: chapter)")
    p.add_argument("--keep-images", action="store_true",
                   help="Bild-Alt-Texte als Platzhalter behalten")
    p.add_argument("--keep-front-back", action="store_true",
                   help="Front-/Back-Matter nicht wegfiltern")
    p.add_argument("--dry-run", action="store_true",
                   help="nur analysieren, nichts schreiben")
    args = p.parse_args(argv)

    for path in args.epubs:
        if not os.path.isfile(path):
            print(f"Datei nicht gefunden: {path}", file=sys.stderr)
            continue
        try:
            process(path, args)
        except (zipfile.BadZipFile, ValueError, ET.ParseError) as e:
            print(f"Fehler bei {path}: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
