# Im Systemmenü zurechtfinden

Öffne **SUPER + F > System**. Aktionen sind alphabetisch gruppiert. Die globale Suche findet sie weiterhin direkt, ohne dass du jede Gruppe öffnen musst.

## Konnektivität

**Bluetooth**, **Netzwerk-Backend**, **WiFi**. Die Geräteeinträge öffnen dieselben Panels wie die Leiste. Die Wahl des Netzwerkdienstes bereitet den nächsten Start vor, ohne die laufende Verbindung neu zu starten.

## Geräte und Eingabe

**Audio**, **Batterieladegrenzwert**, **Bildschirm**, **Tastatur**, **Beleuchtung**, **Mikrofon**. Die Ladegrenze benötigt unterstützte Laptop-Firmware. Anzeige enthält Helligkeit, Nachtlicht, Monitorauswahl und unterstützte Laptop-Energieprofile.

**Beleuchtung** bestimmt, ob Designwechsel Lüfter, Tastaturen und andere OpenRGB-Geräte umfärben. Standardmäßig ist das ausgeschaltet; EITR lässt deine Beleuchtung unverändert. **Design folgen** übernimmt die aktuelle Designfarbe sofort und bei jedem Designwechsel.

## Informationen

**Über**, **KI-Nutzung**, **Hardware**, **Problem melden**, **Wetter**. Über öffnet die EITR-Systemzusammenfassung. Problem melden sammelt einen vertraulichen Bericht, den du vor dem Senden liest. Die anderen Einträge öffnen native Panels. Kalender und Arbeitsflächenübersicht bleiben in Leiste und globaler Suche, statt dieses Menü zu füllen. Suche **Ragnarök**, damit Fenrir in den Bildschirm beißt; Klick oder Escape beendet den Effekt vorzeitig.

## Instandhaltung

**Bereinigung**, **Werkseinstellungen**, **Momentaufnahmen**, **Aktualisierung**. Aktualisieren trennt Systemaktualisierung und erweiterte Paketaktualisierungen. Zurücksetzen auf Werkseinstellungen ist destruktiv und verlangt zwei Warnungen. Lies vorher [Werkseinstellungen](handbook:factory-reset).

## Sicherheit

**FIDO2 Sicherheitsschlüssel**, **Fingerabdrücke**, **TPM-Laufwerksentsperrung**, **Firewall**, **Zurück zur Passwort-Authentifizierung**, **Passwort ändern**. Die Secure-Boot-Anleitung liegt unter **Lernen > EITR-Handbuch > Secure Boot**, nicht in einer eigenen Menü- oder Sicherheitsaktion.

## Dotfiles

Öffnet deinen Konfigurationsordner in VS Code oder, falls nicht installiert, in LazyVim. Rechnerspezifische Monitor- und Hardwarevorgaben gehören in `~/.config/hypr/local.lua`, nicht in gemeinsame Standards. Füge keine Token, Wiederherstellungsschlüssel oder Passwörter in Konfigurationssicherungen ein.

Die folgenden Kapitel erklären Abläufe und Sicherheitsgrenzen genauer.

## Sprache

**Walker > System > Sprache** listet die Sprachen auf, die aktuelle ist markiert; siehe [Sprachanleitung](handbook:language). Englische und übersetzte Namen bleiben suchbar. Untermenüs stehen vor Aktionen; beide werden nach übersetzten Titeln sortiert. Hauptmenü und Anwendungen behalten ihre Reihenfolge.
