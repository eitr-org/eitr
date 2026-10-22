# Apps und Installation

Vor der Installation offizieller Pakete zeigt dir das Terminal an, dass es nach ausstehenden Systemaktualisierungen sucht. Diese Prüfung kann etwas dauern, bevor du nach deinem Administratorpasswort gefragt wirst. Auch Flatpak-Installationen zeigen ihre Vorbereitungsphase an.

**SUPER + Space** und Hauptmenü > Apps öffnen dieselbe Anwendungsliste. Enter startet eine App. Delete bietet in Apps eine bestätigte Deinstallation an. Die globale Suche über **SUPER + F** startet Apps, bietet aber keine Deinstallation. Es gibt kein separates Menü mit angehefteten Apps.

Eingaben im Hauptmenü suchen installierte Apps und Aktionen aus allen Untermenüs. In einem Untermenü wie System oder Installieren umfasst die Suche dieses und alle darunterliegenden Menüs. Untermenüzeilen enden mit **>**; **Shift + Backspace** führt zum übergeordneten Menü.

## Installieren

Drücke Delete bei einem installierten Eintrag in den Anwendungs- und Werkzeuglisten unter Installieren, um ihn nach einer Bestätigung zu deinstallieren. Web-Apps behalten ihre Aktion zum Entfernen. Pakete (Pacman und Yay) dienen weiterhin nur zur Installation und haben keine Delete-Aktion. Erforderliche Systemabhängigkeiten werden nie rekursiv entfernt. pacman verweigert das Entfernen, wenn dadurch ein anderes Paket beschädigt würde.

Bei verwalteten Sprachpaketen siehst du zunächst die vollständige Warnung im Terminal. Danach bestätigst du mit [y/N]; Enter bricht ab. Bei Node werden alle von NVM verwalteten Versionen und ihre globalen npm-Werkzeuge entfernt. Bei Python betrifft dies die von uv verwalteten Versionen und uv selbst, nicht System-Python. Bei Java werden die aktuellen SDKMAN-Versionen von Java und Maven entfernt, bei Rust nur die stabile Toolchain. Rails und Laravel entfernen ihre Framework-Werkzeuge; Ruby, PHP und Composer bleiben erhalten. Projekte, Einstellungen und Zugangsdaten bleiben erhalten, aber abhängige Werkzeuge und Umgebungen funktionieren danach möglicherweise nicht mehr. Beim Entfernen nativer Assistenten bleiben zwischengespeicherte Versionen und Einstellungen erhalten.


Vorhandene Apps zeigen **Installiert** unter ihrem Namen; die Auswahl meldet dies, statt erneut zu installieren. Auch über eigene Manager installierte Werkzeuge werden erkannt, etwa Java aus SDKMAN oder Node.js aus NVM. Pakete mit Laufzeitbedarf, beispielsweise DBeavers Java, bringen eine kleine Laufzeit nur mit, wenn noch kein Paket sie bereitstellt.

- **KI-CLIs:** optionale KI-Kommandozeilenprogramme.
- **Browser:** unterstützte Browserauswahl.
- **Datenbanken:** optionale Werkzeuge wie DBeaver, Datenbankclients und Valkey, der Redis-kompatible Server, den Arch statt Redis ausliefert.
- **Entwicklungssprachen:** optionale Entwicklungswerkzeuge; Java/Flutter sind keine erforderlichen Desktop-Abhängigkeiten.
- **JavaScript-Werkzeuge:** optionale JavaScript-Laufzeiten und Werkzeuge.
- **Pakete > Pacman** und **Pakete > Yay (AUR):** offizielle Arch-Pakete oder Community-AUR-Pakete suchen, jeweils mit Herkunft und Installationsstatus. Oben steht die Suche, darunter die Pakete und unten die Auswahldetails. **Ctrl+B** wechselt zur Bauanweisung (PKGBUILD) und zurück, **Ctrl+O** öffnet die Webseite, **Tab** wählt mehrere Pakete und **Enter** installiert sie. AUR-Pakete werden auf diesem Rechner nach ihrer Bauanweisung erstellt: Lies diese zuerst. Es sind keine offiziellen Arch-Pakete.

Installations-, Aktualisierungs- und Einrichtungsterminals zeigen das EITR-Banner im aktuellen Design. Erfolgreiche Aufgaben schließen normalerweise; Fehler bleiben sichtbar. Berichte wie Bereinigung bleiben zum Lesen offen. Normale Terminals und Über zeigen kein Aufgabenbanner.

Drücke **Esc**, um wartende Aufgaben-, Konto-, Berichts- und Über-Terminals zu schließen. Enter bleibt für Antworten und Bestätigungen vorgesehen, etwa zum Bestätigen der notierten Wiederherstellungsschlüssel und zum Ausschalten im Installationsprogramm.

