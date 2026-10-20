# Git-Konten

Öffne **Entwicklung > Git-Konten**. Du kannst GitHub- und GitLab-Konten gleichzeitig nutzen, auch mehrere beim selben Anbieter oder Unternehmenshost. Neue Installationen enthalten GitHub CLI (`gh`) und GitLab CLI (`glab`). Bestehende ISO-Dateien müssen für Änderungen neu gebaut werden.

Jede Kontozeile zeigt, wo Git das Konto verwendet: **Standard**, die Ordnernamen oder **Noch nicht verwendet**. Enter öffnet die Aktionen, Shift+Backspace kehrt zur Liste zurück.

## Erste Einrichtung

1. **Konto hinzufügen** öffnet ein Formular mit Anbieter, Kontoname, Commit-Autor und E-Mail, Hostname und vorhandenem privatem SSH-Schlüssel (aus `~/.ssh`) oder zunächst ohne Schlüssel. Anschließend legst du Standardkonto und zugehörigen Ordner fest, prüfst die Vorschau und speicherst mit Enter.
2. **Vorhandene Einrichtung importieren** liest manuell eingerichtete Identitäten: Standardwerte `user.name`/`user.email` und ordnerbezogene Regeln `includeIf "gitdir:…"` in `~/.gitconfig` oder `~/.config/git/config`, einschließlich SSH-Alias und Schlüssel, über die eine eingebundene Datei Verbindungen leitet (`url.<alias>.insteadOf`). Nach Anzeige und Bestätigung werden passende Konten und Regeln erstellt. Deine Dateien bleiben unverändert; Ordnerregeln mit Platzhaltern werden als übersprungen angezeigt.

## Standard und Ordner

Das **Standardkonto** gilt in Ordnern ohne eigenes Konto. Ein **Ordnerkonto** gilt nur für Repositories darin. Der spezifischste Ordner gewinnt; repository-lokale Einstellungen sowie Git-Befehlszeilen- und Umgebungsvorgaben haben weiterhin Vorrang. EITR erhält globale Einstellungen und Kommentare und ergänzt am Ende von `~/.gitconfig` ein markiertes Include. Bestätigte Regeln überschreiben Identitäten aus externen Includes.

Walker bestätigt jede Kontoaktion vor dem Speichern und meldet sie als Benachrichtigung: **Als Standard festlegen** oder **Nicht mehr als Standard verwenden**, **Ordner hinzufügen** (wähle `~/Development`, einen Unterordner oder **Anderer Ordner…** für eine Pfadeingabe) und **Ordner entfernen**. Git richtet sich nach dem tatsächlichen `.git`-Verzeichnis. Verknüpfte Worktrees und Submodule können deshalb das Konto des übergeordneten Repositorys verwenden.

## SSH-Schlüssel

Die Commit-Identität gewährt keinen Repository-Zugriff. **Öffentlichen Schlüssel anzeigen** zeigt und kopiert den öffentlichen Schlüssel und nennt die Anbieterseite zum Hinterlegen (GitHub: Settings > SSH keys). **Vorhandenen SSH-Schlüssel wählen** wählt aus `~/.ssh`; **SSH-Schlüssel erstellen** erstellt einen Ed25519-Schlüssel mit Passphrase und zeigt den öffentlichen Schlüssel. **Verbindung testen** zeigt die Anbieterbegrüßung wie "Hi username!" als Benachrichtigung. Teile niemals einen privaten Schlüssel.

Schlüssel gelten nur für den SSH-Host des Anbieters. Der Starter löst vorhandene SSH-Aliasse ohne Verbindung auf und verwendet nur den gewählten Schlüssel; andere SSH-Einstellungen werden für diese Verbindung ignoriert. Proxy-Verbindungen werden abgelehnt. Behalte für fortgeschrittene Konfigurationen ein repository-lokales `core.sshCommand`. Die Prüfung bekannter Hosts bleibt aktiv. Ohne konfigurierten Schlüssel wird normales SSH verwendet, nicht der Schlüssel eines anderen Kontos. HTTPS-Zugangsdaten und ihre Helfer bleiben unverändert.

## Anbieter-CLIs

**Bei der CLI anmelden** meldet jedes Konto mit einem eigenen Konfigurationsverzeichnis an. Das normale globale Konto von `gh` oder `glab` wird nicht gewechselt. Geerbte Anbieter-Token-Variablen werden für diesen Prozess entfernt. Die Bestätigung erklärt, dass Token in vertraulichen, unverschlüsselten CLI-Profildateien liegen, damit Konten desselben Hosts keine Schlüsselbundeinträge teilen. Teile niemals `~/.config/eitr/git-accounts/cli`; dieser Ordner ist nicht in EITR-Sicherungen enthalten.

Verwende im Repository die CLI mit automatischer Kontowahl:

```sh
eitr-git cli auth status
eitr-git cli repo view
```

Das gewählte Standard- oder Ordnerkonto bestimmt `gh` oder `glab`. Normale CLI-Befehle behalten ihr globales Verhalten. SSH-Schlüsselregistrierung authentifiziert keine CLI-API-Aufrufe. Eine Bitbucket-CLI wird nicht mitgeliefert.

## Entfernen und Wiederherstellen

**Name und E-Mail bearbeiten** ändert die Identität; **Konto entfernen** entfernt Konto und Regeln nach Bestätigung. Ohne Ordnerregel greift eine allgemeinere Regel oder der Standard. Entfernen des Standards stellt vorhandene Git-Einstellungen außerhalb verbleibender Regeln wieder her. Projekte, Schlüssel und CLI-Zugangsdaten werden niemals gelöscht. Eine Regel zu entfernen widerruft keinen Anbieterzugriff.

Versionierte Einstellungen liegen in `~/.config/eitr/git-accounts.json`. Bei jeder Übernahme werden die globale Git-Datei, das aktive Include und die Einstellungen vertraulich gesichert unter `~/.local/state/eitr/git-account-backups/<id>`. `manifest.json` nennt Originalpfade, Sicherungsdateien und Berechtigungen. Schlüssel und CLI-Token werden nie kopiert. Prüfe zur manuellen Wiederherstellung das Manifest und erhalte alle seit der Sicherung vorgenommenen Änderungen. Veränderte oder fehlerhafte EITR-Include-Blöcke werden abgelehnt statt stillschweigend ersetzt.

Quellen: [bedingte Git-Includes](https://git-scm.com/docs/git-config), [GitHub-CLI-Profile](https://cli.github.com/manual/gh_help_environment), [GitLab-CLI-Profile](https://docs.gitlab.com/cli/configuration/).
