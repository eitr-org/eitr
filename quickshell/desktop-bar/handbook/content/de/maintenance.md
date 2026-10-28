# Aktualisierungen, Bereinigung und Wiederherstellung

Das Terminal zeigt dir während der Ausführung die jeweilige Prüfung und Schnappschusserstellung an. Wenn alles aktuell ist, bleibt die Meldung drei Sekunden sichtbar, bevor sich das Terminal schließt.

Warteschritte bei Systemaktualisierungen zeigen eine kreisende Rune und fließenden Bifröst-Regenbogentext auf Truecolor-Terminals, sonst die Design-Akzentfarbe, gefolgt von übersetzten nordischen Sprüchen und der Laufzeit. Erfolgreiche Schritte enden mit einem schlichten Häkchen und dem Schritttext.

Öffne **System > Instandhaltung**. Prüfe Terminalausgaben und halte vor Systemänderungen unabhängige Sicherungen bereit. Snapshots sind keine Sicherungen auf einem anderen Laufwerk.

Die Systemaktualisierung prüft zuerst offizielle Pakete mit checkupdates in einer separaten temporären Datenbank, AUR-Pakete (einschließlich Entwicklungspaketen) und Benutzer-Flatpaks. Bestätigen alle Prüfungen, dass keine Updates vorliegen, endet sie ohne Schnappschüsse, Upgrades oder Neustartabfrage. Scheitert eine Prüfung oder fehlt ein Werkzeug, läuft der normale Aktualisierungsvorgang weiter.

## Aktualisierung

**Aktualisierung > Systemaktualisierung** ist der normale Ablauf für vollständige Paketaktualisierungen. Eine konfigurierte neue EITR-Installation prüft die Snapshot-Unterstützung und erstellt Vorher-/Nachher-Snapshots mit Startdateiarchiven. Scheitert der Schutz, beginnt keine Aktualisierung. Ein vorhandener Arch-Desktop ohne Distributionsrichtlinie benötigt diese Einrichtung nicht allein zum Aktualisieren. Die Systemaktualisierung aktualisiert auch Flatpak-Anwendungen wie GeForce NOW. Ein Flatpak-Fehler wird gemeldet, ohne die Systemaktualisierung zurückzunehmen.

Vor der Aktualisierung prüfen die Systemaktualisierung und Terminalaktualisierungen offizieller Pakete die Arch-Linux-Nachrichten seit der letzten Aktualisierung. Dort kündigt Arch Änderungen mit manuellen Schritten an. Gibt es Nachrichten, erscheinen Titel, Links und **Aktualisierung fortsetzen? [y/N]**. Enter bricht vor jeder Änderung ab, damit du zuerst den Beitrag lesen kannst. Ohne Nachrichten oder Internet wird fortgefahren.

**Aktualisierung > Update-Kanal** zeigt beide Kanäle und markiert den aktuellen. Ein anderer Kanal wird nach Passwortabfrage im Terminal ausgewählt; er bestimmt die Herkunft von Eitrs eigenen Aktualisierungen. Stable ist der Standard und erhält erprobte Versionen. Testing erhält neue Builds sofort nach Veröffentlichung, um Änderungen früh auszuprobieren. Alles andere kommt weiterhin von Arch. Beim Wechsel zurück zu Stable bleibt eine neuere Eitr-Version erhalten, bis Stable aufholt. Im Terminal zeigt `eitr channel` den Kanal; `eitr channel testing` oder `eitr channel stable` wechselt ihn.

Verhindert eine Aktualisierung den Systemstart, nimmt der **Startschutz** sie zurück. Erreichen zwei aufeinanderfolgende Starts den Anmeldebildschirm nicht, stellt der nächste das System samt Startdateien von vor der Aktualisierung wieder her und startet neu. Dein persönlicher Ordner bleibt unverändert; bei der nächsten Anmeldung erfährst du, was geschehen ist. Das gilt für Rechner mit Eitr-Installation über den Installer. Einzelheiten unter [Wiederherstellung und Snapshots](handbook:recovery).

**Snapshots des persönlichen Ordners** behalten ältere Dateiversionen. Aktiviere sie unter **System > Instandhaltung > Momentaufnahmen > Snapshots des persönlichen Ordners**. Sie werden stündlich für einen Tag und täglich für eine Woche erstellt; bei Platzmangel werden die ältesten entfernt. Caches, Downloads, VM-Laufwerke und Spiele sind ausgeschlossen. Wähle **Wiederherstellen einer Datei oder eines Ordners**, gib den Pfad ein und wähle einen Zeitpunkt. Die alte Version erscheint neben der aktuellen; nichts wird ersetzt.

