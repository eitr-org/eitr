# WiFi, Bluetooth und Flugmodus

Öffne die Leistensymbole oder **System > Verbindungen**. Ein Panel zu öffnen wechselt niemals selbstständig den Netzwerkdienst oder trennt Geräte.

## WiFi

Das Panel trennt verbundene, bekannte und andere Netzwerke. Wähle ein verfügbares Netzwerk zum Verbinden; Passwortfelder verbergen den Inhalt. Gespeicherte nicht erreichbare Netzwerke bleiben ohne erfundene Signalprozentwerte sichtbar. Trennen liegt in der verbundenen Zeile; ein gespeichertes Netzwerk zu vergessen verlangt Bestätigung.

Oben stehen Netzwerkstatus, Ping, WiFi-Band, IP-Adresse und Gateway. QR-Freigabe verwendet ein bereitgestelltes WiFi-Passwort und hält das Bild im Speicher. Unternehmenszugangsdaten werden nicht als persönlicher Netzwerk-QR geteilt.

Für Unternehmensnetzwerke werden PEAP/MSCHAPv2 und TTLS/PAP unterstützt. Frage den Administrator nach Benutzername, CA-Zertifikat und Domäne des Authentifizierungsservers. Deaktiviere die Zertifikatsprüfung nicht. Andere Verfahren brauchen eine erweiterte Einrichtung. Siehe [Netzwerkdienste](handbook:network-backends).

## Bluetooth

Schalte den Adapter ein oder aus, suche, kopple, verbinde, trenne oder vergiss Geräte. Verbundene, bekannte und neu entdeckte Geräte bilden eigene Gruppen. Eine vom Panel gestartete Suche endet nach 20 Sekunden oder beim Schließen.

Kopplung kann eine PIN oder einen Bestätigungsagenten benötigen. Der Desktop verwendet dafür derzeit Blueman. Ein schon gekoppeltes Gerät erneut zu verbinden belegt nicht, dass neue Kopplungen funktionieren. Behalte den Agenten, bis eine Kopplung mit PIN oder Bestätigung geprüft wurde. Die Abdeckung bei Neuinstallationen muss weiterhin geprüft werden.

## Flugmodus

Kontrollzentrum > Allgemein blockiert WiFi und Bluetooth mit rfkill. Ausschalten stellt nur selbst blockierte Funkgeräte wieder her. Hardware- oder externe Sperren werden nicht stillschweigend aufgehoben. Aktiviere bei Bedarf ein Funkgerät einzeln.
