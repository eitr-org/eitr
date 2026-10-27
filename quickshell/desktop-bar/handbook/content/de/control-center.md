# Kontrollzentrum

**SUPER + ,** öffnet oder schließt das Kontrollzentrum. Es öffnet am aktuellen Leistenrand und schließt mit Escape oder einem Klick außerhalb. Beim Schließen wird auf Allgemein zurückgesetzt.

Seine fünf Seiten enthalten alles außerhalb von Entwicklung, Apps, Installieren, Lernen und Spielen; die meisten Einstellungen brauchen daher keinen Walker. Einklappbare Abschnitte beginnen geschlossen; ein Klick auf den Titel schaltet sie um und bleibt bis zur Abmeldung gespeichert. Gibt es ein eigenes Leistenpanel (OBS, WiFi, Bluetooth, Audio, Bildschirm, Hardware, KI-Nutzung, Wetter), öffnet das Kontrollzentrum dieses.

## Allgemein

- **Verbindungen:** WiFi- und Bluetooth-Schalter sowie Flugmodus.
- **Schnellschalter:** automatische Bildschirmsperre, Absturzbenachrichtigungen, Nicht stören, Spielmodus (Effekte, Unschärfe und Popups aus, Leistungsprofil an, bis du ihn ausschaltest) und Nachtlicht. Ein eingeschalteter Schalter füllt sich mit der Akzentfarbe des Designs. Darunter führen Leiste ausblenden (SUPER+Shift+Space holt sie zurück) und Bildschirmschoner einmalig eine Aktion aus.
- **Ton:** Lautstärke sowie Mikrofonverstärkung und Stummschaltung.
- **Bildschirm:** Helligkeit.
- **Medien:** Cover, Interpret, Wiedergabesteuerung und Positionswahl, sofern unterstützt.
- **Energie:** Sperren sowie **Ein/Aus…**, das Abmelden, Bereitschaft, Neustart und Ausschalten aufklappt.

Der Flugmodus merkt sich gesperrte Funkverbindungen und stellt nur diese wieder her. Nicht stören unterdrückt Popups, ohne den Verlauf zu löschen. Automatische Sperre ist nicht dasselbe wie das Verhindern des Schlafmodus; beachte den Schutz deines Bildschirminhalts.

## Stil

Design und Hintergrundbild öffnen ihre Karussells; Standardschrift öffnet die Schriftliste. Sperrbildschirmdesign, Mauszeiger (Familie, Größe, Farbe), Leistenerscheinung, Layout, Rand und Bildschirme, Arbeitsflächenmarkierungen, Ecken und Kittys Cursor Fire ändere direkt im Panel. Die Einstellungen werden mit Walker geteilt.

## Werkzeuge

Screenshots (Auswahl, Vollbild, Fenster oder Auswahl direkt in die Zwischenablage), Aufnahme (OBS-Steuerung, Aufnehmen, Aufnehmen + Audio und Stopp), OCR, QR-Codes, Farbauswahl, Transkodieren, Erinnerungen und LocalSend-Freigabe. Das Panel schließt vor Beginn einer Auswahl oder Aufnahme.

## System

- **Geräte:** Panels für Audio, Mikrofon, Bildschirm (Auflösung, Bildwiederholrate, Skalierung), Bluetooth und WiFi, Beleuchtung und Akkuladelimit auf Laptops.
- **Tastatur:** Belegungen wählen, hinzufügen und entfernen; mindestens eine bleibt erhalten.
- **Nachtlicht und Hauptbildschirm:** Nachtlichtmodus und Zeitplan, getrennt vom manuellen Schalter, sowie der Hauptbildschirm mit der Leiste.
- **Informationen:** Über, Hardware, KI-Nutzung, Wetter und Problem melden.
- **Aktualisierungen:** Kanal, Systemaktualisierung, Änderungen jeder Aktualisierung sowie reine Pacman- oder AUR-Updates.
- **Snapshots und Bereinigung:** Datei wiederherstellen, persönliche und System-Wiederherstellungs-Snapshots samt Anleitung, Bereinigung und Dotfiles.

Sicherheit, Zurücksetzen auf den Werkszustand und Netzwerk-Backend bleiben unter Walker > System mit eigenen Bestätigungen.

## Sprache

**System > Sprache** zeigt die aktuelle Sprache entsprechend dem Gebietsschema. Öffne die Auswahl, wähle eine Sprache oder Systemstandard und melde dich zur Anwendung ab und wieder an. Nur die Meldungssprache deiner Sitzung wird geändert, niemals System-Gebietsschemadateien. Siehe [Sprachanleitung](handbook:language).

## Schnellchat

Das Chatsymbol neben den Seiten öffnet eine flüchtige Unterhaltung mit dem unter Entwicklung > KI gewählten Standardassistenten. Ohne Standard oder bei deaktivierender Organisationsrichtlinie bleibt es verborgen. Enter sendet, Shift+Enter fügt einen Zeilenumbruch ein. Escape oder Zurück kehrt zu den Seiten zurück. Neuer Chat, Verlassen des Chats oder Schließen des Kontrollzentrums löscht alle Nachrichten und bricht ausstehende Antworten ab.

Antworten bieten auswählbares Markdown und Kopieren. Die Unterhaltung bleibt im Arbeitsspeicher; Eitr schreibt weder Verlauf noch Protokolle. Unter der Eingabe steht der Cloudanbieter oder der Hinweis, dass Ratatoskr auf diesem PC läuft. Cloudanbieter erhalten Nachrichten und bisherige Gesprächsbeiträge. Jede Nachricht enthält außerdem nur Eitr-Version/Kanal, Kernel, CPU/GPU/RAM und Thema als nicht vertrauenswürdigen Kontext. Benutzernamen, Hostnamen, Dateien, E-Mails, WLAN-Namen, Fenstertitel und Zwischenablage werden nicht erfasst. Der Assistent verwendet den schreibgeschützten Aufruf ohne Oberfläche mit dem ausgewählten Konto und kann das System nicht ändern. Fehler erscheinen im Chat.

## Plugins

**Kontrollzentrum > Plugins** zeigt für jedes installierte Plugin eine kompakte Zeile mit Symbol, Namen und Aktivierungsschalter. Wähle eine Zeile, um Autor, Version, Beschreibung, Aktualisieren/Entfernen, Widgets, Leistenelemente und Vorschau zu sehen. Mit Zurück oder Escape kehrst du zur Liste zurück. Aktivieren/Deaktivieren erhält Positionen und stoppt oder startet Dienste, Walker-Einträge, Hooks und visuelle Komponenten; per CLI: `eitr plugin enable ID` oder `eitr plugin disable ID`. Plugin hinzufügen…, Aktualisieren und Entfernen öffnen die geprüften Terminalabläufe; Entfernen verlangt Bestätigung. Allgemein behält nur Plugin-Kacheln. Visuelle Fehler haben eine unabhängige Aktion zum erneuten Aktivieren.