Die Systemaktualisierung umfasst offizielle Pakete, AUR und Flatpak mit Snapshots auf unterstützten Distributionsinstallationen. In seltenen Fällen, etwa um bei einem fehlgeschlagenen AUR-Build nur offizielle Pakete zu aktualisieren oder den Snapshot auszulassen, nutze ein Terminal: `eitr update pacman`, `eitr update aur` oder `eitr update full` (keine automatischen Snapshots), oder direkt `sudo pacman -Syu` / `yay -Sua`. Flatpaks, Entwicklungslaufzeitumgebungen und getrennte persönliche Daten sind nicht durch Root-Snapshots geschützt.

Vermeide Teilaktualisierungen von Arch. Lies Paketabfragen, statt eine unerwartete Entfernung ungeprüft zu bestätigen. Erfolgreiche Aufgaben schließen sich; Fehlerausgaben bleiben zur Untersuchung sichtbar.

Nach erfolgreicher Aktualisierung fordert bei Bedarf eine Benachrichtigung zum Abschluss auf: **Jetzt neu starten** nach Kernel-, Firmware-, Mikrocode-, systemd-, glibc-, Grafiktreiber- oder Laufwerksverschlüsselungs-Aktualisierungen. **Jetzt abmelden** gilt nach Desktop-Aktualisierungen wie EITR, Hyprland, Quickshell, Walker oder PipeWire. Mit **Später** arbeitest du weiter; die neuen Versionen werden beim nächsten Neustart oder Anmelden verwendet.

## Bereinigung und Snapshots

Die Bereinigung führt die Wartung aus und lässt den Bericht zum Lesen offen. Prüfe die Vorschläge; nicht jedes verwaiste Paket ist ungenutzt. Snapshots bietet die vorhandenen Snapper-Status- und Einrichtungsabläufe. Unterstützte Anordnungen und Bootloader-Grenzen stehen unter [Wiederherstellung und Snapshots](handbook:recovery).

## Werkseinstellungen

Nur eine unterstützte Distributionsinstallation mit Wiederherstellungspunkt der ersten Anmeldung kann zurückgesetzt werden. Diese vertrauliche Ausgangskopie liegt getrennt von gewöhnlichen Snapper-Listen und der Bereinigung. Root kann sie löschen und ein Laufwerksausfall kann sie zerstören. Zwei getrennte Warnungen und eine eingetippte Bestätigung sind erforderlich. [Werkseinstellungen](handbook:factory-reset) erklärt genau, was Alles löschen und Eigene Dateien behalten erhalten.

## Energie

Hauptmenü > Energie und Kontrollzentrum > Allgemein (hinter **Ein/Aus…**) bieten Sperren, Abmelden, Bereitschaft, Neustart und Ausschalten. Speichere vorher deine Arbeit. Die Aktionen werden tatsächlich ausgeführt; sie sind keine Vorführungen.

## Paketspiegel

Unter System > Wartung wähle Schnellste Spiegel auswählen. Das Terminal erklärt die Änderung; Enter bestätigt und Esc bricht ab. Reflector wählt bis zu zehn HTTPS-Spiegel aus, die innerhalb von 12 Stunden synchronisiert wurden, und sortiert sie nach Downloadgeschwindigkeit. Wenn bekannt, bevorzugt es das durch die Systemzeitzone bestimmte Land und versucht bei zu wenigen Treffern weltweite Spiegel. Die drei mitgelieferten weltweiten Server bleiben immer am Ende; schlägt die Bewertung fehl, bleibt die Liste unverändert, auch eigene Spiegel. Jeder reflector-Aufruf ist auf zwei Minuten begrenzt.

Die vorherige Liste wird neben `/etc/pacman.d/mirrorlist` als `mirrorlist.eitr-<timestamp>.bak` gesichert. Falls eine Sicherung existiert, bietet derselbe Ablauf die Wiederherstellung an: `restore` eingeben und Enter drücken. Auch beim Wiederherstellen wird die aktuelle Liste gesichert. Das Ergebnis bleibt bis Esc sichtbar.

Neue Installationen planen zwei Minuten nach jedem Start einen Hintergrundversuch, bis zu drei Versuche mit Verbindung. Starts ohne Verbindung werden still übersprungen und zählen nicht; eine erfolgreiche Bewertung beendet weitere Versuche. Die Anmeldung wartet nie darauf. Wenn alle Versuche scheitern, nutze später das Menü. Nur Arch-Paketspiegel ändern sich; Eitr- und Flatpak-Quellen bleiben gleich.

Nur lesender Status: `/usr/lib/eitr/eitr-system mirrors-status` gibt JSON mit `last_ranking_time` (UTC oder null vor dem ersten Erfolg), `mirror_count`, `shipped_fallback` und `backup_available` aus. Dabei werden lokale Dateien ohne Netzwerkzugriff oder sudo gelesen.

Die Systemaktualisierung prüft am Ende auf neue Plugin-Commits, ohne bestätigte Versionen zu ändern. Prüfe und installiere sie separat unter **Kontrollzentrum > Plugins > Plugins aktualisieren**, **Installieren > Plugins > Plugins aktualisieren** oder mit `eitr plugin update`. Netzwerkfehler werden still ignoriert; after-update-Hooks bleiben unverändert.
