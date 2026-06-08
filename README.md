# small-claude-skills

Sammlung kleiner, allgemein nutzbarer Skills im SKILL.md-Format. Privates Projekt von Martin Kurz.

## Idee

Ein Ort für die kleinen, allgemeinen Skills, die ich entwickle oder anpasse, getrennt von den großen domänenspezifischen Skills. Entwicklung lokal mit Claude Code.

## Skills

- concise-style: Antwortstil knapp, Antwort zuerst, ohne Inhalt zu verlieren.

## Aufbau

Pro Skill ein Ordner:

    skill-name/
      SKILL.md       der Skill selbst
      README.md      kurze Übersicht
      NOTES.md       Befunde und Begründungen (optional)
      CHANGELOG.md   Versionsverlauf (optional)
      workbench/     Arbeitsdateien, nicht versioniert

Auf Projektebene zusätzlich ein workbench/ für übergreifende Arbeitsdateien.

## Konventionen

- SKILL.md beginnt mit Frontmatter (name, description).
- Eine Verantwortung pro Skill, klein und kombinierbar.
- Änderungen mit Grund im CHANGELOG, Befunde in NOTES.
- Arbeitsdateien bleiben in workbench/ und damit aus der Versionierung.

## Lizenz

CC BY 4.0, siehe LICENSE.md.
