# Organisationsprofile

Verwenden Sie die offizielle ISO unverändert. Legen Sie `eitr-profile.json` neben oder statt `eitr-answers.json` auf einen FAT32-Stick mit der Bezeichnung `EITRANSWERS`. Nur mit Profil läuft der normale Assistent mit allen Profiländerungen in der Prüfung. Mit beiden Dateien erscheinen Datenträgeraktion und sämtliche Änderungen vor dem 15-Sekunden-Countdown. Strg+C bricht vor Datenträgeränderungen ab. Lassen Sie den Stick bis zum Ausschalten angeschlossen.

Vollständiges Beispiel: Ersetzen Sie die Beispielprüfsummen durch die tatsächlichen Kleinbuchstabenwerte von `sha256sum` und kopieren Sie alle genannten Dateien auf den Stick.

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Nur `version` und `name` sind Pflicht. Unbekannte und doppelte JSON-Schlüssel werden abgelehnt. Entfernen Sie unnötige optionale Abschnitte. Pfade sind relativ zum Stick; absolute Pfade, symbolische Links und `..` sind verboten. Alle Dateien müssen vor Datenträgeränderungen vorhanden sein und zur SHA-256 passen. Hintergrundbilder müssen gültige PNG-, JPEG- oder WebP-Dateien sein. Die Schlüsseldatei muss genau einen öffentlichen OpenPGP-Schlüssel enthalten, die Serveradresse HTTPS ohne Zugangsdaten verwenden. Der Schlüssel wird in pacman importiert und lokal signiert: Verwenden Sie nur vertrauenswürdige Schlüssel. Pakete und Skripte sind vertrauenswürdiger Administratorcode ohne Sandbox.

`remove` akzeptiert nur die geprüfte Liste `distro/removable-apps.json`; die Einzelprüfung steht in `distro/PROFILE-PACKAGE-REVIEW.md`. Geschützte oder unbekannte Pakete lehnen das gesamte Profil ab. pacman prüft Abhängigkeiten, ohne rekursives Entfernen oder Umgehen der Prüfung. Gruppenrichtlinien schließen alle freigegebenen Pakete aus `gaming`, `media`, `development`, `sharing` und `remote_access` aus. `false` deaktiviert, `true` erlaubt. `update_channel` akzeptiert nur `"stable"`. Ausgelassene Richtlinien schränken nicht ein.

`plugins` akzeptiert `false`, das Installieren > Plugins und Werkzeuge > Plugins ausblendet und Hinzufügen, Aktualisieren und Starten von Plugins ablehnt, oder `{"allow": ["https://git.example.org/team/tools.git", "git@github.com:team/plugin.git"]}`, das nur diese Repositorys erlaubt. Einträge der Erlaubnisliste sind HTTPS- oder SSH-URLs und passen unabhängig von Schema, Benutzer, Port, Endung `.git`, abschließendem Schrägstrich und Groß-/Kleinschreibung; ein SSH-Host-Alias aus `~/.ssh/config` muss so eingetragen werden, wie er geschrieben wird. Wird eine solche Richtlinie auf einem installierten Rechner angewendet, werden die Dienste nicht mehr erlaubter Plugins gestoppt und deaktiviert; ihre Dateien bleiben erhalten.

Rezepte verwenden `group/name` aus `distro/software.json`. Nur vorgefertigte pacman- und Flatpak-Rezepte sind erlaubt. AUR, interaktive Installer und Webapps werden abgelehnt; liefern Sie geprüfte vorgefertigte Paketdateien. Repositorypakete, Rezepte und Flathub benötigen Internet. Paketdateien funktionieren offline, wenn ihre Abhängigkeiten auf ISO oder Stick liegen. Paketnamen müssen in den aktuellen pacman-Datenbanken existieren; aktualisieren Sie vor Onlineprüfungen über den normalen Ablauf. Es gibt keine AUR-Builds. Online-pacman-Ergänzungen führen ein vollständiges Upgrade aus. Das zusätzliche Repository dient späteren Updates; liefern Sie nur dort verfügbare Pakete als Dateien.

Während der Installation werden Flathub-Apps und Flatpak-Rezepte für den Desktopbenutzer vorgemerkt und beim ersten Start mit Internetverbindung installiert. Fehlgeschlagene Installationen werden beim nächsten Start erneut versucht. Beim Anwenden eines Profils auf einem bereits installierten Rechner werden sie direkt installiert.

Browser: Firefox und Chromium; Chromium muss zusätzlich installiert werden. Thema und Hintergrund werden für die nächste Anmeldung des gewählten Benutzers gespeichert, ohne Desktopneustart. Kanal und Repository gelten systemweit. `setup` läuft abschließend als root im privaten kopierten Stickverzeichnis, nachdem das Profil gespeichert wurde. Ein SHA-256-Marker erfasst den Versuch vor dem Start: Fehler und Unterbrechungen führen nicht zu stiller Wiederholung. Ändern Sie Skript und Prüfsumme für einen weiteren Versuch. Fehler bleiben sichtbar; abgeschlossene Pakettransaktionen werden nicht zurückgerollt.

```sh
eitr profile check /run/media/alex/EITRANSWERS
eitr profile apply /run/media/alex/EITRANSWERS
```

`check` liest Dateien und Metadaten mit temporären Verzeichnissen, ohne Systemeinstellungen zu ändern. `apply` nutzt die explizite Rootaktion `eitr-system profile-apply`, kopiert und prüft erneut, zeigt die Zusammenfassung und verlangt `APPLY PROFILE`. Abbrechen ändert nichts. Es entfernt mit pacman, installiert Ergänzungen, speichert Vorgaben sowie `/etc/eitr/policies.json` (0644, root:root) und `/etc/eitr/profile.json`. Ein anderes Profil ersetzt gespeicherte Entscheidungen, installiert aber frühere Entfernungen nicht automatisch neu und setzt ausgelassene Einstellungen nicht zurück. Setup-Marker bleiben erhalten.

Ausschlüsse filtern Installationslisten; `IgnorePkg` verhindert die Wiedereinführung als Abhängigkeit bei System Update. Ein Konflikt muss das Upgrade stoppen. Benutzervorgaben installieren keine Anwendungen. Richtlinien verbergen Elephant-Menüs und Suche, Fernzugriffsleisteneinträge, Assistentenzusammenarbeit und Kanalwahl. Werkzeuge lehnen auch direkte Aufrufe ab. Menüs und Panels müssen eventuell aktualisiert werden.

**Dies sperrt Benutzer mit root nicht aus.** Root kann Richtlinien ändern oder andere Werkzeuge nutzen. Echte Beschränkung bedeutet auch, root nicht zu vergeben. Keine Flottenverwaltung. Installationen mit und ohne Netzwerk, ein abgelehntes Profil und das Anwenden auf ein installiertes System haben eine VM-Prüfung bestanden; die übrigen Prüfungen stehen in `distro/PROFILE-VM-TESTING.md`.
