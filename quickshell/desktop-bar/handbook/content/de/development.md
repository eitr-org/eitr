# Entwicklungswerkzeuge

Hauptmenü > Entwicklung enthält **KI**, **Cloud**, **Git-Konten**, **Monitoring**, **LazyVim** und **VS Code**. Die Projektauswahl öffnet den gewählten Ordner im Editor; die Themenintegration aktualisiert unterstützte geöffnete Editoren, auch LazyVim-Sitzungen.

**Git-Konten** richtet eine GitHub/GitLab-Standardidentität, Ordnerregeln, SSH-Schlüssel und getrennte Anbieter-CLI-Anmeldungen ein. Jede Regeländerung erfordert eine bestätigte Vorschau; Projekt-Remotes und globale CLI-Konten werden niemals umgeschrieben. Siehe [Git-Konten](handbook:git-accounts).

## Optionale Werkzeuge

Installieren > Entwicklungssprachen und JavaScript-Werkzeuge installiert deine Auswahl. Java, Flutter und Datenbankclients sind für EITRs Leiste, Starter oder Themen nicht erforderlich. Installieren > Datenbanken bietet optionale Datenbankwerkzeuge. Installieren > Entwicklungsanwendungen bietet Bruno, Cursor, GitHub Desktop, Insomnia, JetBrains Toolbox, Meld, Postman, VS Code und Zed; Installieren > Produktivität bietet 1Password, Bitwarden, Discord, LibreOffice, Obsidian, Slack und Thunderbird. AUR-Pakete werden auf deinem Rechner heruntergeladen und gebaut; manche Lizenzen erlauben EITR keine Weitergabe.


Sprachen bietet außerdem **mise (viele Laufzeitumgebungen)** als optionales Arch-Paket. Aktiviere es manuell mit `eval "$(mise activate zsh)"` in `~/.zshrc`; es kann für dieselbe Laufzeitumgebung mit nvm/uv kollidieren. Bestehende Sprachmanager bleiben unverändert.

## Web-Apps

Installieren > Web-Apps > Web-App erstellen fragt nach Name und Adresse und legt einen Starter an, der die Website im eigenen Fenster öffnet. Das Symbol wird bei der Erstellung ausschließlich über HTTP(S) heruntergeladen. Fehlerhafte Manifeste oder nicht verfügbare Symbole führen zum Seitensymbol oder einem allgemeinen Browsersymbol. Gib keine Zugangsdaten in der Adresse an. Starter und Symbole nutzen dein XDG-Datenverzeichnis, auch ein eigenes `XDG_DATA_HOME`; das Entfernen über beide Menüs verwendet denselben Ort.
Bei mehreren Browserprofilen fragt die Erstellung einer Web-App, in welchem Profil sie geöffnet wird; um dies zu ändern, entferne die App und füge sie erneut hinzu.

Web-Apps brauchen Chrome, Chromium, Edge, Brave oder Vivaldi (Installieren > Browser); DRM-Streamingdienste wie Netflix brauchen Chrome. Entferne eine App mit Delete unter Installieren > Web-Apps oder im Apps-Menü.

Installieren > Browser bietet auch Brave (AUR). Installieren > Produktivität bietet Basecamp und Notion als optionale Web-Apps. Die Rezepte enthalten nur Name und URL; das Website-Symbol wird erst bei der Installation auf Ihren Rechner geladen. Nichts ist vorinstalliert.

## KI-Assistenten

Jeder Cloud-Assistent hat unter Entwicklung > KI ein Untermenü Konten. Standard verwendet die vorhandene Konfiguration und Anmeldung, ohne Dateien zu verschieben. Konto hinzufügen… fragt nach einem Namen, zeigt eine Übersicht und öffnet die Anmeldung der CLI nach Möglichkeit in einem privaten Browserfenster (unbekannte Browser verwenden den normalen Aufruf). Enter bestätigt; Esc bricht ab. Wählen Sie ein Konto, um künftige interaktive Sitzungen, KI fragen und schreibgeschützte Helfer manuell umzustellen; laufende Sitzungen behalten ihr Konto. Delete entfernt ein hinzugefügtes Konto samt lokaler Konfiguration nach Bestätigung; Standard lässt sich nicht entfernen. Das Entfernen des gewählten Kontos kehrt zu Standard zurück, ohne ein anderes Konto abzumelden. Antigravity bietet nur Standard, da seine CLI keinen anderen Konfigurationsordner unterstützt. Ratatoskr hat ein lokales Konto. Namen und Auswahl bleiben auf diesem PC in `eitr/ai-accounts.json` (0600); separate Ordner liegen unter `$XDG_DATA_HOME/eitr/ai-accounts/` (0700). KI-Nutzung gruppiert Konten nach Assistent und zeigt Keine Daten, wenn die Nutzung nicht lesbar oder nicht unterstützt ist.

