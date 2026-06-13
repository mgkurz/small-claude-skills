# epub-to-notebooklm

Bereitet DRM-freie EPUBs für NotebookLM (oder RAG) auf: säubert nach Markdown, filtert Rauschen, splittet bei Bedarf nach Kapiteln in mehrere Quellen.

## Wann er greift

Bei "EPUB für NotebookLM", "Buch in Quellen aufteilen", "EPUB splitten", "Buch für RAG aufbereiten", "Kapitel als einzelne Quellen". Oder per direktem Aufruf.

## Was er macht

- Abschnittsgrenzen aus der Verlags-TOC (EPUB3 `nav.xhtml`, EPUB2 `toc.ncx`), nicht aus Fließtext-Überschriften.
- Front-/Back-Matter (Cover, Copyright, Inhaltsverzeichnis, Index, Notes, Danksagung) wird gefiltert.
- HTML nach schlankem Markdown, Fußnoten-Verweise raus, Bilder raus (optional Alt-Text).
- Ausgabe als eine gesäuberte Datei oder nach Kapiteln gesplittet, je Datei mit YAML-Frontmatter als Zitier-Anker.
- Empfiehlt anhand der Wortzahl, ob Splitten überhaupt nötig ist (eine Quelle fasst 500.000 Wörter).

## Werkzeug

`scripts/epub_split.py`, reine Python-Standardbibliothek. Keine Installation, kein pip, kein pandoc.

    python3 scripts/epub_split.py --dry-run buch.epub          # analysieren
    python3 scripts/epub_split.py --mode both -o out buch.epub  # erzeugen

Optionen siehe SKILL.md.

## Nutzung

Den Ordner in das Skill-Verzeichnis legen, das deine Umgebung ausliest. Lokal mit Claude Code im Repo weiterentwickeln.

## Dateien

- SKILL.md, der Skill selbst
- scripts/epub_split.py, das Werkzeug
- NOTES.md, Befunde aus den Testläufen
- CHANGELOG.md, Versionsverlauf
- workbench/, Arbeitsdateien und Test-EPUBs, nicht versioniert

## Status

Version 0.1.0. Siehe CHANGELOG.md.
