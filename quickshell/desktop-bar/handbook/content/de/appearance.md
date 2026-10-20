# Designs, Hintergrundbilder und Darstellung

## Designs und Hintergrundbilder

Öffne **Stil > Design** oder **SUPER + Ctrl + Shift + N**. Wähle dunkel oder hell und dann ein Design. Tippe im Designkarussell zum Filtern; Pfeiltasten oder Tab wechseln die Auswahl, Enter wendet sie an. Backspace bearbeitet zuerst die Suche; Escape leert sie vor dem Schließen. Kategorieauswahl und Hintergrundbildkarussell haben keine Designsuche.

**SUPER + Ctrl + N** öffnet die Hintergrundbilder, **SUPER + Shift + N** wechselt zum nächsten. Ein Häkchen markiert die aktive Wahl in Walker. Änderungen zeigen keine Erfolgsbenachrichtigungen. Ultrawide-Monitore, deren Breite mindestens das Doppelte der Höhe beträgt, verwenden die 21:9-Version mit weniger Beschnitt; andere verwenden 4K in 16:9.

Norse enthält gezeichnete Raben, Walküren, Odin, Fenrir und Jörmungandr auf schwarzem Hintergrund. Wähle sie über dieselben Hintergrundbild-Steuerungen; zusätzliche Bilder ändern die Palette nicht. Das erste Bild, der Runenstein, ist animiert: Polarlichter bewegen sich langsam hinter dem Runenring. Hinter Vollbildanwendungen pausieren sie; der Sperrbildschirm zeigt das Standbild.

## Leiste und Ecken

**Stil > Desktopleiste** wählt Unschärfe oder Designfarbe, vollständige oder zentrierte Anordnung und Bildschirmkante. Walker folgt dieser Darstellung. **Stil > Ecken** wählt eckige, abgerundete oder stark abgerundete Ecken für EITR-Flächen und Fensterdekorationen. Fremdanwendungen können eigene Bedienelemente behalten; runde Statuspunkte bleiben rund.

## Schriftarten

**Stil > Schriftarten** zeigt nutzbare installierte Schriftfamilien, nicht jede fette oder kursive Variante. Dokument- und Ersatzschriften bleiben verborgen. Standard ist JetBrainsMono Nerd Font. Die Auswahl aktualisiert unterstützte Anwendungen und aktiviert verfügbare Ligaturen. Das Entfernen einer Familie entfernt ihre unterstützten installierten Varianten; die letzte nutzbare Auswahl lässt sich nicht entfernen. Die Paketzugehörigkeit muss gegebenenfalls geprüft werden.

## Mauszeiger

**Stil > Mauszeiger** bietet Bibata Modern, Breeze und Vanilla DMZ. Farbe bietet automatisch, dunkel und hell; Größe bestimmt die Zeigergröße. Automatisch folgt der hellen oder dunklen Designkategorie, ohne deine gewählte Familie zu ändern. Ausdrückliche Farbvorgaben bleiben erhalten. Die ausgewählte Zeile hat links ein Häkchen; andere Familien zeigen Vorschauen. Fehlende Dateien führen zu einem Fehler statt einer ungültigen gespeicherten Auswahl.

Das Limine-Startmenü verwendet die aktuellen Designfarben, einen EITR-Titel und eine größere Schrift. Neue Installationen richten das ein; nach einem Designwechsel folgt das Menü beim nächsten Herunterfahren. Ist dein Design nicht lesbar, werden Standardfarben verwendet. Starteinträge bleiben unverändert und `limine.conf` wird vor jeder Änderung gesichert. Bei aktiviertem Secure Boot wird die Gestaltung übersprungen: Eine Änderung der Limine-Konfiguration würde bei registriertem Konfigurationshash den Start verhindern.

**Stil > Sperrbildschirm** bestimmt Sperr- und Anmeldebildschirm. Bestehende Einstellungen bleiben bei Designwechseln erhalten.

Verfügbar sind Clockwork Neo Orbital, Clockwork Tape, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing und Theme Wallpaper. Die Auswahl zeigt nur ausgelieferte Designs; Vorschauen sperren die Sitzung nicht. Ein nicht mehr ausgeliefertes Design wird durch Clockwork Tape ersetzt, den Standard neuer Installationen.

Die Bilder sind für 4K (3840×2160, 16:9) vorgesehen. Coffee und Pillow behalten ihren ruhigen Anime-Stil mit nordischer Kleidung; Material und Clockwork verwenden dezente Runenornamente. Nothing behält sein Design. QML und SVG bleiben skalierbar.

Vergleiche die acht Designs mit `bash quickshell/lockscreen/scripts/gallery.sh`. Dies ändert die Auswahl nicht; Anmeldung und Energieaktionen sind in der Galerie deaktiviert. Clockwork nutzt prozedurales QML. Coffee, Pillow, Material und Nothing behalten ihre lizenzierten Anordnungen mit neuen Bildern und installierter JetBrainsMono Nerd Font. Zusätzliche mitgelieferte Schriften oder Videos sind nicht erforderlich.

**Design-Hintergrundbild** zeigt das aktuelle Hintergrundbild mit Uhr oben links und Passworteingabe unten rechts. Die Walker-Vorschau zeigt das aktuelle Bild. Spätere Änderungen erscheinen beim nächsten Sperren oder Öffnen der Vorschau; Ctrl+P zeigt das gesamte Design ohne Sperren. Der Anmeldebildschirm kann deinen persönlichen Ordner nicht lesen. Er nutzt eine Kopie, die Eitr beim Auswählen dieses Designs und bei jedem Bildwechsel speichert. Fehlt sie, wird ein anderes Bild des aktuellen Designs oder der Norse-Standard verwendet.
