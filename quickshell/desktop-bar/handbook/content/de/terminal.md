# Terminal und Editoren

**SUPER + Enter** öffnet Kitty. **SUPER + Ctrl + Enter** öffnet die tmux-Hauptsitzung oder verbindet dich mit ihr. **SUPER + P** sucht Dateien mit unscharfer Suche, **SUPER + Ctrl + P** deren Inhalt. Lernen > Cmux-Befehle, Tmux-Befehle und LazyVim-Befehle sind durchsuchbare Referenzen. Die Auswahl kopiert einen Befehl, statt ihn auszuführen.

Kitty zeigt bei Sprüngen ab zwei Zellen eine kurze Cursorspur, etwa bei Enter, Home/End oder Wortwechseln. Sie beginnt nach 3 ms Ruhe und verblasst in 0,05–0,15 Sekunden. Passe `cursor_trail`, `cursor_trail_decay` oder `cursor_trail_start_threshold` in `~/.config/kitty/local.conf` an; `cursor_trail 0` schaltet sie aus. Eigene Optionen haben Vorrang vor Paketstandards und bleiben bei Designwechseln erhalten.

### Cursor-Feuer

**Stil > Terminal > Cursor-Feuer** bietet **Deaktiviert** (Standard) und **Aktiviert**. Aktiviert wird Kittys integrierter Effekt `cursor-trail-blaze` bei Cursorbewegungen, ohne Erkennung der Tippgeschwindigkeit. Deaktivieren stellt die normale kurze Spur und deine eigene Shader-Auswahl wieder her.

Erforderlich sind Kitty 0.49+ und `shader-slang` aus Eitrs Desktop-Abhängigkeiten. Aktivieren prüft den Shader vor Speichern oder Neuladen von Kitty. Die lokale Einstellung liegt in `~/.config/eitr/terminal.json`. Das Hilfsprogramm schreibt `kitty/cursor-fire.conf`, die der Benutzer-Lader zuletzt einbindet. Aktiviert wählt es den Feuershader und senkt die Bewegungsschwelle auf eine Zelle. Schriften, Designs und eigene Konfigurationsdateien bleiben unverändert.

## Der Befehl eitr

