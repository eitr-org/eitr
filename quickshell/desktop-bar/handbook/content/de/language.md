# Sprache

Eitr verwendet die Nachrichtensprache des Systems. **Kontrollzentrum > System > Sprache** zeigt die für das aktuelle Gebietsschema verwendete Sprache und öffnet eine Sprachauswahl; **Walker > System > Sprache** listet dieselben Optionen auf, die aktuelle ist markiert. Wähle eine Sprache oder **Systemstandard** und melde dich danach ab und erneut an. Eitr meldet dich niemals automatisch ab.

Eitr prüft zuerst **LC_ALL**, dann **LC_MESSAGES** und zuletzt **LANG**. Leere Variablen werden ignoriert. `LC_MESSAGES` ändert die Nachrichten, ohne Datums-, Zahlen- oder Währungsformate zu verändern. `LC_ALL` überschreibt alle Gebietsschema-Kategorien und bleibt normalerweise ungesetzt. Bei `C`, `POSIX` und nicht unterstützten Sprachen verwendet Eitr Englisch. Fehlende Übersetzungen erscheinen auf Englisch; bei einem fehlenden Handbuchkapitel wird das gesamte englische Kapitel verwendet.

## Systemsprache ändern

Wenn du auch systemweite Einstellungen ändern musst, verwende die Gebietsschema-Einstellungen des Systems. Aktiviere unter Arch Linux das gewünschte Gebietsschema in `/etc/locale.gen` und erzeuge die installierten Gebietsschemata mit `sudo locale-gen`. Lege danach die Sprache in `/etc/locale.conf` fest, zum Beispiel:

```text
LANG=pt_BR.UTF-8
```

Die ersten unterstützten Sprachen sind `pt_BR.UTF-8` (brasilianisches Portugiesisch), `es_ES.UTF-8` (Spanisch), `de_DE.UTF-8` (Deutsch) und `fr_FR.UTF-8` (Französisch). Regionale Varianten können auf die Basissprache zurückgreifen. Prüfe mit `locale` im Terminal, welche Variablen die Einstellungen überschreiben, und liste mit `locale -a` die installierten Gebietsschemata auf. Melde dich ab und wieder an, damit die Sprache für den Desktop, die Menüs und neue Terminals gilt. Die Auswahl schreibt nur `~/.config/environment.d/90-eitr-language.conf`: Sie setzt `LC_MESSAGES` und leert `LC_ALL` für die nächste Sitzung. Datums- und Zahlenformate bleiben erhalten. **Systemstandard** entfernt diese Einstellung. `/etc/locale.conf` wird nicht geändert und es werden keine Gebietsschemata erzeugt. Bereits laufende Anwendungen behalten ihre Sprache.

## Eine Übersetzung beitragen

Der englische Text ist die Quelle. Die Kataloge liegen unter `i18n/catalogs/<locale>/`; bearbeite die übersetzten Werte und behalte die englischen Schlüssel bei. Python- und Shell-Nachrichten verwenden die gemeinsame gettext-Domäne `eitr`. Behalte Platzhalter wie `%1` und `{name}`, Glyphen, Paketnamen, Befehle und Dateipfade unverändert bei. Die bei destruktiven Aktionen einzugebenden Bestätigungswörter müssen genau den von der Prüfung akzeptierten Wörtern entsprechen.

Handbuchkapitel liegen unter `quickshell/desktop-bar/handbook/content/<locale>/<chapter-id>.md`. Behalte `handbook:`-Links, Codeblöcke und Befehle bei. Die Tastatur- und Maustabellen werden aus den maßgeblichen Quellen der Tastenkürzel erzeugt. Übersetze ihre Nachrichten im Handbuchkatalog, statt eine zweite Liste der Tastenbelegungen zu pflegen.

Führe `python3 tools/i18n-build.py --check` aus, erzeuge das Handbuch mit `python3 quickshell/desktop-bar/scripts/handbook-build.py` und führe anschließend dessen Option `--check` sowie `bash tools/check.sh` aus. Die Prüfungen listen fehlende Nachrichten und veränderte Platzhalter auf. Prüfe lange Übersetzungen vor dem Einreichen in einer außerhalb des Bildschirms gerenderten Vorschau.

Aktualisiere nach der vollständigen Übersetzung eines geänderten Kapitels dessen Eintrag in `source-hashes.json` mit dem SHA-256 der englischen Quelle. Die Prüfung meldet geänderte oder nicht erfasste Quellen; das bloße Neugenerieren der Kataloge bestätigt keine Quelländerung.

Die Zeile Systemstandard zeigt den aus `/etc/locale.conf` ermittelten nativen Namen: `LC_ALL`, dann `LC_MESSAGES` und `LANG`; leere Werte werden ignoriert. Sitzungseinstellungen werden nicht berücksichtigt. English erzwingt Englisch; Systemstandard folgt dem System. Kann die Systemkonfiguration nicht gelesen werden, bleibt die einfache Beschriftung erhalten.
