# Sicherung und Wiederherstellung

Übertrage Desktop-Einstellungen, ausgewählte persönliche Ordner und Listen installierter Apps in einer einzigen verschlüsselten `.eitrbackup`-Datei auf einen anderen PC oder eine frische Eitr-Installation.

Snapshots unter [Wiederherstellung und Snapshots](handbook:recovery) bleiben für Rollbacks nach Updates auf demselben Datenträger. Sicherung und Wiederherstellung erstellt ein portables, mit `zstd` komprimiertes und per `age`-Passwort geschütztes Archiv für externe Laufwerke oder Cloud-Speicher.

## Sicherung und Wiederherstellung öffnen

- **Einstellungen**: Drücke **SUPER + ,** und öffne **System > Sicherung und Wiederherstellung**.
- **Walker**: Drücke **SUPER + F** und wähle **Einstellungen > System > Sicherung und Wiederherstellung**.
- **Terminal**: Führe `eitr backup` (oder `eitr-backup wizard`) aus.

## Sicherung erstellen

1. Wähle die gewünschten Kategorien:
   - **Eitr-Einstellungen**: Desktop-Vorgaben, bewusste Überschreibungen unter `~/.config/eitr/overrides`, eigene Designs, Hintergrundbilder und Sperrbildschirme.
   - **App-Einstellungen**: Nicht zu Eitr gehörende Ordner in `~/.config` ohne Browser-Profile und Caches.
   - **Persönliche Ordner**: Oberste Ordner in `$HOME`, standardmäßig abgewählt, plus **Ordner hinzufügen…** für Unterordner in `$HOME`. Größen werden im Hintergrund berechnet.
   - **Installierte Apps**: Listen explizit installierter offizieller Arch-, AUR- und Flatpak-Apps sowie Eitr-Plugins und Store-Einträge.
   - **Maschineneinrichtung**: Standardmäßig aus; lokale Display- und `hypr/local.lua`-Vorgaben für diesen PC.
2. Prüfe einzelne App-Einstellungsordner und installierte Apps (durchsuchbar und nach Quelle gruppiert).
3. Wähle das Ziel. Externe Laufwerke erscheinen vor `~/Backups`. Ziele auf derselben Festplatte zeigen eine Warnung; fehlender Speicherplatz wird vor dem Schreiben abgelehnt.
4. Gib dein Passwort zweimal ein. Passwörter stehen niemals in Befehlszeilen, Umgebungsvariablen oder Dateien.
5. Prüfe die Zusammenfassung auf der **Prüfen**-Seite und drücke **Enter**, um das Archiv atomar zu schreiben, oder **Esc** zum Abbrechen ohne Änderungen.

### Was ausgeschlossen bleibt

- Browser-Profile, Browser-Caches sowie Sperr-, Socket- und temporäre Dateien.
- Ausgelieferter Systemcode, Standarddateien und neu erzeugte Design-Ausgaben (werden nach der Wiederherstellung neu erstellt).
- Anmeldedaten außerhalb der Einstellungen: SSH-/GPG-Schlüssel, Schlüsselbunde, Cloud-CLIs (`~/.aws`, `~/.azure`, `~/.config/gcloud`, `~/.config/gh`) sowie gespeicherte Git-/WLAN-Geheimnisse.

## Aus einer Sicherung wiederherstellen

1. Wähle ein Archiv (von angeschlossenen Laufwerken, `~/Backups`, dem letzten Ziel oder einem eigenen Pfad) und gib das Passwort ein.
2. Eitr liest zuerst `manifest.json` und lässt dich Kategorien, Ordner oder Apps vor Änderungen auf dem Datenträger abwählen.
3. Bestätige die **Prüfen**. Ersetzte Dateien werden vorher mit Protokoll nach `~/.local/state/eitr/restore-backups/<id>/` gesichert.
4. Pakete werden der Reihe nach neu installiert: verfügbare offizielle Pakete in einer `pacman`-Transaktion (fehlende werden übersprungen und aufgelistet), AUR-Pakete einzeln über `yay`, danach Flatpaks sowie Eitr-Plugins und Store-Elemente **nur nach regulärer Prüfungsbestätigung**.
5. Designs und erzeugte Konfigurationen werden ohne Verlust zugewiesener Bildschirm-Hintergründe neu gebaut; Hyprland lädt bei aktiver Sitzung neu.
6. Melde dich danach wieder in Browsern, Cloud-CLIs (`gh`, `gcloud`, `aws`, `az`) an und füge externe SSH-/GPG-Schlüssel wieder ein.

## Wiederherstellung rückgängig machen

```sh
eitr backup undo <id>
```

`<id>` findest du in **Einstellungen > System > Sicherung und Wiederherstellung** oder über `eitr-backup status`. Undo stellt ersetzte Dateien wieder her, entfernt neu angelegte Dateien und regeneriert Designs.

## CLI-Übersicht

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Passwörter werden interaktiv am `/dev/tty` oder über `--passphrase-fd N` eingelesen. Neuere, noch nicht unterstützte Archivversionen werden klar abgewiesen.
