# Entwicklungswerkzeuge

Hauptmenü > Entwicklung enthält **KI**, **Cloud**, **Git-Konten**, **Monitoring**, **LazyVim** und **VS Code**. Die Projektauswahl öffnet den gewählten Ordner im Editor; die Themenintegration aktualisiert unterstützte geöffnete Editoren, auch LazyVim-Sitzungen.

**Git-Konten** richtet eine GitHub/GitLab-Standardidentität, Ordnerregeln, SSH-Schlüssel und getrennte Anbieter-CLI-Anmeldungen ein. Jede Regeländerung erfordert eine bestätigte Vorschau; Projekt-Remotes und globale CLI-Konten werden niemals umgeschrieben. Siehe [Git-Konten](handbook:git-accounts).

## Optionale Werkzeuge

Installieren > Entwicklungssprachen und JavaScript-Werkzeuge installiert deine Auswahl. Java, Flutter und Datenbankclients sind für EITRs Leiste, Starter oder Themen nicht erforderlich. Installieren > Datenbanken bietet optionale Datenbankwerkzeuge. Installieren > Entwicklungsanwendungen bietet Bruno, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code und Zed; Installieren > Produktivität bietet 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack und Thunderbird. AUR-Pakete werden auf deinem Rechner heruntergeladen und gebaut; manche Lizenzen erlauben EITR keine Weitergabe.

## Web-Apps

Installieren > Web-Apps > Web-App erstellen fragt nach Name und Adresse und legt einen Starter an, der die Website im eigenen Fenster öffnet. Das Symbol wird bei der Erstellung ausschließlich über HTTP(S) heruntergeladen. Fehlerhafte Manifeste oder nicht verfügbare Symbole führen zum Seitensymbol oder einem allgemeinen Browsersymbol. Gib keine Zugangsdaten in der Adresse an. Starter und Symbole nutzen dein XDG-Datenverzeichnis, auch ein eigenes `XDG_DATA_HOME`; das Entfernen über beide Menüs verwendet denselben Ort.

Web-Apps brauchen Chrome oder Chromium (Installieren > Browser); DRM-Streamingdienste wie Netflix brauchen Chrome. Entferne eine App mit Delete unter Installieren > Web-Apps oder im Apps-Menü.

## KI-Assistenten

Entwicklung > KI bietet Standardassistent und ein Menü für jeden installierten Assistenten: Claude Code, Codex, Gemini CLI, Grok Build und GitHub Copilot CLI. Installiere sie unter Installieren > KI-CLIs; ohne installierte Assistenten verweist Entwicklung > KI dorthin.

Beim Sitzungsstart oder Öffnen eines LazyVim- oder VS Code-Projekts wähle zuerst einen Ordner unter `~/Development`: Ordner öffnen vertieft die Auswahl, Öffnen verwendet den aktuellen Ordner und Zurück führt eine Ebene höher beziehungsweise oben zurück zum Menü.

Du kannst Claude Code, Codex, Gemini CLI, Grok Build und GitHub Copilot CLI (`copilot`) auch per Befehl starten. Fehlt ein Werkzeug, erklärt Eitr seine Funktion und bietet dieselbe Installation wie Installieren > KI-CLIs an. Gib `yes` zum Installieren ein; die Eingabetaste bricht ab. Ohne interaktives Terminal endet der Befehl mit Installationshinweisen. Installierte Programme haben Vorrang vor diesen Startern. Melde dich über das jeweilige Werkzeug an; Eitr enthält weder Assistenten-Binärdateien noch Zugangsdaten.

Entwicklung > KI > Standardassistent wählt einen installierten Assistenten für diesen Computer. **SUPER + Alt + A** öffnet ihn im Terminal; ohne Auswahl öffnet sich die Auswahlliste. Eitr verwendet die üblichen Berechtigungsabfragen des jeweiligen Assistenten.

Beim Themewechsel aktualisiert Eitr nur die Hell-/Dunkel-Einstellung in vorhandenen, lesbaren Einstellungen von Claude Code, Gemini CLI und Grok Build. Alle anderen Einstellungen und die Formatierung bleiben erhalten. Nicht installierte Programme sowie fehlende oder beschädigte Dateien werden übersprungen; Assistenten ohne unterstützte Hell-/Dunkel-Einstellung verwenden die Terminalfarben.

