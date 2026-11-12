# Fernzugriff

Öffnen Sie Einstellungen > Streaming für Sunshine und Moonlight oder Walker > Einstellungen > Geräte > Streaming für dieselben Aktionen. Die Freigabe bleibt bis zur
Aktivierung ausgeschaltet. Unterstützt wird der angemeldete, wache Eitr-Desktop.
Betrieb ohne Monitor, Zugriff vor der Anmeldung und wake on LAN folgen später.
Sperrt sich dieser PC während der Freigabe, zeigt der entfernte Bildschirm den
Sperrbildschirm; wer verbunden ist, sieht ihn und kann das Passwort eingeben.
Beenden Sie die Freigabe, bevor Sie weggehen, wenn Vertraulichkeit wichtig ist.

Einrichtungsordner bündeln die Konfiguration. Unter Streaming > Freigabe-Einrichtung stehen Freigabe einrichten, Freigabeeinstellungen, Beim Anmelden starten, Start beim Anmelden ausschalten, Detaillierter Status und Freigabeeinrichtung wiederherstellen. Tägliche Freigabeaktionen (Freigabe starten, Freigabe beenden, Gerät koppeln, Freigabestatus und Mit anderem PC verbinden) bleiben direkt in Streaming.

Detaillierter Status öffnet ein Diagnoseterminal, das bis zum Drücken von Esc geöffnet bleibt.

## Sunshine auf Eitr

Wählen Sie unter Diesen PC freigeben den Eintrag Freigabe einrichten. Der Release-Verantwortliche
baut das signierte native Eitr-Paket aus den offiziellen Quellen. Beim ersten Klick
wird kein AUR-Paket gebaut. Flatpak und AppImage bieten keine KMS-Aufnahme.
Einstellungen und gekoppelte Geräte bleiben erhalten. Starten Sie keine zweite Instanz.

Lesen Sie die Warnung zur vollständigen Kontrolle. Geben Sie `yes` nur ein, wenn
Sie KMS-Aufnahme und virtuelle Tastatur-, Maus- und Controller-Eingaben erlauben. Der ursprüngliche Zustand wird unter `/var/lib/eitr/remote-access` gespeichert. Die Einrichtung ergänzt eine udev-Regel für uinput, lädt uinput beim Start, gewährt
Ihrem Benutzer Gerätezugriff und setzt `cap_sys_admin+p` für Sunshine. Freigabeeinrichtung zurücksetzen stellt Dateien und Geräte-ACL wieder her und entfernt die Aufnahmeberechtigungen.

Wurde uinput bei der Einrichtung geladen, wird es beim Zurücksetzen entladen. Verwendet es eine andere Anwendung noch, wird der Fehler gemeldet und das Protokoll
bleibt erhalten. Schließen Sie die Anwendung und versuchen Sie es erneut.

Freigabe starten fragt nach und öffnet `https://localhost:47990`. Akzeptieren Sie das
lokale selbstsignierte Zertifikat nur dort. Legen Sie vor dem Koppeln Benutzername
und ein starkes Passwort fest. Einstellungen öffnen öffnet die Einstellungen; Gerät koppeln
die PIN-Seite. Geben Sie nur die PIN Ihres eigenen Moonlight-Geräts ein.
Eitr erzwingt `upnp=off`. Richten Sie keine Portweiterleitung am Router ein.

TCP 47984, 47989 und 48010 sowie UDP 47998-48000 sind nur aus direkt verbundenen
privaten LAN-Subnetzen zugänglich. TCP 47990 bleibt auf diesen
PC beschränkt, auch wenn andere Regeln Zugriff erlauben. LAN-Bereiche werden bei
jedem Start ermittelt; starten Sie die Freigabe nach einem Netzwechsel neu. Verwenden Sie nur ein vertrautes Heimnetz.

Freigabe beenden deaktiviert den Autostart
und schließt die Ports samt bestehenden Streams. Auch Dienstfehler schließen sie;
die Öffnungen überstehen keinen Neustart. Nach dem ersten Start schalten Freigabe starten und Freigabe beenden sofort, ohne Fragen
oder Passwort. Bei Anmeldung starten ist optional und schaltet sofort
im Streaming-Panel oder im Menü um.

