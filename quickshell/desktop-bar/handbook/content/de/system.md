# In den Einstellungen zurechtfinden

Öffne **SUPER + F > Einstellungen**. Zuerst kommen Ordner, dann Aktionen, jeweils alphabetisch. Die globale Suche findet auch frühere Namen wie System und Toggle.

**Verbindungen**, **Geräte und Eingabe**, **Sprache**, **Sicherheit**, **Stil**, **System** sind Ordner. **Kontrollzentrum** öffnet dieselben Bedienelemente wie SUPER + Komma. **Konfigurationsdateien** öffnet deinen Konfigurationsordner in VS Code oder LazyVim.

Verbindungen öffnet die nativen Bluetooth- und WiFi-Panels, Netzwerk-Backend und Fernzugriff. Die Backend-Auswahl bereitet den nächsten Start vor, ohne die laufende Verbindung neu zu starten.

Geräte & Eingabe enthält Audio, Batterieladegrenzwert, Anzeige, Tastatur, Beleuchtung und Mikrofon. Der Batterieladegrenzwert erscheint nur mit einer Systembatterie und benötigt unterstützte Firmware. Peripheriebatterien aktivieren keine Laptop-Bedienelemente. Anzeige enthält Helligkeit, Nachtlicht und unterstützte Laptop-Energieprofile.

Beleuchtung ist standardmäßig ausgeschaltet. Thema folgen lässt Themenwechsel die von OpenRGB gesteuerten Geräte neu einfärben.

Stil enthält die bisherigen Optionen für Thema, Hintergrundbild, Sperrbildschirm, Schriften und Desktop-Aussehen. Im Hauptmenü heißt Toggle jetzt Schnellaktionen; Bildschirmschoner starten startet ihn sofort.

**Einstellungen > System** enthält **Informationen**, **Instandhaltung**, **Update-Kanal**, **Über**, **Systemaktualisierung**. Über öffnet die EITR-Systemübersicht. Informationen enthält KI-Nutzung, Hardware, Problem melden und Wetter. Kalender, Arbeitsbereichsübersicht und Ragnarök bleiben über die globale Suche erreichbar.

Wartung enthält Werksreset, Snapshots, Diesen PC prüfen, Schnellste Spiegel auswählen und Bereinigung. Der Werksreset verlangt zwei Warnungen und eine eingetippte Bestätigung; lies zuerst [Werksreset](handbook:factory-reset).

Sicherheit behält die bisherigen Authentifizierungs-, Firewall- und Benutzerfunktionen. Die Dokumentation bleibt unter [Secure Boot](handbook:secure-boot). Hardware-Anpassungen gehören in `~/.config/hypr/local.lua`; halte Geheimnisse aus Konfigurationssicherungen heraus.

**Walker > Einstellungen > Sprache** listet die Sprachen mit markierter aktueller Auswahl; siehe [Sprache](handbook:language). Englische und übersetzte Namen bleiben suchbar. Hauptmenü und Apps behalten ihre eigene Reihenfolge.

Sicherheit: Assistentenzugriff, FIDO2 Sicherheitsschlüssel, Fingerabdrücke, TPM-Laufwerksentsperrung, Benutzer, Firewall, Zurück zur Passwort-Authentifizierung, Passwort ändern.
