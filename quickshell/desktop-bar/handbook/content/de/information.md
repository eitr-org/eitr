# Informationen, Medien und Benachrichtigungen

Benachrichtigungskarten zeigen unter dem Titel das lokale Eingangsdatum und die Uhrzeit, sowohl in Popups als auch im Verlauf. Diese Zeiten bleiben nur für die laufende Sitzung erhalten.

## Systeminformationen lesen

Öffne Einstellungen > Über für Eitr-Version, Codename, Aktualisierungskanal, Kernel und Lizenz sowie Prozessor, Grafik, Mainboard, eingebauten Arbeitsspeicher und jedes angeschlossene Laufwerk mit seiner Kapazität. Die Systemübersicht zeigt dein Profil, die aktuelle Hardwareauslastung und die Netzwerkgeschwindigkeit (Download und Upload). Für Hardwaredetails, KI-Nutzung und Wetter klicke auf die Leistensymbole; Walker findet sie auch nach Namen.

**Hardware** zeigt CPU, GPU, RAM und den Speicher des Laufwerks, auf dem `/` liegt. Andere Laufwerke werden nicht in diese Summe einbezogen. Fehlende Sensor- oder GPU-Daten werden als nicht verfügbar gekennzeichnet.

Unter Einstellungen > Über können Sie unter „Über-Logo“ Emblem oder Runen für die Über-Seite im Terminal wählen. Die Auswahl bleibt auf diesem Rechner gespeichert; standardmäßig wird Emblem verwendet. Beide folgen der Akzentfarbe des aktuellen Designs.


**KI-Nutzung** erkennt installierte oder konfigurierte Clients. Zuerst erscheint die zwischengespeicherte Nutzung; Aktualisieren startet weder Anmeldung noch Gespräche. Die Grenzen jedes Kontos werden angezeigt. Prozentwerte geben den bereits verbrauchten Anteil eines Limits an.

Jeder erkannte Anbieter hat einen eigenen Abschnitt mit Tarif, Limits und Fehlern. Klicke auf eine Überschrift, um nur diesen Abschnitt ein- oder auszuklappen. Nach der Anmeldung sind alle eingeklappt; der Zustand bleibt für die Sitzung erhalten. Lange Listen lassen sich innerhalb des Bildschirms scrollen.

**Wetter** verwendet den Standardstandort und erlaubt vorübergehende Stadtsuchen. Die temporäre Auswahl endet beim Schließen des Panels. Escape leert zuerst die Stadtsuche und schließt erst danach. Temperatureinheiten richten sich nach dem Standort; daneben steht eine alternative Einheit.

## Kalender und Medien

Klicke für den Kalender auf Uhr oder Datum. Er zeigt sechs Wochenzeilen und darunter den Jahresfortschritt. Navigiere mit Zurück/Weiter, Heute, Pfeiltasten oder T. Bei versteckter Leiste suche in Walker nach Kalender. Klicke auf einen Tag, um seine Erinnerungen unter dem Raster zu sehen; das + neben dem Tag öffnet seine Pläne an Ort und Stelle, mit einem Feld, um für diesen Tag eine Erinnerung zu einer Uhrzeit hinzuzufügen, und der Zurück-Pfeil führt zum Monat zurück.

Klicke auf den animierten Equalizer für das Panel Medien: das Cover, umgeben von Balken im Takt der Musik, der Song, sein Text, Zurück/Wiedergabe/Weiter sowie das Springen innerhalb des Titels, falls unterstützt. Ohne geeigneten Player wird er ausgeblendet; erkannte Besprechungen werden ausgeschlossen. Der Equalizer der Leiste folgt dem aktuellen Systemaudio über einen eigenen cava-Prozess, nur solange die Wiedergabe läuft und die Anzeige sichtbar ist. Ziehe den Equalizer nach links, um ihn gegen die gerade gesungene Zeile zu tauschen; Ziehen der Zeile in eine Richtung tauscht ihn zurück; Pause oder ein Songwechsel lassen sie stehen. Online-Songtexte sind eine Einstellung der Desktopleiste (siehe das Kapitel Leiste und Arbeitsflächen).

## Benachrichtigungen

**SUPER + N** oder die Glocke öffnet die Benachrichtigungszentrale. Benachrichtigungen sind nach Anwendung gruppiert. Die neueste Karte liegt vorn im Stapel; erweitere ihn für ältere Karten. Du kannst eine Karte verwerfen, eine Gruppe oder alle löschen. Popups bilden ebenfalls Stapel je Anwendung, mit der neuesten Meldung vorn. Darüberhalten des Zeigers pausiert ihre Ablaufzeit.

**SUPER + Alt + N** führt die Hauptaktion der neuesten Benachrichtigung aus (wie ein Klick darauf), **SUPER + Alt + Shift + N** schließt sie. Eine wiederholte Benachrichtigung (gleiche App, gleicher Titel und Text) ersetzt die frühere und zeigt eine Anzahl wie ×3, statt eine weitere Karte zu stapeln.

Benachrichtigungen leuchten sanft nach innen in der Akzentfarbe des Themes. Kritische verwenden stattdessen dessen Rot; solche mit niedriger Priorität bleiben dezent und ohne Leuchten. Nicht stören unterdrückt Popups, ohne den Verlauf zu löschen. Dieser bleibt bei Konfigurationsneuladungen im Speicher, aber nicht bei einem Prozessneustart. Benachrichtigungsinhalte werden nicht protokolliert.

Ein Klick auf eine Benachrichtigung führt ihre Hauptaktion aus. Eine ohne Aktion öffnet die App, die sie gesendet hat: ihr Fenster oder bei herdr das Terminal mit herdr, auf dem Arbeitsbereich und Tab, die die Benachrichtigung nennt. Jede Karte zeigt das eigene Symbol der App, sonst die Glocke.

Popups erscheinen auf jedem Bildschirm. Schalte Popups auf jedem Bildschirm unter Einstellungen > Benachrichtigungen aus, damit sie nur auf dem Hauptbildschirm erscheinen. Dort findest du auch Nicht stören und Absturzbenachrichtigungen.
