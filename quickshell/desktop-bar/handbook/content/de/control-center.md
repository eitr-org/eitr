# Kontrollzentrum

**SUPER + I** öffnet oder schließt das Kontrollzentrum. Es öffnet am aktuellen Leistenrand und schließt mit Escape oder einem Klick außerhalb. Beim Schließen wird auf Allgemein zurückgesetzt. Mit einer Full-Leiste am linken oder rechten Rand beginnt das Kontrollzentrum am oberen Bildschirmrand. Der Inhalt hat Innenabstand innerhalb der mit der Leiste verbundenen Fläche.

Seine Seiten sind Allgemein, Plugins und Werkzeuge. Die Zahnrad-Schaltfläche darunter, **Alle Einstellungen**, schließt das Kontrollzentrum und öffnet die Einstellungen mit Darstellung, Leiste, Geräten, Tastatur, Bildschirmen und System. Einklappbare Abschnitte beginnen normalerweise geschlossen; ein Klick auf den Titel schaltet sie um und bleibt bis zur Abmeldung gespeichert. Hat die Leiste ein eigenes Panel, etwa OBS, WiFi oder Bluetooth, öffnet das Kontrollzentrum dieses.

## Allgemein

<!-- eitr-figure: control-center -->

Die Seite Allgemein. Die Schaltflächen links wechseln zwischen Allgemein, Plugins und Werkzeuge; das Zahnrad darunter öffnet die Einstellungen. Ein eingeschalteter Schalter füllt sich mit der Akzentfarbe des Designs.

- **Verbindungen:** WiFi- und Bluetooth-Schalter sowie Flugmodus.
- **Schnellaktionen:** automatische Bildschirmsperre, Nicht stören, Spielmodus (Effekte, Unschärfe und Popups aus, Leistungsprofil an, bis du ihn ausschaltest) und Nachtlicht. Darunter führen Leiste ausblenden (SUPER+Shift+Space holt sie zurück) und Bildschirmschoner einmalig eine Aktion aus.
- **Ton:** Lautstärke sowie Mikrofonverstärkung und Stummschaltung, dazu zwei optionale, standardmäßig ausgeschaltete Schalter: **Benachrichtigungstöne** (ein Klang, ein anderer für dringende Benachrichtigungen; unwichtige bleiben still) und auf PCs mit Akku **Ladetöne** beim An- und Abstecken des Ladegeräts. Beide schweigen bei Nicht stören und im Spielmodus. Walker > Einstellungen > Geräte > Ereignisklänge bietet dieselben Schalter.
- **Bildschirm:** Helligkeit, auf Laptops mit eingebautem Bildschirm.
- **Medien:** Cover, Interpret, Wiedergabesteuerung und Positionswahl, sofern unterstützt.
- **Energie:** Sperren sowie **Ein/Aus…**, das Abmelden, Bereitschaft, Neustart und Ausschalten aufklappt.

Der Flugmodus merkt sich gesperrte Funkverbindungen und stellt nur diese wieder her. Nicht stören unterdrückt Popups, ohne den Verlauf zu löschen. Automatische Sperre ist nicht dasselbe wie das Verhindern des Schlafmodus; beachte den Schutz deines Bildschirminhalts.

## Werkzeuge

Timer & Fokus (ein Countdown, eine Stoppuhr oder Fokussitzungen von 25 Minuten mit 5-minütigen Pausen; ein Ring neben der Uhr zeigt, dass er läuft, und öffnet ihn), Screenshots (Auswahl, Vollbild, Fenster oder Auswahl direkt in die Zwischenablage), Aufnahme (OBS-Steuerung, Aufnehmen, Aufnehmen + Audio und Stopp), OCR, QR-Codes, Farbauswahl, Transkodieren, Erinnerungen und LocalSend-Freigabe. Das Panel schließt vor Beginn einer Auswahl oder Aufnahme.

## Schnellchat

Wähle deinen Standardassistenten unter Einstellungen > KI-Assistent.

Das Chatsymbol neben den Seiten öffnet eine flüchtige Unterhaltung mit dem unter Entwicklung > KI gewählten Standardassistenten. Ohne Standard oder bei deaktivierender Organisationsrichtlinie bleibt es verborgen. Enter sendet, Shift+Enter fügt einen Zeilenumbruch ein. Escape oder Zurück kehrt zu den Seiten zurück. Neuer Chat, Verlassen des Chats oder Schließen des Kontrollzentrums löscht alle Nachrichten und bricht ausstehende Antworten ab.

Antworten bieten auswählbares Markdown und Kopieren. Die Unterhaltung bleibt im Arbeitsspeicher; Eitr schreibt weder Verlauf noch Protokolle. Unter der Eingabe steht der Cloudanbieter oder der Hinweis, dass Ratatoskr auf diesem PC läuft. Cloudanbieter erhalten Nachrichten und bisherige Gesprächsbeiträge. Die Maschinenübersicht enthält Eitr-Version/Kanal, Kernel, CPU/GPU/RAM und Thema als nicht vertrauenswürdigen Kontext. Benutzernamen, Hostnamen, Dateien, E-Mails, WLAN-Namen, Fenstertitel und Zwischenablage werden nicht erfasst. Der Assistent verwendet den schreibgeschützten Aufruf ohne Oberfläche mit dem ausgewählten Konto und kann das System nicht ändern. Fehler erscheinen im Chat.

Der Assistent erhält außerdem Eitrs Handbucheinführung und passende übersetzte Auszüge, eine feste Liste installierter Desktop-Werkzeuge und die Angabe, ob ein HDR-Monitor angeschlossen ist. Das beschreibt die Verfügbarkeit, nicht die Einrichtung eines Dienstes. Der Assistent kann keine Befehle ausführen oder Einstellungen ändern.

## Plugins

**Kontrollzentrum > Plugins** zeigt für jedes installierte Plugin eine kompakte Zeile mit Symbol, Namen und Aktivierungsschalter. Wähle eine Zeile, um Autor, Version, Beschreibung, Aktualisieren/Entfernen, Widgets, Leistenelemente und Vorschau zu sehen. Mit Zurück oder Escape kehrst du zur Liste zurück. Aktivieren/Deaktivieren erhält Positionen und stoppt oder startet Dienste, Walker-Einträge, Hooks und visuelle Komponenten; per CLI: `eitr plugin enable ID` oder `eitr plugin disable ID`. Plugins hinzufügen, Aktualisieren und Entfernen öffnen die geprüften Terminalabläufe; Entfernen verlangt Bestätigung. Allgemein behält nur Plugin-Kacheln. Visuelle Fehler haben eine unabhängige Aktion zum erneuten Aktivieren.

Installation, Prüfung und sichere Updates erklärt [Apps und Installation](handbook:apps).

Einstellungen (**SUPER + ,**) und Profilbilder erklärt [Einstellungen](handbook:system).