Entwicklung > KI bietet ein Menü für jeden installierten Assistenten: Claude Code, Codex, Gemini CLI, Grok Build und GitHub Copilot CLI. Installiere sie unter Installieren > KI-CLIs; ohne installierte Assistenten verweist Entwicklung > KI dorthin.

Beim Sitzungsstart oder Öffnen eines LazyVim- oder VS Code-Projekts wähle zuerst einen Ordner unter `~/Development`: Ordner öffnen vertieft die Auswahl, Öffnen verwendet den aktuellen Ordner und Zurück führt eine Ebene höher beziehungsweise oben zurück zum Menü.

Du kannst Claude Code, Codex, Gemini CLI, Grok Build und GitHub Copilot CLI (`copilot`) auch per Befehl starten. Fehlt ein Werkzeug, erklärt Eitr seine Funktion und bietet dieselbe Installation wie Installieren > KI-CLIs an. Enter bestätigt die Installation; Esc bricht ab. Ohne interaktives Terminal endet der Befehl mit Installationshinweisen. Installierte Programme haben Vorrang vor diesen Startern. Melde dich über das jeweilige Werkzeug an; Eitr enthält weder Assistenten-Binärdateien noch Zugangsdaten.

Entwicklung > Standardassistent wählt einen installierten Assistenten für diesen Computer. **SUPER + A** öffnet ihn im Terminal; ohne Auswahl öffnet sich die Auswahlliste. Interaktive Assistenten starten standardmäßig mit vollem Zugriff und können Dateien ändern und Befehle ohne Nachfrage ausführen. Unter **System > Sicherheit > Assistentenzugriff > Vor Änderungen fragen** aktivierst du die normalen Berechtigungsabfragen. Die Einstellung liegt nur auf diesem PC in `eitr/ai.json`. Organisationsrichtlinien erzwingen Rückfragen. Sudo benötigt weiterhin dein Passwort. Zusammenarbeit ohne Fenster und Sprach-Erinnerungen bleiben schreibgeschützt.

Beim Themewechsel aktualisiert Eitr nur die Hell-/Dunkel-Einstellung in vorhandenen, lesbaren Einstellungen von Claude Code, Gemini CLI und Grok Build. Alle anderen Einstellungen und die Formatierung bleiben erhalten. Nicht installierte Programme sowie fehlende oder beschädigte Dateien werden übersprungen; Assistenten ohne unterstützte Hell-/Dunkel-Einstellung verwenden die Terminalfarben.

Installierte SDK-Versionen und Installationsquellen stehen in den Distributionsmanifesten. Maßgeblich ist die aktuelle Auswahl; ein Handbuchbeispiel verspricht nicht die neueste Upstream-Version. Die Installation kann Downloads benötigen.

### Ratatoskr

Entwicklung > Standardassistent bietet immer **Ratatoskr (lokal, experimentell)** an; dafür brauchst du weder Konto noch Abonnement. Beim ersten Mal erklärt ein Terminal die einmaligen Downloads, bevor sich etwas ändert: das Arch-Paket `ollama` (etwa 15 MB) und das Sprachmodell `qwen3:4b` (etwa 2,5 GB, Apache-2.0-Lizenz). Eine Bestätigung (Enter bestätigt; Esc bricht ab) installiert das Paket, legt den Benutzerdienst `eitr-ollama.service` an, lädt das Modell mit sichtbarem Fortschritt herunter und macht es zum Standard. Schlägt ein Schritt fehl, bleibt seine Ausgabe sichtbar und der bisherige Standard erhalten.

Alles bleibt auf diesem PC: Der Dienst lauscht nur auf `127.0.0.1:11434`, startet bei Bedarf und speichert seine Modelle in `~/.local/share/eitr/ollama`. Er ist spürbar weniger zuverlässig als die Cloud-Assistenten, besonders bei ungewöhnlichen Formulierungen, und auf dem Prozessor langsamer. Sprach-Erinnerungen prüfen seine Antworten wie die jedes anderen Assistenten, eine falsche Antwort ändert also nichts. **SUPER + A** öffnet einen Chat mit dem Modell; `/bye` schließt ihn. Er ist nie Helfer für zusammenarbeitende Assistenten und hat keinen Eintrag in der KI-Nutzung.

