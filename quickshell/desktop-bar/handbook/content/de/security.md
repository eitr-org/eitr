# Sicherheit und Sperren

**SUPER + M** sperrt den Bildschirm sofort. Ein Klick auf das Symbol der automatischen Sperre links in der Leiste (nach KI-Nutzung) schaltet die Sperre bei Inaktivität ein oder aus; der Tooltip zeigt den Zustand. Ist sie an, sperrt der Bildschirm nach 15 Minuten Inaktivität, schaltet sich nach 30 ab, und der Computer geht nach 60 in Bereitschaft. Das Kontrollzentrum bietet denselben Schalter und eine Sperren-Schaltfläche.

Zwanzig Sekunden vor dem Sperren werden unterstützte Bildschirme auf etwa 30 % ihrer bisherigen Helligkeit gedimmt (nie auf null). Aktivität stellt den exakten vorherigen Wert wieder her, auch nach dem Sperren; ebenso das Ausschalten der automatischen Sperre. Externe Monitore ohne DDC-Helligkeitssteuerung werden übersprungen.

## Passwort und alternative Authentifizierung

**System > Sicherheit > Passwort ändern** ändert dein Kontopasswort. Fingerabdruck und FIDO2 haben eigene Abläufe zur Registrierung und Aktivierung. Ein FIDO2-Sicherheitsschlüssel ist ein physisches Sicherheitsgerät, kein Fingerabdruckleser im Laptop. Registriere das Gerät zuerst und aktiviere dann die Authentifizierung. Das Hilfsprogramm sichert die PAM-Einstellungen; halte ein funktionierendes Passwort und einen Zugang zu einem TTY bereit.

Zurück zur Passwortauthentifizierung stellt die Anmeldung ausschließlich per Passwort wieder her. Diese Änderungen betreffen die unterstützten PAM-Dienste für Sperrbildschirm, Anmeldung und sudo. Sie setzen geeignete Hardware und installierte Hilfsprogramme voraus. Die Fingerabdruckauthentifizierung kann die Passwortabfrage kurz verzögern. Das Lesen dieser Seite ändert PAM nicht.

## Firewall

Neue Installationen starten mit eingeschalteter Firewall. Sie weist eingehende Verbindungen ab, außer Antworten auf Verbindungen, die dein Rechner gestartet hat, lokale Namenssuche und Verbindungen der von Eitr installierten Freigabeprogramme: KDE Connect (Ports 1714-1764) und LocalSend (53317). Virtuelle Maschinen und Container auf deinem Rechner können ihn weiterhin erreichen. Ausgehender Datenverkehr wird nie gefiltert. Ist SSH aktiviert, bleibt es ebenfalls erreichbar.

**System > Sicherheit > Firewall** zeigt den Zustand an und ändert ihn nach deiner Bestätigung. Rechner, die vor Einführung der Firewall eingerichtet wurden, starten mit ausgeschalteter Firewall. Damit ein weiteres Programm Verbindungen annehmen kann, füge eine Datei unter `/etc/eitr/firewall.d/` hinzu, zum Beispiel `game.nft` mit folgendem Inhalt:

```
add rule inet eitr_firewall input udp dport 27015 accept
```

Schalte die Firewall danach aus und wieder ein.

## Festplattenverschlüsselung und TPM

Die Laufwerksverschlüsselung ist eine Auswahl bei der Installation. TPM-Laufwerksentsperrung kann einem vorhandenen, unterstützten LUKS2-Root-Laufwerk einen TPM2-Slot hinzufügen; die Installation richtet ihn nicht automatisch ein. Bewahre die Passphrase und einen Wiederherstellungsschlüssel offline auf, niemals in Screenshots oder Repository-Dateien. Änderungen an Firmware oder Secure Boot können beim nächsten Start die Passphrase erforderlich machen.

Lies [Wiederherstellung und Snapshots](handbook:recovery), bevor du Authentifizierung oder TPM-Einrichtung änderst. [Secure Boot](handbook:secure-boot) ist ein fortgeschrittenes, manuelles Verfahren: EITR registriert keine Firmware-Schlüssel und signiert keine Startdateien für dich. Ein Fehler kann den Systemstart und auf manchen Geräten sogar den Zugang zu den Firmware-Einstellungen verhindern.

## Benutzerkonten

**System > Sicherheit > Benutzer > Benutzer erstellen…** erstellt eine eigene Anmeldung. Gib Benutzername, optionalen vollständigen Namen, Kontotyp und Passwort ein, prüfe die Angaben und drücke Enter zum Erstellen. Esc bricht vor dem Anwenden ab. Standardkonten können sudo nicht verwenden; Administratorkonten treten wheel bei und erhalten eine passwortgeschützte sudo-Regel. Vorhandene Benutzerkonten (UID 1000–65533) erscheinen darunter in Benutzer als schreibgeschützte Zeilen.

Das neue Home enthält keine Dateien deines Kontos. Bei der ersten Hyprland-Anmeldung über UWSM führt Eitr die benutzerspezifische Desktop-Einrichtung des Installers aus und übernimmt das Paketlayout unter der Identität des neuen Benutzers. Die Shell-Einrichtung kann Internetzugang benötigen. Nach einem Fehler bleibt die Markierung für die nächste Anmeldung erhalten; nach Erfolg läuft die Einrichtung nicht erneut. Fehler beim Erstellen lassen ein unvollständiges Konto für die manuelle Prüfung gesperrt und abgelaufen zurück. Das Löschen von Benutzern wird nicht angeboten.
