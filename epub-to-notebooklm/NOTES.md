# NOTES

Befunde aus Entwicklung und Tests. Begründungen kleben hier am Artefakt.

## Testbuch

`Forte_Building-a-Second-Brain_9781800812239.epub` (Tiago Forte, Profile Books).
EPUB 3.0, hybrid: enthält sowohl `toc.ncx` (EPUB2) als auch `nav.xhtml` (EPUB3).
Saubere Verlagsstruktur: eine XHTML pro Kapitel, Teile als eigene Dateien, reiche
`epub:type`-Landmarks. Verschachtelte TOC (Part > Kapitel). Gut geeignet als Testfall,
deckt aber nicht alles ab (kein Single-File-EPUB, keine wirklich unsauberen EPUBs).

## Designentscheidungen

### Stdlib statt ebooklib/BeautifulSoup
Die ursprüngliche Übergabe schlug ebooklib + BeautifulSoup vor. Auf dem Rechner war
nichts davon installiert, kein pandoc. Ein EPUB ist nur ZIP + XML, das deckt die
Standardbibliothek vollständig ab (`zipfile`, `xml.etree`, `html.parser`). Entscheidung:
null Abhängigkeiten. Der Skill läuft damit sofort und überall, kein pip-Schritt als
Vorbedingung.

### Abschnittsgrenzen aus der TOC
Wahrheit ist die verlagsgepflegte TOC, nicht Fließtext-Überschriften. `nav.xhtml`
bevorzugt (EPUB3), `toc.ncx` als Fallback (EPUB2). Lesereihenfolge aus dem OPF-Spine.
Beide TOC-Parser strippen Namespaces, damit der Code gegen verschiedene EPUB-Dialekte
robust ist.

### Front-/Back-Matter filtern
Cover, Copyright, Inhaltsverzeichnis, Index, Notes, Danksagung sind für NotebookLM
Rauschen. Erkennung dreistufig: `nav`-Landmarks (`epub:type`) zuerst, dann Dateiname-
Präfixe, sonst behalten. Per `--keep-front-back` abschaltbar.

### Zwei Modi statt nur Splitten
Das Testbuch hat rund 66.000 Wörter und passt damit komplett in eine NotebookLM-Quelle
(Limit 500.000). Splitten ist hier nicht aus Größe nötig, nur fürs Kapitel-Scoping.
Darum: `single` (eine gesäuberte Datei) und `split` (nach Kapiteln), plus `auto` nach
Wortzahl. Das deckt beide Realfälle ab statt blind zu splitten.

## Gefundene und behobene Fehler

### Skip-Zähler lief bei selbstschließenden Tags voll (kritisch)
Erster Lauf meldete für mehrere Kapitel viel zu niedrige Wortzahlen (ch08: 914 statt
~6450, ch06: 2306 statt ~9300). Ursache: Beim Verwerfen von `<figure>` zählte
`skip_depth` bei jedem inneren `<img/>` hoch, aber nie wieder runter, weil `img` kein
DROP-Tag ist. Nach der ersten Figur blieb der Skip-Zähler hängen und schluckte den Rest
des Kapitels. Fix: ausgewogener Tiefenzähler, selbstschließende/Void-Tags (`img`, `br`,
pagebreak-`span`) zählen nicht für die Tiefe; eigener `handle_startendtag`. Danach
stimmen die Wortzahlen mit den Rohwerten überein.

Lehre: bei HTMLParser-Skip-Logik müssen Void- und selbstschließende Tags getrennt
behandelt werden, sonst läuft jeder Tiefenzähler in verschachtelten gedroppten Bäumen
aus dem Ruder.

### Fußnoten-Ziffern klebten am Satzende
Absätze endeten mit verwaisten Ziffern (".previously.1"), den `<a epub:type="noteref">`-
Markern. Da die Endnoten-Datei ohnehin gefiltert wird, zeigen die Marker ins Leere. Fix:
noteref-Anker samt Inhalt verwerfen.

### Kaputte Emphasis `****`
Aneinandergrenzende Fettpassagen (`<b>x</b><b>y</b>`) ergaben `**x****y**`. Fix: `****`
im Ergebnis entfernen. Triple-Marker (`***bold-italic***`) bleiben unberührt, weil sie
nie als Vierfachfolge entstehen.

## Offen / nicht getestet

- Single-File-EPUB ohne getrennte Kapiteldateien (Fallback nur über Überschriften). Der
  aktuelle Ansatz schneidet an Spine-Dateien; bei einem einzigen Spine-Dokument entstünde
  nur ein Abschnitt. Ein Heading-Fallback ist noch nicht gebaut.
- Wirklich unsaubere EPUBs (kaputtes Markup, wiederholte Kopfzeilen).
- EPUB2-only (reines `toc.ncx` ohne `nav.xhtml`). Der ncx-Pfad ist implementiert, aber am
  Testbuch nur indirekt geprüft.