Wähle **Ratatoskr** im selben Menü und drücke **Delete**. Das Entfernen fragt einmal nach, löscht dann Dienst und Modelle, setzt den Standard zurück, falls er lokal war, und deinstalliert `ollama`, falls die Einrichtung es installiert hat. Ollamas eigener Schlüssel und Chatverlauf in `~/.ollama` bleiben erhalten.

## Monitoring

Entwicklung > Monitoring macht deine Dashboards per Suche erreichbar. **Dashboard hinzufügen** fragt nach Dienst (Grafana, Datadog, Sentry, New Relic, Prometheus oder Andere), Name und Adresse. Danach öffnet das Menü das Dashboard im Browser. Die Einträge liegen nur auf diesem Rechner unter `~/.config/eitr/monitoring.json`; Delete entfernt einen. Gib niemals Passwörter oder Token in einer Adresse an.

**Monitoring-Werkzeuge** installiert Kommandozeilenprogramme: Prometheus’ `promtool` und die Sentry CLI. Arbeitsbereiche von Amazon Managed Grafana findest du unter Cloud > AWS > dein Konto > Grafana bei den anderen AWS-Werkzeugen.

## Konten und Cloud-Abläufe

KI-Nutzungsanzeigen erfordern einen installierten und eingerichteten Client; melde dich über dessen üblichen Ablauf an. Kontingente und Unternehmens-/API-Abrechnung können von den unterstützten Privatkonto-Panels abweichen. EITR enthält keine Zugangsdaten.

Cloud-Menüs verwenden deine lokalen Anbieterkonten und Profile. AWS-Profile stammen aus der lokalen AWS-Konfiguration oder EITRs eingerichteter Cloud-Profilzuordnung. Google Cloud listet benannte gcloud-Konfigurationen mit Konto und Projekt. Fehlt das Projekt, wird es beim Öffnen von Ressourcenwerkzeugen abgefragt; Anmelden bleibt bereits vor der Projektsuche verfügbar. Azure zeigt aktivierte Abonnements mit Mandanten-IDs. Wähle vor einem Werkzeug einen Kontext: Google-Cloud- und Azure-Werkzeuge werden innerhalb ihres Kontextmenüs gesucht, nicht global.

AWS-Konten benötigen einen passenden Abschnitt `[default]` oder `[profile NAME]` in der AWS-Konfigurationsdatei (`~/.aws/config` oder, falls gesetzt, `AWS_CONFIG_FILE`). Profile, die nur in der Zugangsdaten-Datei stehen, sowie Konfigurationsprofile mit `endpoint_url` (auch mit leerem Wert) werden ausgeschlossen, einschließlich verschachtelter Diensteinstellungen und referenzierter `[services NAME]`-Gruppen, da sie S3-kompatible Dienste wie Cloudflare R2 verwenden können. `EITR_AWS_PROFILES` kann zulässige Profile benennen oder einschränken, aber ausgeschlossene Profile nicht hinzufügen. EITR verändert keine der beiden AWS-Dateien.

Beim Öffnen eines Google-Kontexts werden unpassende geerbte Projektüberschreibungen entfernt; Konfigurationen ohne Projekt fragen für Ressourcenwerkzeuge nach einem. Die Rückkehr vom Terminal behält Kontext und ein gewähltes Projekt für projektlose Konfigurationen bei, ohne globale CLI-Vorgaben zu ändern. Anmelden, Authentifizierung prüfen und Aktualisieren liegen in jedem erkannten Kontext. Google-Anmelden verwendet das konfigurierte Konto; Azure-Anmelden den Mandanten und stellt danach das bisherige Standardabonnement wieder her. Azure-Aktualisieren erneuert den Abonnementcache und zeigt die Auswahl.

Jedes Anbietermenü beginnt mit **AWS-Konto hinzufügen**, **GCP-Konto hinzufügen** oder **Azure-Konto hinzufügen**. So kannst du beliebig viele Konten einrichten, etwa Entwicklung und Produktion eines Unternehmens. Nach der Namensabfrage läuft die eigene CLI-Einrichtung des Anbieters: AWS-Profil über AWS SSO (IAM Identity Center) oder Zugriffsschlüssel, getrennte gcloud-Konfiguration mit Anmeldung und Projekt oder Azure-Anmeldung mit selbst benannten Abonnements. Fehlendes `gcloud` oder `az` wird zuerst zur Installation angeboten. **Ctrl+R** benennt ein Konto um.