`eitr` bündelt Eitrs Werkzeuge. Ohne Argumente zeigt es die Liste. Es verwendet dieselben Skripte wie die Menüs und verhält sich deshalb genauso.

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Norse" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
eitr about
```

`eitr about` öffnet das Informationsfenster von Eitr oder fokussiert das bereits geöffnete Fenster.

`eitr config` und `eitr git` geben Argumente an `eitr-config` und `eitr-git` weiter. Jeder Befehl hat `--help`.

## Eigene Hooks

Ein Hook ist ein eigenes kleines Skript, das Eitr zu einem bestimmten Zeitpunkt ausführt. So ergänzt du Funktionen, ohne Eitr selbst zu ändern. Lege eine ausführbare Datei mit dem entsprechenden Namen in `~/.config/eitr/hooks/` ab:

| Datei | Ausführung | Argument |
| --- | --- | --- |
| `post-update` | nach Systemaktualisierung oder pacman/AUR-Aktualisierung | `system`, `pacman`, `yay` oder `full` |
| `theme-set` | nach einem Designwechsel | Ordnername des Designs |
| `battery-low` | einmal bei jedem Absinken des Akkus auf 15% | Prozentwert |
| `post-boot` | bei der ersten Anmeldung nach jedem Start | keines |

Für Spotify-Farben über Spicetify bei jedem Designwechsel erstellst du etwa `~/.config/eitr/hooks/theme-set`:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

Mache die Datei mit `chmod +x ~/.config/eitr/hooks/theme-set` ausführbar. Jeder Hook erhält bis zu 60 Sekunden. Ausgabe und Fehler landen in `~/.local/state/eitr/hooks.log`; ein fehlgeschlagener Hook stoppt nie Aktualisierung oder Designwechsel. `eitr hook list` zeigt vorhandene Hooks, `eitr hook run theme-set norse` probiert einen aus. Aktualisierungen verändern diesen Ordner nie.

## cmux TUI

Starte `cmux` in Kitty oder `cmux --session work` für eine benannte Sitzung. cmux TUI ist optional neben tmux und ersetzt weder Kitty noch dessen Tastenkürzel. Neue Installationen enthalten eine offizielle Binärdatei mit festgelegter Version unter `/usr/bin/cmux`. Ältere Benutzerinstallationen können im PATH Vorrang haben; prüfe mit `command -v cmux`. `less` wird zum Lesen von Terminalausgaben und Textdateien mitgeliefert.

Der Standardpräfix ist **Ctrl-b**: loslassen, dann die nächste Taste drücken.

| Tastenkürzel | Aktion |
| --- | --- |
| Ctrl-b ? | Aktuelle Kürzel zeigen |
| Ctrl-b W | Arbeitsfläche erstellen |
| Ctrl-b c | Bildschirm erstellen |
| Ctrl-b % / Ctrl-b " | Rechts / unten teilen |
| Ctrl-b t | Neuer Terminal-Tab |
| Ctrl-b h/j/k/l | Links/unten/oben/rechts fokussieren |
| Ctrl-b s | Seitenleiste zeigen/verbergen |
| Ctrl-b d | Lokal beenden oder vom Server trennen |

Für eine Sitzung ohne Oberfläche startest du `cmux --headless --session work` und verbindest dich mit `cmux attach --session work`. Browser-Tabs brauchen Chrome/Chromium. Das Schließen von Tabs, Bereichen oder Arbeitsflächen kann laufende Aufgaben beeinflussen; prüfe vorher. Lernen > Cmux-Befehle enthält Sitzungsbefehle, Navigation, Mausaktionen und Schließkürzel. Standards können sich ändern oder überschrieben werden; **Ctrl-b ?** zeigt die aktuelle Belegung.

## Aufgabenterminals

Terminals aus Menüs sowie Aktualisierungs- und Problembericht-Benachrichtigungen schweben mittig über deinen Fenstern mit deckendem Designhintergrund. KI-Sitzungen und LazyVim-Projekte aus Entwicklung öffnen sich als normale gekachelte Fenster mit durchsichtigem Hintergrund, ebenso wie selbst geöffnete Terminals. Gewöhnliche Terminals sind interaktiv und ohne Banner. Installation, Aktualisierung und Einrichtung zeigen das runenartige EITR-Banner. Erfolgreiche Aufgaben schließen normalerweise; Fehler bleiben bis zum Schließen sichtbar. Informationsberichte können absichtlich offen bleiben. Elephant neu zu starten soll gestartete Anwendungen nicht schließen: Anwendungen und Terminals aus Menüs, Tastenkürzeln und Leistenschaltflächen laufen in einer uwsm-Sitzung in eigenen Anwendungs-Scopes. Ohne uwsm werden sie direkt gestartet. Elephant behält das Beenden nur des Prozesses für Desktop-Helfer und Starts ohne uwsm bei.

Drücke **Esc**, um wartende Aufgaben-, Konto-, Berichts- und Über-Terminals zu schließen. Enter bleibt für Antworten und Bestätigungen vorgesehen, etwa zum Bestätigen der notierten Wiederherstellungsschlüssel und zum Ausschalten im Installationsprogramm.

## Shell-Verlauf

`history` zeigt letzte Befehle. Prüfe in zsh den tatsächlichen Verlaufspfad mit:

```sh
printf '%s\n' "$HISTFILE"
```

In Neovim öffnen:

```sh
nvim "$HISTFILE"
```

Der Verlauf kann Token oder Zugangsdaten enthalten; kopiere ihn nicht in Fehlerberichte. Schließe andere Shells vor manuellen Änderungen, da sie ihren Verlauf aus dem Speicher zurückschreiben können. Erweiterter zsh-Verlauf kann Zeitstempel und mehrzeilige Befehle enthalten. Entferne den ganzen Eintrag, kein beliebiges Fragment. Sichere ihn vertraulich, wenn du Änderungen zurücknehmen möchtest.

## Darstellung der Editoren

Designwechsel aktualisieren erzeugte Einstellungen für VS Code und LazyVim. Unterstützte laufende LazyVim-Sitzungen aktualisieren sich ohne erneutes Öffnen. Eigene Vorgaben und Plugins können andere Farben wählen. Prüfe ihre Konfiguration, wenn der Editor nicht dem Desktop folgt. Die Standardschrift wird nur in unterstützten Anwendungen übernommen.
