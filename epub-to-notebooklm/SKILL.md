---
name: epub-to-notebooklm
description: "Bereitet ein DRM-freies EPUB für NotebookLM (oder RAG) auf, säubert es nach Markdown und teilt es bei Bedarf nach Kapiteln in mehrere Quellen. Nutze diesen Skill, wenn jemand ein EPUB oder Buch in NotebookLM laden, ein EPUB splitten, ein Buch für RAG oder einen KI-Chat aufbereiten will, oder bei Signalen wie 'EPUB für NotebookLM', 'Buch in Quellen aufteilen', 'Kapitel als einzelne Quellen', 'EPUB säubern'. Nur für DRM-freie EPUBs."
license: CC-BY-4.0
metadata:
  author: Martin Kurz
  version: 0.1.0
  source: https://github.com/mgkurz/small-claude-skills
---

# EPUB für NotebookLM aufbereiten

Macht ein EPUB für NotebookLM nutzbar: säubert nach Markdown, filtert Rauschen (Cover, Copyright, Inhaltsverzeichnis, Index, Notes) und teilt bei Bedarf nach Kapiteln in mehrere Quellen.

Werkzeug: `scripts/epub_split.py`, reine Python-Standardbibliothek, keine Installation nötig.

## Vorab klären

- **DRM-frei?** Hartes DRM kann das Skript nicht lesen, NotebookLM auch nicht. Bei Fehler beim Entpacken: vermutlich DRM.
- **Splitten überhaupt nötig?** Eine NotebookLM-Quelle fasst 500.000 Wörter (über 1000 Seiten). Die meisten Bücher passen komplett in eine Quelle. Splitten lohnt nur, wenn:
  1. das Buch das Wortlimit sprengt, oder
  2. gezielt nach einzelnen Kapiteln gefragt werden soll (Scoping über aktive Quellen).

## Ablauf

1. **Analysieren (immer zuerst, schreibt nichts):**

       python3 scripts/epub_split.py --dry-run <buch.epub>

   Zeigt Titel, Autor, EPUB-Version, erkannte Abschnitte mit Wortzahl, Teile und eine Empfehlung (eine Quelle vs. splitten).

2. **Empfehlung dem Nutzer vorlegen.** Wortzahl gesamt nennen, die Empfehlung des Skripts wiedergeben, dann entscheiden lassen: eine gesäuberte Datei (`single`), nach Kapiteln gesplittet (`split`), oder beides (`both`).

3. **Erzeugen:**

       python3 scripts/epub_split.py --mode <single|split|both> -o <ausgabe-ordner> <buch.epub>

4. **Sanity-Checks berichten:** Zahl der Dateien, Wortzahl pro Datei, Warnungen (über Quellenlimit, nahe am Free-Limit von 50 Quellen).

## Optionen

- `--mode {auto,single,split,both}` — Ausgabemodus. `auto` (Default) wählt nach Wortzahl: unter 500k eine Quelle, sonst splitten.
- `--level {chapter,part}` — Split-Granularität. `chapter` (Default) je Kapitel eine Datei. `part` fasst Kapitel je Teil zusammen, sinnvoll wenn sonst mehr als ~30 bis 40 Dateien entstünden (Quellenlimit).
- `-o, --outdir DIR` — Ausgabeverzeichnis. Default: Ordner neben dem EPUB.
- `--keep-front-back` — Front- und Back-Matter nicht filtern (Default: Cover, Copyright, Inhaltsverzeichnis, Index, Notes, Danksagung werden entfernt).
- `--keep-images` — Bild-Alt-Texte als Platzhalter behalten (Default: Bilder raus).
- `--dry-run` — nur analysieren, nichts schreiben.

Mehrere EPUBs in einem Aufruf sind erlaubt.

## So arbeitet das Skript

- **Abschnittsgrenzen aus der Verlags-TOC**, nicht aus Fließtext-Überschriften: EPUB3 `nav.xhtml` bevorzugt, EPUB2 `toc.ncx` als Fallback. Lesereihenfolge aus dem OPF-Spine.
- **Rauschfilter** über `nav`-Landmarks, `epub:type` und Dateinamen.
- **Fußnoten-Verweise** (noteref) werden entfernt, da die Endnoten-Datei ohnehin gefiltert wird.
- **Pro Datei** ein YAML-Frontmatter (Titel, Autor, Buch, Teil) als Zitier-Anker für NotebookLM.

## Ausgabe

- `single`: eine `<buchtitel>.md`, Kapitel als Überschriften, Teile als Zwischenebene.
- `split`: pro Abschnitt `NN_slug.md` (z. B. `04_3-how-a-second-brain-works.md`), Abschnittstitel als `#` oben.

## Grenzen

- Nur DRM-freie EPUBs.
- Bei sehr langen Dokumenten verarbeitet NotebookLM teils nur den vorderen Teil. Im Zweifel gegenprüfen oder splitten.
- Sehr unsaubere EPUBs (kaputtes Markup) können Restrauschen hinterlassen. Stichprobe einer Ausgabedatei lesen.