Die Namen stehen in `~/.config/eitr/cloud-contexts.json`, zugeordnet zu AWS-Profil, gcloud-Konfiguration oder Abonnement-ID. EITR leitet keine Umgebungen ab und speichert dort keine Zugangsdaten; Hinzufügen wechselt keine globale CLI-Vorgabe. Grafana und Cloud-Operationen benötigen passende Konten und Berechtigungen. Manche Aktionen lesen nur, andere verändern entfernte Ressourcen: Prüfe Vorgang und Konto vor der Bestätigung.

Halte Token, `.env`-Geheimnisse und Zugangsdaten aus geteilten Dotfiles und Screenshots heraus. Die Shell-Konfiguration lädt unterstützte Manager, ohne dass Installationsprogramme deine Profile umschreiben. Lernen enthält eigene Referenzen für LazyVim, tmux und cmux.

## Assistenten arbeiten zusammen

Entwicklung > KI > Assistenten zusammenarbeiten lassen ist standardmäßig aus.
Verbinde installierte Claude-, Codex-, Copilot-, Grok- und Gemini-CLI-Programme,
die angemeldet erscheinen. Jede Übergabe nutzt das Abonnement oder die
API-Abrechnung des Helfers und zählt zu dessen Limits. Bei anderen Clients
werden reine API-Schlüssel- oder Schlüsselbund-Anmeldungen nicht erkannt.

Gemini wird nur bei nicht leerem `GEMINI_API_KEY` oder `GOOGLE_API_KEY` erkannt,
oder wenn `security.auth.selectedType` in `~/.gemini/settings.json` auf
`gemini-api-key` oder `vertex-ai` steht. Private Google-Anmeldung zählt nicht:
Google bedient sie nicht mehr. Gemini läuft ohne Oberfläche im Planmodus,
ohne MCP-Server und Erweiterungen. Eitr hat es mit einem kostenlosen API-Schlüssel
getestet: Eine schreibgeschützte Frage und eine Frage über die Brücke wurden
beantwortet. Der Planmodus ist als schreibgeschützt dokumentiert; Eitr hat sein
Datei-, Shell- und Plandateiverhalten noch nicht unabhängig geprüft.

Bitte deinen Assistenten, den anderen für eine Prüfung, Erklärung oder einen
Vorschlag zu befragen. Bestätige jede Übergabe über die übliche Werkzeugabfrage
des aufrufenden Assistenten; Eitr genehmigt diese Werkzeuge niemals vorab.
Aktiviere keine automatische Werkzeugfreigabe für den Server assistants.
Helfer lesen nur; Änderungen übernimmt dein Hauptassistent. Ein Helfer kann
keinen weiteren Helfer aufrufen. Eine Benachrichtigung nennt die beteiligten
Assistenten, und jede Anfrage hat ein Zeitlimit von drei Minuten. Der Helfer
liest das aktuelle Arbeitsverzeichnis des Aufrufers; Frage und Kontext können
an den Anbieter dieses Assistenten gesendet werden.

Der Schalter registriert einen MCP-Server `assistants` über den eigenen Befehl
des jeweiligen Assistenten (`claude mcp add`, `codex mcp add`, `copilot mcp add` und `grok mcp add`, `gemini mcp add -s user`),
sodass jeder Assistent seine Einstellungen selbst schreibt. Ein vorhandener
gleichnamiger Server bleibt unverändert und wird gemeldet. Die Änderungen werden nur auf diesem
Computer unter `~/.local/state/eitr/assistants.json` (oder `XDG_STATE_HOME`)
vermerkt. Ausschalten entfernt genau Eitrs Einträge; wurde ein Eintrag danach
bearbeitet, bleibt er erhalten und Eitr meldet den Konflikt. Starte bestehende
Assistentensitzungen nach dem Umschalten neu. Die vollständige Prüfung mit
echten Konten erfolgt später in einem gesonderten Durchlauf.

