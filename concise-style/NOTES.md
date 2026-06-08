# Notes

## Befund vom 2026-06-07: Skill kürzte Inhalt, nicht nur Floskeln

Getestet an einem Vergleich Claude Code gegen Codex (Vorteile plus Kostenvergleich). Zwei Fassungen derselben Antwort, ohne und mit Skill.

Messung: 376 Wörter ohne Skill, 252 mit Skill, rund 33 Prozent kürzer. Ohne die identische Kostentabelle 303 gegen 179 Wörter, rund 41 Prozent.

Problem: Nicht der ganze Schnitt war Leerlauf. Mit gekürzt wurden auch echte Sachaussagen:
- Modellverhalten, worin Opus und Sonnet stark sind (substanziell, der ganze Punkt fehlte).
- CLAUDE.md als Projektgedächtnis, Nutzen für wiederkehrende Workflows (mittel).
- Codex teilt das Budget mit weiteren Agenten wie ChatGPT for Excel (mittel).

Ehrlich waren also eher 25 bis 30 Prozent echtes Kürzen, der Rest war Verlust.

## Ursache

Der Skill verbot Inhaltsverlust bereits ("Knapp heißt, Leerlauf zu streichen, nicht Inhalt"). Die Regel war nur zu abstrakt:
- Kein Prüfschritt, der Vollständigkeit erzwingt.
- Das einzige Beispiel zeigte nur Floskel-Streichen, nicht die Grenze zum Weglassen.

Unter dem Zug von "kürzer" gewann Kürze gegen Vollständigkeit.

## Fix in 0.2.0

- Abschnitt "Erst Inhalt sichern, dann kürzen": Sachaussagen auflisten, nur Formulierung straffen, am Ende Vollständigkeit prüfen.
- Zweites Beispiel mit Gegenbeispiel: falsch gekürzt (Aussage weg) gegen richtig gekürzt (Aussage bleibt).

## Befund vom 2026-06-08: Test 2, Prüfschritt hielt

Zweiter Test der 0.2.0-Fassung, diesmal an inhaltsdichtem technischem Stoff (TLS-Handshake, 12 Sachaussagen mit Zahlen und Caveats), gezielt die Gefahrenzone. Rohbeleg in workbench/tls-handshake_concise-style-test.md.

Methodik: erst die 12 Sachaussagen als Sollwert auflisten, dann aufgeblähte Fassung, dann Skill-Fassung, dann Audit jeder Aussage gegen die Skill-Fassung.

Messung: 360 gegen 165 Wörter, rund 54 Prozent kürzer. Inhaltsverlust: keiner, 12 von 12 erhalten.

Anders als in Test 1 (0.1.0) ging kein Inhalt verloren. Ursache laut Test: Das Auflisten des Sollwerts vor dem Kürzen erzwingt die Vollständigkeit, das bloße Verbot "kürze keinen Inhalt" tat das in Test 1 nicht. Der Prüfschritt aus 0.2.0 wirkt also als angewandte Anweisung.

Einschränkung: Selbsttest mit Vorwarnung. Der Sollwert war vor dem Kürzen bekannt, die Gefahr also präsent. Das zeigt, dass der Schritt greift, wenn man ihn befolgt, nicht, dass er auch ohne vorab notierte Aussagen greift.

## Offen

Härterer Test: Skill-Fassung erzeugen, ohne den Sollwert vorher zu sehen, Audit erst danach. Erst das zeigt, ob der Prüfschritt auch unwissentlich greift oder ob er als ausdrücklicher Pflichtschritt ("immer erst auflisten") zwingender formuliert werden muss. Bis dahin gilt: Anweisung wirkt bei Befolgung, Verhalten unter Nichtbefolgung unbelegt.
