# Apps und Installation

Vor der Installation offizieller Pakete zeigt dir das Terminal an, dass es nach ausstehenden Systemaktualisierungen sucht. Diese Prüfung kann etwas dauern, bevor du nach deinem Administratorpasswort gefragt wirst. Auch Flatpak-Installationen zeigen ihre Vorbereitungsphase an.

**SUPER + Space** und Hauptmenü > Apps öffnen dieselbe Anwendungsliste. Enter startet eine App. Delete bietet in Apps eine bestätigte Deinstallation an. Die globale Suche über **SUPER + F** startet Apps, bietet aber keine Deinstallation. Es gibt kein separates Menü mit angehefteten Apps.

Eingaben im Hauptmenü suchen installierte Apps und Aktionen aus allen Untermenüs. In einem Untermenü wie System oder Installieren umfasst die Suche dieses und alle darunterliegenden Menüs. Untermenüzeilen enden mit **>**; **Shift + Backspace** führt zum übergeordneten Menü.

## Installieren

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

**Offline-Diktat** wandelt Sprache in Text um, ohne den Rechner zu verlassen. Halte **SUPER + D**, sprich und lass los: Der Text wird an der Cursorposition in der gesprochenen Sprache eingefügt. Beim Zuhören wird der rote Punkt neben dem Wetter zur kleinen Wellenform, die deiner Stimme folgt und die Erfassung sichtbar macht; nach dem Loslassen pulsiert sie bis zur Texteingabe. Beim ersten Einsatz wird einmalig das Sprachmodell heruntergeladen (148 MB, mit veröffentlichter Prüfsumme geprüft), nach `~/.local/share/eitr/whisper/`; danach funktioniert es offline. Die Transkription dauert nach dem Loslassen kurz, auf älteren Prozessoren länger.

**Hauptmenü > Werkzeuge > Erinnerungen > Neue Erinnerung** fragt nach Zeitpunkt (Dauer wie `10m` oder `1h30m`, Uhrzeit wie `18:30`) und Inhalt. Dann erscheint eine Benachrichtigung, die bis zum Schließen bleibt. **Kommende Erinnerungen** listet wartende Einträge; wähle einen zum Abbrechen. Sie überstehen Neustarts; bei ausgeschaltetem Rechner fällige Erinnerungen erscheinen bei der nächsten Anmeldung. Im Terminal: `eitr remind 25m Take the tea out`; `eitr remind` allein listet sie auf.

## Spielen

Hauptmenü > Spielen listet **GeForce NOW**, **RetroArch** und **Steam**. Die Auswahl öffnet installierte Programme und installiert fehlende. RetroArch stammt aus offiziellen Arch-Paketen mit Kernen für NES, SNES, Game Boy und Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo DS, PSP und Dreamcast. Füge eigene Spiele und nötige BIOS-Dateien hinzu; Eitr liefert beides nicht mit. GeForce NOW wird per Flatpak installiert.

**Umschalten > Spielmodus** reduziert Desktop-Störungen: Fensteranimationen, Unschärfe und Schatten aus, Benachrichtigungs-Popups aufgeschoben (Nicht stören), Leistungsprofil an, sofern vorhanden. Ausschalten stellt genau seine Änderungen zurück. Steam kommt mit **GameMode** und **MangoHud**: Füge `gamemoderun mangohud %command%` den Steam-Startoptionen eines Spiels hinzu, um die CPU beim Spielen zu optimieren und die FPS-Anzeige einzublenden.

LocalSends Paket enthält seine Laufzeitvoraussetzungen; zum Ausführen ist kein Flutter SDK nötig. Entwicklungswerkzeuge bleiben optional.

Für Aktualisierungen siehe [Updates und Bereinigung](handbook:maintenance); ein einzelnes Paket zu installieren ist nicht dasselbe wie die Snapshot-geschützte Systemaktualisierung.