Antigravity CLI (`agy`) ist für private Google-Konten unter Installieren > KI-CLIs und über den Starter beim ersten Aufruf verfügbar. Es wird nie mitgeliefert. Es wird über Googles offizielles Installationsprogramm installiert, das den Download prüft, und du meldest dich mit deinem Google-Konto an. Als Helfer für zusammenarbeitende Assistenten wird es noch nicht angeboten. Ein bereits installiertes `agy` kann normal gestartet werden. Gemini CLI benötigt einen Gemini-API-Schlüssel oder ein Google-Cloud-/Firmenkonto. Antigravity ist kein Zusammenarbeitshelfer: Ohne Oberfläche verweigert es selbst Lesezugriffe. Freigaben erfordern das Umgehen von Berechtigungen oder globale Regeln. Eitr prüft es erneut, sobald Berechtigungen pro Aufruf oder ein schreibgeschützter Modus ohne Oberfläche verfügbar sind.

### Weitere Anbieter

Entwicklung > Cloud enthält außerdem Cloudflare (`wrangler`), DigitalOcean (`doctl`), Hetzner Cloud (`hcloud`), Oracle Cloud (`oci`), Vercel, Netlify und IBM Cloud (`ibmcloud`). Füge ein Konto mit Kleinbuchstaben, Ziffern oder Bindestrichen hinzu. Diese privaten Arbeitsbereiche liegen unter `~/.config/eitr/cloud-accounts/<provider>/<name>`; bestehende Anbieter-Konfigurationen werden nie importiert. Anbieter und gewählter Arbeitsbereich bleiben in Werkzeugauswahl und Terminal sichtbar. Nach dem Terminal bleibt derselbe Arbeitsbereich gewählt; Shift+Backspace führt zur Kontoliste zurück. Die Auswahl ändert keine globale CLI-Vorgabe.

Fehlende Programme `wrangler`, `doctl` und `hcloud` werden aus den offiziellen Arch-Paketquellen angeboten (`doctl` und `hcloud` aus extra). Oracle Cloud und IBM Cloud verwenden ihre offiziellen HTTPS-Shell-Installer aus `distro/installers.json`; Oracle erhält `--accept-all-defaults`. Vercel (`vercel`) und Netlify (`netlify-cli`, Befehl `netlify`) nutzen das bestehende NVM/npm-Installationsrezept. Die Installation erfordert eine Bestätigung. Anmeldung und Kontoaktionen laufen ausschließlich im gewählten privaten Arbeitsbereich. DigitalOcean und Hetzner listen native Kontexte; Oracle listet Profile aus dessen `~/.oci/config`. Die Kontext-/Profilauswahl wird lokal gespeichert und pro Befehl übergeben, ohne globale Vorgaben zu ändern. Vercel und Netlify bieten ihre native Wechselaktion; danach wird die gewählte Team-/Kontobezeichnung eingegeben. Vercel fragt auch vor der Anmeldung nach einem Scope und übergibt bei weiteren Befehlen `--scope TEAM`. IBM bietet SSO- und API-Schlüssel-Anmeldung, zeigt `ibmcloud target` und wählt explizit Konto und Region. Kontext/Profil/Scope/Konto und gespeicherte Region bleiben bei der Rückkehr ins Menü sichtbar. Diese Bezeichnungen sind lokale Auswahlen, keine geprüften entfernten Identitäten. Bestehende Zugangsdaten und Anbieter-Variablen werden nicht übernommen. Browserkonsolen haben eigene Sitzungen; vor Aktionen das Konto prüfen.

Die sieben Anbieter mit privaten Arbeitsbereichen verwenden neutrale Ressourcen- und Aktionssymbole mit kurzen Beschreibungen. Konten stehen zuerst in alphabetischer Reihenfolge, gefolgt von Konto hinzufügen; Werkzeuge werden nach ihren übersetzten Namen alphabetisch sortiert. Die Auswahl zeigt Konto, Kontext und gespeicherte Region; jeder schreibgeschützte Bericht wiederholt diesen Kontext über seiner Ausgabe. Berichte behalten den gemeinsamen AWS-Pager; es kommen keine weiteren Ressourcenbefehle oder Protokollsuchen hinzu.

