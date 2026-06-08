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

## Offen

Beim nächsten Einsatz prüfen, ob der Prüfschritt in der Praxis hält oder ob er ausdrücklicher als Pflichtschritt formuliert werden muss.