## Werkzeuge

**Rechner** in Apps oder die Rechnertaste öffnet Eitrs Rechner in den Designfarben. Tippe oder klicke: `+ − × ÷`, `^` für Potenzen, `%` für Prozent (`200×15%`), `√` und Klammern. Eine Zahl vor einer Klammer multipliziert (`2(3+4)`). Enter zeigt das Ergebnis, Backspace entfernt ein Zeichen, Escape leert (zweimal schließt), Ctrl+C oder **Kopieren** kopiert das Ergebnis. Ausdrücke werden berechnet, nicht als Code ausgeführt.

**Offline-Diktat** wandelt Sprache in Text um, ohne den Rechner zu verlassen. Halte **SUPER + D**, sprich und lass los: Der Text wird an der Cursorposition in der gesprochenen Sprache eingefügt. Beim Zuhören wird der rote Punkt links neben der Uhr zur kleinen Wellenform, die deiner Stimme folgt und die Erfassung sichtbar macht; nach dem Loslassen pulsiert sie bis zur Texteingabe. Beim ersten Einsatz wird einmalig das Sprachmodell heruntergeladen (148 MB, mit veröffentlichter Prüfsumme geprüft), nach `~/.local/share/eitr/whisper/`; danach funktioniert es offline. Die Transkription dauert nach dem Loslassen kurz, auf älteren Prozessoren länger. Die Aufnahme endet beim Loslassen von D, auch wenn SUPER zuerst losgelassen wurde, oder nach 120 Sekunden; anschließend wird der Text wie gewohnt transkribiert.

**Hauptmenü > Werkzeuge > Erinnerungen > Neue Erinnerung** fragt nach Zeitpunkt (Dauer wie `10m` oder `1h30m`, Uhrzeit wie `18:30`) und Inhalt. Dann erscheint eine Benachrichtigung, die bis zum Schließen bleibt. **Kommende Erinnerungen** listet wartende Einträge; wähle einen zum Abbrechen. Sie überstehen Neustarts; bei ausgeschaltetem Rechner fällige Erinnerungen erscheinen bei der nächsten Anmeldung. Im Terminal: `eitr remind 25m Take the tea out`; `eitr remind` allein listet sie auf.

## Spielen

Hauptmenü > Spielen listet **GeForce NOW**, **RetroArch** und **Steam**. Die Auswahl öffnet installierte Programme und installiert fehlende. RetroArch stammt aus offiziellen Arch-Paketen mit Kernen für NES, SNES, Game Boy und Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP und Dreamcast. Füge eigene Spiele und nötige BIOS-Dateien hinzu; Eitr liefert beides nicht mit. GeForce NOW wird per Flatpak installiert.

**Umschalten > Spielmodus** reduziert Desktop-Störungen: Fensteranimationen, Unschärfe und Schatten aus, Benachrichtigungs-Popups aufgeschoben (Nicht stören), Leistungsprofil an, sofern vorhanden. Ausschalten stellt genau seine Änderungen zurück. Steam kommt mit **GameMode** und **MangoHud**: Füge `gamemoderun mangohud %command%` den Steam-Startoptionen eines Spiels hinzu, um die CPU beim Spielen zu optimieren und die FPS-Anzeige einzublenden.

LocalSends Paket enthält seine Laufzeitvoraussetzungen; zum Ausführen ist kein Flutter SDK nötig. Entwicklungswerkzeuge bleiben optional.

Für Aktualisierungen siehe [Updates und Bereinigung](handbook:maintenance); ein einzelnes Paket zu installieren ist nicht dasselbe wie die Snapshot-geschützte Systemaktualisierung.

**Musikvisualisierer** unter **Hauptmenü > Werkzeuge** öffnet cava in den Theme-Farben. Ein Rechtsklick auf den Medien-Equalizer öffnet denselben Visualisierer; ein Linksklick öffnet weiterhin die Mediendetails. **q** oder **Esc** schließt ihn. Auf bestehenden Desktops wird cava bei Bedarf zuerst installiert.

## Erinnerungen per Sprache

Halte **SUPER + Shift + D**, sprich und lasse los, oder tippe unter Hauptmenü > Werkzeuge > Erinnerungen > Dem Assistenten etwas sagen…. Eitr transkribiert lokal mit dem Offline-Modell der Diktierfunktion und fragt den unter Entwicklung > Standardassistent gewählten Assistenten. Nur Transkript und Erinnerungskontext gehen an dessen Anbieter; Audio bleibt lokal und wird nach der Transkription gelöscht. Der Assistent läuft ohne Fenster über Eitrs schreibgeschützten Aufruf. Eitr prüft dessen JSON und führt Erinnerungsaktionen selbst aus; der Assistent erhält keine Werkzeuge zum Ändern von Daten.

