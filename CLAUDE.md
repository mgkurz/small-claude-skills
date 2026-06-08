# CLAUDE.md

Leitfaden für Claude Code in diesem Repo.

## Was das hier ist

Sammlung kleiner, allgemein nutzbarer Skills im SKILL.md-Format. Bewusst klein und kombinierbar, getrennt von den großen domänenspezifischen Skills.

## Aufbau

Pro Skill ein Ordner auf oberster Ebene:

    skill-name/
      SKILL.md       Pflicht, der Skill selbst
      README.md      kurze Übersicht
      NOTES.md       Befunde und Begründungen (optional)
      CHANGELOG.md   Versionsverlauf (optional)
      workbench/     Arbeitsdateien, nicht versioniert

Dazu auf Projektebene ein workbench/ für übergreifende Arbeitsdateien.

## SKILL.md-Konventionen

- Beginnt mit Frontmatter: name und description.
- description schildert knapp, was der Skill tut und wann er greift, mit konkreten Auslösesignalen. Keine Werbefloskeln.
- Eine Verantwortung pro Skill. Im Zweifel lieber zwei kleine Skills als einen großen.
- Inhalt auf Deutsch, im Stil knapp und konkret.

## Arbeitsweise

- Analysen, Tests und Zwischenstände gehören in workbench/, nie in den versionierten Teil.
- Jede inhaltliche Änderung am Skill kommt mit Grund in die CHANGELOG.md.
- Befunde aus Tests in die NOTES.md, damit die Begründung am Artefakt klebt.
- Versionierung nach SemVer, Changelog nach Keep a Changelog.

## Was zu vermeiden ist

- Arbeitsdateien committen.
- SKILL.md mit Ballast aufblähen. Der Skill ist Anweisung, nicht Dokumentation.
- Skills ohne Frontmatter oder ohne klare Auslösesignale.

## Lizenz

CC BY 4.0, Martin Kurz. Siehe LICENSE.md. Bei abgeleiteten Skills die Herkunft nennen.
