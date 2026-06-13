# Changelog

Format nach Keep a Changelog, Versionierung nach SemVer.

## [0.1.0] - 2026-06-13
### Hinzugefügt
- Erste Version. `scripts/epub_split.py` (reine Python-Standardbibliothek): liest ein
  DRM-freies EPUB, parst die Verlags-TOC (EPUB3 `nav.xhtml`, EPUB2 `toc.ncx` als
  Fallback), filtert Front-/Back-Matter, wandelt nach schlankem Markdown und gibt es als
  eine Quelle oder nach Kapiteln gesplittet aus.
- Modi `auto`, `single`, `split`, `both`; Granularität `chapter` und `part`; Optionen
  `--keep-front-back`, `--keep-images`, `--dry-run`.
- Sanity-Checks: Wortzahl pro Datei, Gesamtzahl, Warnungen am NotebookLM-Quellenlimit.
- SKILL.md, README.md, NOTES.md.

### Grund
- Übergabe aus einem Claude-Chat (EPUB-Splitter für NotebookLM). Gegen ein echtes
  Test-EPUB gebaut und iteriert, nicht auf Verdacht. Zwei kritische Konverter-Fehler im
  Test gefunden und behoben (Details in NOTES.md). Tech-Stack bewusst auf Stdlib
  umgestellt statt ebooklib/BeautifulSoup, weil nichts installiert war und ein EPUB mit
  der Standardbibliothek vollständig zu lesen ist.