Sage etwa „Erinnere mich morgen um 15 Uhr an einen Anruf“ oder „Zahnarzt am 30. Oktober um 15 Uhr, 30 Minuten vorher erinnern“. Termine melden sich standardmäßig eine Stunde vorher (oder mit dem gewünschten Vorlauf) und zur Terminzeit; einfache Erinnerungen nur zur angegebenen Zeit. Bei fehlenden Angaben oder Mehrdeutigkeit erscheint ein Terminal mit vollständig ausgeschriebenen nummerierten Optionen. Tippe die Nummer oder diktiere sie mit SUPER + D; Esc bricht ab. Eine Benachrichtigung meldet das Ergebnis. Auch Auflisten und Löschen sind möglich.

Neue Erinnerung akzeptiert außerdem `tomorrow 15:00`, englische Wochentage (ohne Uhrzeit 09:00), `2026-10-30 09:00` und `Oct 30 15:00`. Mehrteilige Datumsangaben in der CLI in Anführungszeichen setzen. Jeder Alarm hat einen eigenen Timer; Abbrechen entfernt alle. Verpasste Alarme erscheinen bei der nächsten Anmeldung. Der Kalender markiert Termintage; ein Klick zeigt sofort aktualisierte Zeiten und Titel. Wiederholungen und externe Kalendersynchronisierung werden noch nicht unterstützt.

## Plugins

Ein Plugin ist ein Git-Repository mit Skripten, Walker-Einträgen und optional einem Benutzerdienst. Plugins laufen mit allen Berechtigungen deines Kontos. Eitr hat ihren Code nicht geprüft: Vertraue Autor und Repository, bevor du Installierenation oder Aktualisierung bestätigst.

Hauptmenü > Installieren > Plugins > Plugin hinzufügen… fragt nach einer HTTPS-Git-URL. Die Prüfung zeigt Manifest-Autor, Repository, genauen Commit, Git-Autor und Datum, Einträge und Hintergrunddienst. Scrolle durch die Prüfung und drücke `y` zum Installierenieren; Enter oder Esc bricht ab. Vor der Bestätigung läuft kein Plugin-Code. Hauptmenü > Werkzeuge > Plugins zeigt die Aktionen; die Suche in Werkzeuge findet sie ebenfalls. Das leere Menü zeigt Keine Plugins installiert.

Systemaktualisierung prüft Plugins auch ohne Paketaktualisierungen. Jede Aktualisierung zeigt alten und neuen Commit, Commit-Betreffzeilen und geänderte Dateien und fragt mit `[y/N]`; Enter lehnt ab. Nicht interaktive Aktualisierungen überspringen Plugins. Installieren > Plugins > das Plugin bietet Aktualisierung und Entfernen; Entfernen fragt nach Bestätigung und löscht Dateien, Einträge und Dienst. Dieselben Abläufe bieten `eitr plugin list`, `eitr plugin add URL`, `eitr plugin update [ID]` und `eitr plugin remove ID`.

Plugins liegen nur unter `$XDG_DATA_HOME/eitr/plugins/<id>/` (Standard `~/.local/share/eitr/plugins/`); Bestätigungen unter `$XDG_STATE_HOME/eitr/plugins.json`. Dienste verwenden `$XDG_CONFIG_HOME/systemd/user/eitr-plugin-<id>.service`. Verwende nie sudo. Aktualisierungen prüfen einen separaten Kandidaten und behalten bei Ablehnung oder Fehlern den bestätigten Commit. Ein Plugin kann deine Dateien verändern; Entfernen macht diese Änderungen nicht rückgängig.

### Manifest-Referenz

Im Stamm liegt `eitr-plugin.json`. Nur diese Schlüssel sind erlaubt: `id` (Kleinbuchstaben und Ziffern, getrennt durch einzelne Bindestriche), `name`, `description` (höchstens 72 Zeichen), `author`, `version`, `rows` (1–20) und optional `service`. Jeder Eintrag benötigt `title`, `description` (beide höchstens 72 Zeichen) und `run`; optional sind `icon` und `arguments` (Liste fester Zeichenketten). Ein Dienst akzeptiert nur `run` und optional `arguments`. Befehle verwenden argv, niemals Shell-Zeichenketten. `run` muss eine ausführbare Datei im Repository bezeichnen: Absolute Pfade, `..` und hinausführende Symlinks werden abgelehnt. Unbekannte oder doppelte JSON-Schlüssel werden abgelehnt. Submodule werden nicht initialisiert.

Das Beispiel unter `distro/plugins/example/` enthält Manifest und `notify.sh`, eine Benachrichtigungsaktion und keinen Dienst. Kopiere es in dein Git-Repository, erstelle einen Commit und veröffentliche eine HTTPS-Git-URL, um den gesamten Installierenationsablauf zu testen. Es wird als Dokumentation geliefert und nicht automatisch installiert.
