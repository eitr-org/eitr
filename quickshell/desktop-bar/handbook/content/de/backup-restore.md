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
   - **Git-Konten** (optionales Geheimnis, standardmäßig aus): `eitr/git-accounts.json`, verwaltete Includes unter `eitr/git-accounts`, `~/.gitconfig`, die von jedem Konto benannten SSH-Schlüssel (privater Schlüssel und `.pub`, mit `0600`), `~/.ssh/config`, `~/.ssh/known_hosts` sowie geheime GPG-Schlüssel über `gpg --export-secret-keys --armor` (GPG fragt selbst nach der Schlüssel-Passphrase).
   - **Cloud-Konten** (optionales Geheimnis, standardmäßig aus): `~/.aws`, `~/.config/gcloud`, `~/.azure`, `~/.kube` und Eitrs Cloud-Bezeichnungen (`eitr/cloud-contexts.json`, `eitr/cloud-navigation.json`).
   - **WiFi-Netzwerke** (optionales Geheimnis, standardmäßig aus): gespeicherte iwd- (`/var/lib/iwd/*.psk`, `*.8021x`, `*.open`) und NetworkManager-Profile (`/etc/NetworkManager/system-connections/*.nmconnection`), exportiert über `/usr/lib/eitr/eitr-network` mit `pkexec`.
2. Prüfe einzelne App-Einstellungsordner und installierte Apps (durchsuchbar und nach Quelle gruppiert).
3. Wähle das Ziel. Externe Laufwerke erscheinen vor `~/Backups`. Ziele auf derselben Festplatte zeigen eine Warnung; fehlender Speicherplatz wird vor dem Schreiben abgelehnt.
4. Gib dein Passwort zweimal ein. Passwörter stehen niemals in Befehlszeilen, Umgebungsvariablen oder Dateien.
5. Prüfe die Zusammenfassung auf der **Prüfen**-Seite (die warnt, sobald geheime Kategorien und Einträge enthalten sind) und drücke **Enter**, um das Archiv atomar zu schreiben, oder **Esc** zum Abbrechen ohne Änderungen.

### Was ausgeschlossen bleibt

- Browser-Profile, Browser-Caches sowie Sperr-, Socket- und temporäre Dateien.
- Ausgelieferter Systemcode, Standarddateien und neu erzeugte Design-Ausgaben (werden nach der Wiederherstellung neu erstellt).
- Anmelde-Schlüsselbunde, Git-CLI-Tokens (`~/.config/gh`, `eitr/git-accounts/cli`) sowie kurzlebige Cloud-Sitzungscaches: AWS-SSO- und CLI-Caches (`~/.aws/sso/cache`, `~/.aws/cli/cache`), gcloud-Token- und Anmeldedatenbanken (`~/.config/gcloud/access_tokens.db*`, `~/.config/gcloud/credentials.db*`, `legacy_credentials`, `logs`), Azure-Tokencaches (`~/.azure/msal_token_cache*`, `accessTokens.json`, `msal_http_cache*`, `logs`, `telemetry`, `commands`) und Kubernetes-Discovery-Caches (`~/.kube/cache`, `~/.kube/http-cache`).

## Aus einer Sicherung wiederherstellen

1. Wähle ein Archiv (von angeschlossenen Laufwerken, `~/Backups`, dem letzten Ziel oder einem eigenen Pfad) und gib das Passwort ein.
2. Eitr liest zuerst `manifest.json` und lässt dich Kategorien, Ordner oder Apps vor Änderungen auf dem Datenträger abwählen.
3. Bestätige die **Prüfen**. Ersetzte Dateien werden vorher mit Protokoll nach `~/.local/state/eitr/restore-backups/<id>/` gesichert.
4. Pakete werden der Reihe nach neu installiert: verfügbare offizielle Pakete in einer `pacman`-Transaktion (fehlende werden übersprungen und aufgelistet), AUR-Pakete einzeln über `yay`, danach Flatpaks sowie Eitr-Plugins und Store-Elemente **nur nach regulärer Prüfungsbestätigung**.
5. Nicht geheime Dateien werden zuerst und geheime Kategorien zuletzt wiederhergestellt: SSH- und GPG-Ordner behalten `0700`-Rechte, SSH-Schlüssel (privat und `.pub`), GPG-Dateien und Cloud-Konfigurationen behalten `0600`, GPG-Schlüssel werden über `gpg --import` importiert und WiFi-Profile als `root:root` `0600` über `/usr/lib/eitr/eitr-network` mit `pkexec` geschrieben.
6. Designs und erzeugte Konfigurationen werden ohne Verlust zugewiesener Bildschirm-Hintergründe neu gebaut; Hyprland lädt bei aktiver Sitzung neu. Melde dich danach wieder in Browsern und kurzlebigen Cloud-/Git-CLIs (`gh`, `gcloud`, `aws`, `az`) an.

## Wiederherstellung rückgängig machen

```sh
eitr backup undo <id>
```

`<id>` findest du in **Einstellungen > System > Sicherung und Wiederherstellung** oder über `eitr-backup status`. Undo stellt ersetzte Dateien (einschließlich geheimer Dateien, GPG-Schlüsselbund und WiFi-Profile) wieder her, entfernt neu angelegte Dateien und regeneriert Designs.

## CLI-Übersicht

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Passwörter werden interaktiv am `/dev/tty` oder über `--passphrase-fd N` eingelesen. Neuere, noch nicht unterstützte Archivversionen werden klar abgewiesen.