Anmeldestart deaktivieren behält manuelles Starten bei. Freigabestatus zeigt Dienstfehler.

Beim ersten Mal bleibt Streaming während der Passwortvergabe gesperrt. Kehren Sie zum Terminal zurück und bestätigen Sie die Vergabe; Ihr Administratorpasswort erlaubt dann die Fernkontrolle.

Ein Sunshine-Paketupdate ersetzt die ausführbare Datei und entfernt damit ihre
Aufnahme-Capability; das Update gibt sie dem Konto, das die Freigabe eingerichtet hat,
anschließend zurück. Startet die Freigabe trotzdem nicht, nennt der Streaming-Schalter
den Grund: Freigabe erneut einrichten oder nach der ersten Einrichtung ab- und wieder
anmelden. Das ursprüngliche Wiederherstellungsprotokoll bleibt erhalten.

Sunshine verwendet die KMS-Capability nur als root oder mit dem Freigabekonto: Die Einrichtung setzt `root:eitr-sharing`, Modus `0750`, und nimmt dein Konto in diese Systemgruppe auf. Melde dich vor dem Start ab und wieder an, damit der Benutzerdienst die neue Gruppe erhält. Die Einrichtung lässt laufende Prozesse aktiv; ein Neustart vor der nächsten Anmeldung kann fehlschlagen. Stoppen behält die Berechtigungen. Zurücksetzen entfernt die Gruppenmitgliedschaft und alle Datei-Capabilities und setzt `root:root`, Modus `0755`, auch bei älteren Einrichtungsdaten. Nach Paketupdates repariert die Einrichtung Eigentümer und Modus vor der erneuten Vergabe der Capability.

## Moonlight auf einem Mac

Installieren Sie [Moonlight](https://moonlight-stream.org/). Verwenden Sie beim
ersten Test dasselbe Heimnetz. Fügen Sie bei Bedarf Eitrs LAN-Adresse manuell hinzu.
Wählen Sie den PC, lesen Sie die PIN und öffnen Sie Gerät koppeln auf Eitr.
Desktop ermöglicht die Steuerung von Anwendungen und Spielen. Wählen Sie den
Bildschirm in Sunshine und prüfen Sie beide Monitore. Gaming > Moonlight und
Mit anderem PC verbinden installieren oder öffnen den Eitr-Client für die umgekehrte
Richtung. Neue Installationen enthalten diese Anwendungen; die Freigabe bleibt deaktiviert, bis du sie ausdrücklich aktivierst.

SUPER-Tastenkürzel vom Mac: Schalte in den Moonlight-Einstellungen **Capture system keyboard shortcuts** ein (im Vollbild oder immer). Erst dann sendet Moonlight die Befehlstaste des Macs als SUPER; sonst bleiben Befehlstasten-Kürzel auf dem Mac. Strg+Alt+Umschalt+K schaltet das Abfangen während einer Sitzung ein oder aus.

## Was geprüft wurde

Automatische Tests verwenden Simulationen. Auf einem echten Desktop (mit einem,
dann zwei Monitoren) und einem MacBook mit Moonlight geprüft: Einrichtung, Freigabe
starten, Kopplung über die Adresse, Bild, Tastatur, Maus, Audio, der Sperrbildschirm
(vom Mac aus entsperrt), Start bei der Anmeldung, Freigabe beenden und
Freigabe-Einrichtung wiederherstellen im Heimnetz und von unterwegs über ein VPN. Controller, andere Grafikkarten und andere
Clients wurden nicht geprüft.

Streaming steht unter Geräte neben Verbindungen. Sunshine zeigt Freigabestatus, Einrichtung, Start/Stopp, Start bei Anmeldung, Kopplung, Einstellungen, Diagnose und Wiederherstellung. Moonlight zeigt den Installationsstatus und eine Schaltfläche zum Installieren/Öffnen.
