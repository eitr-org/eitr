# Aufnahme und Teilen

Aufnahmewerkzeuge liegen unter Hauptmenü > Werkzeuge > Aufnahme sowie Kontrollzentrum > Werkzeuge.

## Screenshots und Texterkennung

- **Print:** vollständiger Screenshot im schwebenden Editor.
- **SUPER + Print:** eingefrorene Auswahl im schwebenden Editor.
- **SUPER + Shift + Print:** aktives Fenster im Editor aufnehmen.
- **SUPER + Ctrl + Print:** Text aus einer Auswahl per OCR erkennen.
- **SUPER + Alt + Print:** QR-Code aus einer Auswahl auslesen.
- **SUPER + =:** Farbe auswählen und kopieren.

Nach einem Screenshot trifft ein kurzer Blitz die erfasste Fläche. Der Effekt beginnt erst nach der Bilderfassung und erscheint deshalb nicht im Screenshot.

Prüfe den Inhalt vor dem Speichern oder Teilen. OCR kann Fehler machen; QR-Codes können private Zugangsdaten oder nicht vertrauenswürdige URLs enthalten. Ein Bildeditor garantiert nicht, dass vertraulicher Hintergrundtext entfernt wurde.

## Aufnahme und Streaming

Bildschirmaufnahme öffnet die OBS-Steuerung. Sie verwendet deine eingerichtete Szene und gespeicherte Wayland-Aufnahmeberechtigung; die Szene muss eine sichtbare Monitorquelle enthalten. Der Aufnahmestart bereitet OBS vor und schließt das Panel, bevor die Erfassung beginnt. Die Steuerung nutzt OBS-WebSocket, das standardmäßig ausgeschaltet ist: Eitr aktiviert es mit Passwort, wenn OBS erstmals geschlossen ist. Ist OBS dabei geöffnet, schließe es einmal und versuche es erneut.

Aufnahmen werden unter **Videos/Records** im persönlichen Ordner gespeichert. OBS verwendet standardmäßig den persönlichen Ordner selbst; Eitr ändert nur diesen Standard. Ein unter OBS > Einstellungen > Ausgabe selbst gewählter Ordner bleibt erhalten.

Während OBS aufnimmt oder streamt, erscheint ein roter Punkt neben dem Wetter. Klicke für Laufzeit, Dateigröße, Pause/Fortsetzen, Stopp, Kapitelmarken (erfordern OBS-Format Hybrid MP4), OBS-Mikrofon und -Kamera sowie Szenenauswahl. Ein Stream zeigt einen LIVE-Zähler mit eigenem Stopp. Nach Aufnahmeende bietet eine Benachrichtigung Ordner öffnen und Pfad kopieren an. Prüfe Audio-/Mikrofonauswahl und Monitor vor dem Start. Die Webcam benötigt eine OBS-Kameraquelle. Aufnahmeschalter für Audio betreffen OBS-Eingänge, nicht die Systemlautstärke.

Das Handbuch startet niemals Aufnahmen oder Streams. Bildschirmfreigabe und Aufnahme bleiben ausdrückliche Aktionen. Transkodieren öffnet den vorhandenen Ablauf zur Bild-/Videokonvertierung; prüfe Ausgabepfade, bevor du Dateien ersetzt.

Bei einer neuen OBS-Konfiguration erstellt Eitr die Sammlung Untitled mit einer Scene: Bildschirmaufnahme, ausgeblendete Kamera sowie Standardaudio von Desktop und Mikrofon. Beim ersten Einsatz fragt das System, welchen Bildschirm du teilen möchtest; OBS speichert die Berechtigung. Die Kamera bleibt aus, bis du sie einschaltest. Vorhandene Sammlungen werden nie verändert.

## Teilen

Hauptmenü > Werkzeuge > Teilen bietet LocalSend und vorhandene Übertragungswerkzeuge. Zum Senden wähle Ziel beziehungsweise Gerät. Prüfe die Empfänger und teile keine privaten Schlüssel, Wiederherstellungscodes, Token oder vollständigen ungeprüften persönlichen beziehungsweise Konfigurationsordner.