Installierte SDK-Versionen und Installationsquellen stehen in den Distributionsmanifesten. Maßgeblich ist die aktuelle Auswahl; ein Handbuchbeispiel verspricht nicht die neueste Upstream-Version. Die Installation kann Downloads benötigen.

## Monitoring

Entwicklung > Monitoring macht deine Dashboards per Suche erreichbar. **Dashboard hinzufügen** fragt nach Dienst (Grafana, Datadog, Sentry, New Relic, Prometheus oder Andere), Name und Adresse. Danach öffnet das Menü das Dashboard im Browser. Die Einträge liegen nur auf diesem Rechner unter `~/.config/eitr/monitoring.json`; Delete entfernt einen. Gib niemals Passwörter oder Token in einer Adresse an.

**Monitoring-Werkzeuge** installiert Kommandozeilenprogramme: Prometheus’ `promtool` und die Sentry CLI. Arbeitsbereiche von Amazon Managed Grafana findest du unter Cloud > AWS > dein Konto > Grafana bei den anderen AWS-Werkzeugen.

## Konten und Cloud-Abläufe

KI-Nutzungsanzeigen erfordern einen installierten und eingerichteten Client; melde dich über dessen üblichen Ablauf an. Kontingente und Unternehmens-/API-Abrechnung können von den unterstützten Privatkonto-Panels abweichen. EITR enthält keine Zugangsdaten.

Cloud-Menüs verwenden deine lokalen Anbieterkonten und Profile. AWS-Profile stammen aus der lokalen AWS-Konfiguration oder EITRs eingerichteter Cloud-Profilzuordnung. Google Cloud listet benannte gcloud-Konfigurationen mit Konto und Projekt. Fehlt das Projekt, wird es beim Öffnen von Ressourcenwerkzeugen abgefragt; Anmelden bleibt bereits vor der Projektsuche verfügbar. Azure zeigt aktivierte Abonnements mit Mandanten-IDs. Wähle vor einem Werkzeug einen Kontext: Google-Cloud- und Azure-Werkzeuge werden innerhalb ihres Kontextmenüs gesucht, nicht global.

Beim Öffnen eines Google-Kontexts werden unpassende geerbte Projektüberschreibungen entfernt; Konfigurationen ohne Projekt fragen für Ressourcenwerkzeuge nach einem. Die Rückkehr vom Terminal behält Kontext und ein gewähltes Projekt für projektlose Konfigurationen bei, ohne globale CLI-Vorgaben zu ändern. Anmelden, Authentifizierung prüfen und Aktualisieren liegen in jedem erkannten Kontext. Google-Anmelden verwendet das konfigurierte Konto; Azure-Anmelden den Mandanten und stellt danach das bisherige Standardabonnement wieder her. Azure-Aktualisieren erneuert den Abonnementcache und zeigt die Auswahl.

Jedes Anbietermenü beginnt mit **AWS-Konto hinzufügen**, **GCP-Konto hinzufügen** oder **Azure-Konto hinzufügen**. So kannst du beliebig viele Konten einrichten, etwa Entwicklung und Produktion eines Unternehmens. Nach der Namensabfrage läuft die eigene CLI-Einrichtung des Anbieters: AWS-Profil über AWS SSO (IAM Identity Center) oder Zugriffsschlüssel, getrennte gcloud-Konfiguration mit Anmeldung und Projekt oder Azure-Anmeldung mit selbst benannten Abonnements. Fehlendes `gcloud` oder `az` wird zuerst zur Installation angeboten. **Ctrl+R** benennt ein Konto um.

Die Namen stehen in `~/.config/eitr/cloud-contexts.json`, zugeordnet zu AWS-Profil, gcloud-Konfiguration oder Abonnement-ID. EITR leitet keine Umgebungen ab und speichert dort keine Zugangsdaten; Hinzufügen wechselt keine globale CLI-Vorgabe. Grafana und Cloud-Operationen benötigen passende Konten und Berechtigungen. Manche Aktionen lesen nur, andere verändern entfernte Ressourcen: Prüfe Vorgang und Konto vor der Bestätigung.

Halte Token, `.env`-Geheimnisse und Zugangsdaten aus geteilten Dotfiles und Screenshots heraus. Die Shell-Konfiguration lädt unterstützte Manager, ohne dass Installationsprogramme deine Profile umschreiben. Lernen enthält eigene Referenzen für LazyVim, tmux und cmux.