| Anbieter | Anmeldung | Liste / Wechsel / Befehlskontext |
| --- | --- | --- |
| Cloudflare | `wrangler login` | — |
| DigitalOcean | `doctl auth init --context NAME` | `doctl auth list`; `doctl auth switch --context NAME`; `--context NAME` |
| Hetzner Cloud | `hcloud context create NAME` | `hcloud context list`; `hcloud context use NAME`; `--context NAME` |
| Oracle Cloud | `oci session authenticate --profile-name NAME --region REGION` | `~/.oci/config`; `--profile NAME --auth security_token` |
| Vercel | `vercel login` | `vercel switch`; `--scope TEAM` |
| Netlify | `netlify login` | `netlify switch` |
| IBM Cloud | `ibmcloud login --sso`; `ibmcloud login --apikey` | `ibmcloud target`; `ibmcloud target -c ACCOUNT -r REGION` |

Die Cloud-Navigation verwendet echte Elephant-Menüs. Shift+Backspace führt zum vorherigen Menü: Ein Dienst oder eine Ressourcenauswahl kehrt zum übergeordneten Menü zurück, das Kontomenü zur Kontenliste des Anbieters und diese Liste zu Cloud. Das gewählte Konto und der Kontext bleiben sichtbar. Eitr speichert diese Navigationsauswahl in `~/.config/eitr/cloud-navigation.json`; die globalen CLI-Standardeinstellungen der Anbieter bleiben unverändert. Berichte behalten ihren Pager, Protokollsuchen behalten fzf und die Einrichtung behält ihre Terminalformulare mit Überprüfung. Freitextsuchen nehmen weiterhin Text in Walker entgegen; sie sind keine Navigationslisten.

Lösche ein Konto mit Delete in seiner Zeile oder **Konto löschen** in seinem Menü. Die Bestätigung nennt Anbieter und Konto: Sie entfernt dessen Anbieter-Anmeldung auf diesem Computer, ohne das entfernte Konto zu beeinflussen. Abbrechen ändert nichts. Nur der ausgewählte private Eitr-Kontoordner wird entfernt; symbolische Links, Pfade außerhalb des Anbieter-Stammordners und Konten mit laufender Eitr-Aktion werden abgelehnt. AWS, Azure und Google Cloud erhalten diese Aktion nicht. Die Bestätigung erscheint in Walker mit Abbrechen und Bestätigen; es öffnet sich kein Terminal.

Schreibgeschützte Berichte verwenden die private Umgebung des gewählten Kontos und den bestehenden Cloud-Pager. Cloudflare: Konto, R2-Buckets, D1-Datenbanken, KV-Namensräume, Pages-Projekte, Warteschlangen. DigitalOcean: Droplets, Apps, Datenbanken, Kubernetes, Volumes, Domains, Lastverteiler, Guthaben. Hetzner: Server, Volumes, Netzwerke, Firewalls, Lastverteiler, primäre IPs, Snapshots. Oracle: Compartments, Instanzen, Buckets, VCNs. Vercel: Projekte, Bereitstellungen, Domains. Netlify: Status, Websites. IBM: Konto, Ziel, Ressourcengruppen, Dienstinstanzen. DigitalOcean und Hetzner übergeben immer den gewählten Kontext; Oracle übergibt Profil und Sicherheitstoken-Authentifizierung und liest die Tenancy nur aus dem privaten Profil dieses Kontos. Vor der Bucket-Liste wird der Namensraum abgefragt. Vercel übergibt den gewählten Team-Scope. Fehler bleiben lesbar und führen nie zu einem erneuten Versuch mit einem anderen Konto. Protokollsuchen behalten den bestehenden fzf-Viewer. Live-Prüfungen mit echten Konten stehen weiterhin aus.

Die Formulare für Cloud-Konten, Git Accounts (Hinzufügen und Bearbeiten), Monitoring-Dashboards und Web-Apps zeigen die Schritte links und die aktuelle Antwort rechts. Mit Pfeilen oder Tab einen Schritt wählen und mit Enter beantworten. Die Übersicht zeigt alle Antworten, bevor Änderungen angewendet werden; mit Links oder den anderen Pfeilen zu einem Schritt zurückkehren und lange Übersichten mit PgUp/PgDn durchblättern. Esc oder Ctrl+C bricht ohne Speichern ab. Die Anbieteranmeldung beginnt nach der Übersicht; bei einem Fehler oder Abbruch wird das neue Konto verworfen. Google Cloud fragt vor der Anmeldung nach einer optionalen Projekt-ID. Azure fragt vorher nach einer optionalen Bezeichnung für Abonnements und behält sonst deren vorhandene Namen. Vercel fragt vor der Anmeldung nach dem Geltungsbereich.
