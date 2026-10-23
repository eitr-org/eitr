# Fehlerbehebung

## Eine Menüaktion meldet ein fehlendes Werkzeug

Neue Installationen enthalten die Desktop-Abhängigkeiten; auf einem bestehenden Arch können einige fehlen. Lies die genaue Meldung und installiere das Paket über Installieren > Pakete > Pacman oder eine normale vollständige Systemaktualisierung. Entferne BlueZ/iwd/PipeWire/WirePlumber nicht wegen nativer Panels: Diese benötigen die Dienste weiterhin.

Dieses Handbuch braucht kein `less`. Es ist mitgeliefertes Markdown in einer nativen Überlagerung. Bei fehlendem oder veraltetem Katalog aktualisierst du die EITR-Desktop-Dateien.

## Root-eigenes Hilfsprogramm fehlt

Netzwerkwechsel, Sicherheit, Ladegrenzen und Wiederherstellung benötigen geprüfte Root-eigene Hilfsprogramme. Eine reine Dotfiles-Installation enthält deren Pakete möglicherweise noch nicht. Lies das zugehörige Kapitel. Umgehe die Prüfung niemals durch Ausführen einer vom Benutzer beschreibbaren heruntergeladenen Datei als Root. Das Öffnen der Auswahl darf deine Netzwerkverbindung nicht trennen.

## Konfigurations- oder Dienstprobleme

Quickshell zeigt verständliche Neuladefehler und behält möglichst die letzte funktionierende Konfiguration. Korrigiere die genannte Datei; starte den Anmeldemanager nicht wiederholt neu. **Starte SDDM niemals während deiner Desktop-Sitzung neu.**

Ein Elephant-Neustart lädt Menüdefinitionen neu. Sein Dienst muss `KillMode=process` behalten, damit gestartete Anwendungen weiterlaufen. Designs erzeugen Stile neu: Verschwindet eine Änderung, korrigiere Generator und erzeugte Ausgabe.

## Installation und Wiederherstellung prüfen

EITR ist weiterhin Beta. VM-Tests belegen nicht die Funktion jedes WiFi-Adapters, Bluetooth-Agenten, TPMs, GPUs, Fingerabdrucklesers oder Secure-Boot-Aufbaus. Aktueller WiFi-Dienst- und Unternehmensauthentifizierungscode wird mit Nachbildungen getestet. Prüfe echte Authentifizierung, bevor du dich darauf verlässt. Bestehende ISOs ändern sich nicht mit den Repository-Manifesten; baue Payload und ISO für neue Installationen neu.

Sichere vor der Installation auf einer separaten SSD deine anderen Laufwerke und prüfe das Ziel sorgfältig. Die Installation löscht das von dir bestätigte Laufwerk. Bewahre Passphrasen und Wiederherstellungsschlüssel offline auf. Snapshots derselben SSD sind keine unabhängige Sicherung. Beginne bei [Wiederherstellung und Snapshots](handbook:recovery).

## Ein Problem melden

**System > Informationen > Problem melden** sammelt EITR- und Paketversionen, Grafikhardware, Hyprland-Fehler, fehlgeschlagene Dienste, aktuelle Warnungen, Abstürze der letzten Woche, Fehler des vorherigen Starts, Installationsprotokoll und letzte Paketänderungen in `~/Documents/eitr-problem-report-<time>.txt`. Nur du kannst die Datei lesen. Benutzername, Rechnername, persönlicher Pfad, E-Mail-, IP- und MAC-Adressen werden entfernt; Protokolle können weiterhin Anwendungen oder Dateinamen nennen. Lies den Bericht vor dem Senden.

Nichts wird automatisch versendet. Das Terminal zeigt nur den Speicherort und bietet Versand oder vorheriges Lesen an:

1. **Per E-Mail** an `reports@eitr.info`: Dein E-Mail-Programm öffnet eine Zusammenfassung. Hänge die gespeicherte Datei an.
2. **GitHub-Issue öffnen** benötigt ein GitHub-Konto und öffnet ein neues Issue des Projekts. Issues sind öffentlich.
3. **Bericht zum Einfügen kopieren** kopiert den Bericht.
4. **Bericht lesen** öffnet deinen Texteditor.

Der Bericht dient nur zum Finden und Beheben dieses Problems und wird danach gelöscht. Eine E-Mail teilt deine Adresse mit. Antworte jederzeit darauf, um den Bericht löschen zu lassen.

### Wenn etwas abstürzt

Absturzbenachrichtigungen sind standardmäßig eingeschaltet. Ein Benutzerdienst beobachtet neue, lesbare systemd-coredump-Einträge deiner eigenen Programme. Jeder Absturz bietet Problem melden, Ignorieren und Dieses Programm stummschalten; Die KI fragen erscheint, wenn ein Standardassistent installiert und ausgewählt ist. Wiederholte Abstürze desselben Programms erzeugen höchstens alle fünf Minuten eine Benachrichtigung. Schalte sie unter Hauptmenü > Umschalten oder Kontrollzentrum > Schnellschalter um. Einstellungen und stummgeschaltete Programmpfade stehen in `~/.config/eitr/crash-help.json`; entferne einen Pfad aus `ignored`, um wieder Hinweise zu erhalten.

Die KI fragen öffnet deinen Standardassistenten nur mit Programm, Signal und Stacktrace aus `coredumpctl info`. Er soll die Ursache erklären und eine Lösung vorschlagen, ohne das System ohne deine Zustimmung zu ändern. Ein Speicherabbild wird nicht übergeben. Wenn du diese Aktion wählst, kann der Assistent die Zusammenfassung an seinen Anbieter senden. Problem melden fügt dieselbe Zusammenfassung dem vorhandenen Meldeablauf hinzu: Prüfe sie vor dem Teilen; nichts wird automatisch gesendet.

## Anpassungen und Aktualisierungen

EITR-Code liegt unter `/usr/share/eitr` und wird mit `eitr-desktop` aktualisiert. Deine Einstellungen bleiben unter `~/.config`. Dauerhafte Änderungen gehören dorthin, wo Aktualisierungen sie nicht berühren:

- Monitore, Geräte, zusätzliche Belegungen und Regeln: `~/.config/hypr/local.lua`.
- Shell-Ergänzungen: `~/.config/eitr/shell.local.zsh`.
- Terminaloptionen: `~/.config/kitty/local.conf`.
- Starterfarben: `~/.config/walker/style.override.css`.
- Vollständiger Ersatz einer mitgelieferten Datei: gleicher relativer Pfad unter `~/.config/eitr/overrides`. Diese Datei erhält keine Fehlerkorrekturen aus Aktualisierungen mehr.

Designdateien wie `kitty/theme.conf` und der Walker-Stil werden bei Designwechseln und einmal nach jeder Paketaktualisierung neu erzeugt. Vorherige Kopien liegen unter `~/.local/state/eitr/generated-backups`. Ändert sich das Speicherformat einer Einstellung, wird sie einmal bei der Anmeldung umgewandelt. Ein Fehler wird gemeldet und bei der nächsten Anmeldung erneut versucht (`~/.local/state/eitr/migrations.log`). `eitr-config status` zeigt wirksame Einstellungen und Überschreibungen.

Fehlgeschlagene Aufgaben bieten bei gewähltem Standardassistenten **A: KI fragen**; **Esc** schließt. Nur die letzten 200 Ausgabezeilen bleiben im Speicher; ANSI-Sequenzen werden entfernt und erkennbare Geheimniszeilen vor dem Teilen verborgen: Ein Cloud-Assistent sendet diese Ausgabe an seinen Anbieter, Ratatoskr behält sie auf diesem PC.
