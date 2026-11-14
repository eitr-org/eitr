# Designs, Hintergrundbilder und Darstellung

Einstellungen (**SUPER + ,**) enthält Darstellungsoptionen; **Weitere Themes** öffnet den separaten Eitr Store (**SUPER + F2**).

## Fensterlayout

Wähle **Kacheln** (Standard, Hyprland dwindle) oder **Scrollen** unter **Einstellungen > Fenster > Fensterlayout** oder **Walker > Einstellungen > Desktop > Fenster > Fensterlayout**. Scrollen ordnet Fenster in Spalten auf einem beweglichen Band an. Die Auswahl wird lokal gespeichert und bleibt bei Themenwechseln, Konfigurationsneuladen und Neustarts erhalten. Änderungen laden die Compositor-Konfiguration ohne Sitzungsneustart neu.

Scrollen zeigt Richtung (Rechts, Links, Unten, Oben), Standard-Spaltenbreite (Ein Drittel, Hälfte, Zwei Drittel, Voll) und Fokusanpassung. Zentrieren zentriert die fokussierte Spalte; Einpassen bringt sie mit möglichst wenig Bewegung ins Blickfeld. Fokus folgen erlaubt dem Band, Fokuswechseln einschließlich Klicks zu folgen. Vollbild bei einer Spalte lässt eine einzelne Spalte den Bildschirm füllen, ohne die Anwendung in den Vollbildmodus zu versetzen. Standard: Rechts, Hälfte, Einpassen und beide Schalter an. Die Optionen bleiben beim Wechsel zu Kacheln gespeichert. Walkers Fensterlayout-Menü bietet jede dieser Optionen als Untermenü.

Nur bei Scrollen: **SUPER + ALT + Pfeiltasten** fokussiert Fenster; **SUPER + ALT + SHIFT + Links/Rechts** tauscht Spalten; **SUPER + ALT + Equal/Minus** wechselt die Spaltenbreite zwischen einem Drittel, der Hälfte, zwei Dritteln und voller Breite. Der Wechsel verändert die fokussierte Spalte; Standard-Spaltenbreite gilt für neue Spalten. Siehe [Tastaturreferenz](handbook:shortcuts).


## Eitr Store

Öffne Eitr Store im App-Starter, mit SUPER + F2, im Desktop-Menü von Walker oder über Weitere Themes in den Einstellungen. Das eigene verschiebbare Fenster nutzt die Einstellungspalette und den Kopf EITR / STORE. Schließen und Escape verwerfen vorübergehende Auswahlen und Prüfungen.

Wähle Entdecken oder Installiert in der Seitenleiste und danach Designs, Plugins, Sperrbildschirme oder Hintergrundbilder als Registerkarte. Strg+1–4 wechselt die Kategorie. Der letzte Bereich und die Kategorie werden auf diesem PC gespeichert. Aktualisierungen erscheint nur bei verfügbaren Updates, zeigt alle Kategorien und bietet Alle aktualisieren; jedes Plugin muss weiterhin einzeln geprüft werden. Die Suche bleibt im gewählten Bereich und der Kategorie (alle ausstehenden Updates unter Aktualisierungen). Der Filter gruppiert Quelle (Alle / Offiziell / Community) und Kategorieoptionen: Darstellung für Designs und Fügt hinzu für Plugins. Alle gewählten Funktionen müssen vorhanden sein: Leistenelement, Widget, Kontrollzentrum-Kachel, Panel, Walker-Einträge, Hintergrunddienst oder Paketinstallation. Unbekannte Metadaten zählen nicht als Treffer. Ein Punkt markiert aktive Filter. Escape oder Löschen leert die Suche. Auf/Ab wählt den Bereich; Rechts oder Tab öffnet das Raster; Links in der ersten Spalte kehrt zurück. Strg+F fokussiert die Suche.

Ein Klick verwendet installierte Themes, Sperrbildschirme und Bilder. Entdecken-Karten öffnen Details und Quellen. Themes und Bildpakete werden erst nach Prüfung und Bestätigung installiert. Alle aktualisieren aktualisiert Themes nacheinander und prüft jedes Plugin einzeln. Entfernen erfordert eine Bestätigung; aktuelle Themes und Sperrbildschirme bleiben geschützt.

Plugins besitzen die vollen Rechte deines Kontos. Vor Installation und Updates zeigt die Prüfung Quelle, festen Commit, Autor, Dateien, Befehle, Pakete und Warnungen. Prüfe den Code und optional die KI-Hinweise. Community-Commits sind im Index festgelegt. Prüfungen verfallen nach 15 Minuten und beim Schließen. Installiert > Hinzufügen akzeptiert HTTPS- und SSH-Git-Adressen für Themes und Plugins. Plugin-Karten öffnen Einstellungen, Aktivierung, Updates und Entfernen; ungenutzte Plugin-Pakete können optional entfernt werden.

Sperrbildschirme bleiben offizielle signierte Pakete. Installation und Entfernen verlangen das Administratorpasswort. Eitr ist eingebaut; verwendete Sitzungs- und Anmeldedesigns lassen sich nicht entfernen. Eigene Sperrbildschirme bleiben gespeichert und erscheinen nach erneuter Installation wieder.

Hintergrundbilder zeigt mitgelieferte und eigene Bilder sowie Paketkarten. Ein Paket verwendet beim Anklicken sein erstes Bild; einzelne Bilder sind ebenfalls verfügbar. Community-Pakete enthalten nur geprüfte JPEG-, PNG- oder WebP-Bilder. Sie erscheinen im vorhandenen Bildwähler und Karussell; Entfernen löscht nur Paketdateien. Bildschirmschoner sind nicht enthalten.


Theme-Repository: `eitr-org/eitr-themes`.

Wähle ein anderes Hintergrundbild, bevor du ein Paket einer gespeicherten Auswahl entfernst.

## Design und Hintergrundbild wählen

Wähle Design und Hintergrundbild unter Einstellungen > Erscheinungsbild > Design und Hintergrundbild. Walkers Dunkel/Hell-Menüs öffnest du mit **Walker > Einstellungen > Desktop > Erscheinungsbild > Design** oder **SUPER + Ctrl + Shift + N**. Ein rechter Doppelklick auf freie Desktopfläche öffnet das Designkarussell. Sonne filtert helle, Mond dunkle Designs; erneutes Anklicken zeigt alle. Das + öffnet den separaten Katalog mit demselben Filter. Ctrl+Tab wechselt Filter, Tippen sucht, Pfeile/Tab bewegen und Enter wendet an. Backspace bearbeitet die Suche, auch bis sie leer ist; Escape leert sie vor dem Schließen.

**SUPER + Ctrl + N** öffnet die Hintergrundbilder, **SUPER + Shift + N** wechselt zum nächsten. Ein Häkchen markiert die aktive Wahl in Walker. Änderungen zeigen keine Erfolgsbenachrichtigungen. Ultrawide-Monitore, deren Breite mindestens das Doppelte der Höhe beträgt, verwenden die 21:9-Version mit weniger Beschnitt; andere verwenden 4K in 16:9.

Eitr hat vier Hintergrundbilder: Aurora-Fjord (Standard), Abendfjord, Rune Seal und Runestone. Die Auswahl erfolgt über dieselben Steuerelemente; die Palette bleibt gleich. Das vierte Bild, Runestone, ist animiert: Polarlichter bewegen sich langsam hinter dem Runenring, aktualisieren sich hinter normalen Fenstern seltener, pausieren hinter Vollbildanwendungen und bleiben auf dem Sperrbildschirm still. Bei Software-Rendering (etwa in einer VM ohne 3D-Beschleunigung) wird das ausgewählte Standbild verwendet; dasselbe gilt, wenn der Renderer nicht erkannt werden kann. Graphite wurde entfernt; gespeicherte Graphite-Auswahlen wechseln zu Eitr und dessen Standardbild.

Die 13 mitgelieferten Themes enthalten zehn dunkle Paletten der Welten: Alfheim, Asgard, Helheim, Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim und Vanaheim. Jedes Welten-Theme hat zwei bis fünf Originalhintergründe in verschiedenen Tusche-, Gouache-, Cel-Shading- und Malstilen, in beiden Bildformaten. Der erste Hintergrund entspricht meist der Theme-Vorschau; Svartalfheim behält seine unabhängige Vorschau.

Eitr Light ist die helle Variante von Primordial Venom, mit blassgrünen Flächen, dunkelgrünem Text, giftgelbgrünen Akzenten und Jade-/Smaragdtönen. Die vier statischen Hintergründe sind Abendfjord (Standard), The Gates of Yggdrasil, Rune Seal und Primordial Drop, jeweils mit einer eigenen Panoramakomposition. Wähle es in der Kategorie Hell; Eitr bleibt der Standard. Design-Hintergrundbild verwendet das ausgewählte Standbild auf dem Sperrbildschirm.

Wenn Hyprpaper das gewählte Hintergrundbild nicht anzeigen kann, zeichnet die Leiste dasselbe Standbild auf jedem betroffenen Bildschirm, einschließlich der Ultrawide-Varianten. Die Auswahl von Hintergrundbild und Theme gilt auch im Focus-Modus; die Ersatzanzeige wechselt ohne die Enthüllungsanimation.

## Eigene Hintergrundbilder, Designs und Sperrbildschirme

Eigene Bilder, Designs und Sperrbildschirme bleiben auf diesem Computer, in `~/.local/share/eitr/` (`wallpapers`, `themes` und `lockscreens`). Eitr lädt sie nie hoch und teilt sie nie, und Updates verändern sie nicht. Sie erscheinen neben den ausgelieferten, markiert mit **Eigenes**, und nur sie lassen sich löschen: auswählen, **Entf** drücken, dann Enter zum Bestätigen oder Escape zum Behalten.

- **Walker > Einstellungen > Desktop > Erscheinungsbild > Hintergrundbild > Eigenes Hintergrundbild hinzufügen** nimmt eine Bilddatei oder eine https-Adresse. Downloads enden bei 50 MB, und Eitr behält eine Kopie erst, nachdem geprüft wurde, dass die Datei ein JPEG-, PNG- oder WebP-Bild ist. Die Adresse einer Webseite funktioniert, wenn die Seite ein Hauptbild anbietet; sonst die Adresse des Bildes selbst kopieren. Das Bild wird sofort angewendet und erscheint in der Hintergrundbildliste, im Karussell und bei SUPER + Umschalt + N. Wird das aktive Hintergrundbild gelöscht, wechselt Eitr zuerst zum ersten Hintergrundbild des Designs. Wähle, ob dein Hintergrundbild bei allen Themen oder nur beim aktuellen Thema erscheint.
- **Walker > Einstellungen > Desktop > Erscheinungsbild > Design > Design erstellen** fragt nach einem Bild (das aktuelle Hintergrundbild, ein eigenes, eines des Designs oder eine andere Datei oder https-Adresse), hell oder dunkel (Automatisch folgt der Helligkeit des Bildes) und einem Namen. Nach der Übersicht erzeugt Eitr aus dem Bild eine vollständige Palette, bei der Text auf dem Hintergrund gut lesbar bleibt, und wendet das Design auf Leiste, Terminal, Starter, Apps und Symbole an. Danach folgt eine Farbliste: Akzent, Hintergrund, Text oder eine der sechs Terminalfarben wählen, sechs Hex-Ziffern eingeben, und die Änderung gilt sofort; Escape beendet. **Strg + E** auf einem eigenen Design öffnet die Liste erneut. Wird das aktive Design gelöscht, kehrt Eitr zuerst zum Design zurück, das vor dem Erstellen aktiv war.
- **Walker > Einstellungen > Desktop > Sperrbildschirm > Sperrbildschirm erstellen** nutzt das Design Theme Wallpaper oder Material mit deinem Bild, einer optionalen Akzentfarbe und einer optionalen Begrüßung unter der Uhr und zeigt dann eine Vorschau. Er wird wie jedes Design ausgewählt. Der Anmeldebildschirm kann den Home-Ordner nicht lesen: Er zeigt dasselbe Design, mit deinem Bild bei Theme Wallpaper und dem eigenen Bild des Designs bei Material. Wird der aktive Sperrbildschirm gelöscht, wählt Eitr zuerst sein Design.

## Das Leistenlayout ändern

**Einstellungen > Desktopleiste** wählt Layout, Position und Darstellung; siehe [Desktopleiste](handbook:desktop-bar). **Einstellungen > Fenster > Ecken** wählt Eckig, Abgerundet oder Stark abgerundet. Fensterabstände und Bewegung reduzieren stehen auf derselben Fenster-Seite. Fremde Apps können ihren eigenen internen Stil behalten.

<!-- eitr-figure: window-style -->

Fensterabstände und Ecken, wie **Einstellungen > Fenster** sie zeigt, mit deiner aktuellen Auswahl markiert. Standardmäßig liegen 6 px zwischen Fenstern und 12 px an den Bildschirmrändern.

Unter **Einstellungen > Fenster > Fensterabstände** oder **Walker > Einstellungen > Desktop > Fenster > Fensterabstände** stehen Keine, Klein, Mittel (Standard) und Groß zur Wahl. Die lokale Auswahl bleibt bei Themewechseln und Neuladen erhalten.

## Schrift ändern

Wähle eine installierte Schrift unter Einstellungen > Erscheinungsbild > Schriften & Zeiger. JetBrainsMono Nerd Font ist Standard. Die Auswahl aktualisiert unterstützte Desktop-Apps; manche Apps behalten eigene Schrifteinstellungen. Entferne Schriftfamilien unter Walker > Einstellungen > Desktop > Erscheinungsbild > Schriftarten und prüfe die zugehörigen Pakete. Die letzte nutzbare Familie lässt sich nicht löschen.

## Mauszeiger ändern

Öffne Einstellungen > Erscheinungsbild > Schriften & Zeiger. Zeigerfamilie wählt Bibata Modern, Breeze oder Vanilla DMZ. Zeigerfarbe bietet Automatisch, Dunkel oder Hell; Automatisch folgt dem Design, ohne die Familie zu ändern. Zeigergröße passt die Größe an. Explizite Farb- und Größenwahlen bleiben bei Designwechseln erhalten. Die Seite zeigt den ausgewählten Zeiger, wenn dessen Dateien verfügbar sind.

## Einen Sperrbildschirm wählen

**Einstellungen > Sperrbildschirm** bestimmt Sperr- und Anmeldebildschirm. Bestehende Einstellungen bleiben bei Designwechseln erhalten.

Verfügbar sind Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing und Theme Wallpaper. Danach folgen deine eigenen Sperrbildschirme; Vorschauen sperren die Sitzung nicht. Ein nicht mehr ausgeliefertes Design wird durch Clockwork Tape ersetzt. Neue Installationen beginnen mit Eitr.

Eitr zeigt die EITR-Wortmarke in der Akzentfarbe deines Themas im goldenen Runenring des Startbildschirms, der jede Sekunde weiterrückt, vor einem Sternenhimmel mit Milchstraße, gelegentlichen Sternschnuppen und dem Polarlicht des Desktops auf reinem Schwarz (auf einem OLED bleiben diese Pixel aus). Die Uhr zeigt Stunden und Minuten in Eitrs eigenen nordischen Ziffern und folgt der 12- oder 24-Stunden-Einstellung.

Jedes eingegebene Zeichen meißelt eine Rune in das Passwortfeld (immer dieselben Runen in fester Reihenfolge, sodass nur die Länge sichtbar ist); Pfeiltasten, Pos1 und Ende bewegen den Blockcursor, Rücktaste oder Entf lassen die Rune daneben zerbröckeln. Nach erfolgreicher Authentifizierung wird die Sitzung sofort entsperrt. Beim Absenden, nach einer fehlgeschlagenen Anmeldung und beim Kontowechsel verschwinden die Runen sofort, ohne zu zerbröckeln.

Bewegung reduzieren hält alles still und überspringt die Meißel- und Bröckeleffekte. In einer Vorschau schließen Enter und Escape sie sofort, ohne etwas zu entsperren.

Die Bilder sind für 4K (3840×2160, 16:9) vorgesehen. Coffee und Pillow behalten ihren ruhigen Anime-Stil mit nordischer Kleidung; Material und Clockwork verwenden dezente Runenornamente. Nothing behält sein Design. QML und SVG bleiben skalierbar.

Vergleiche die neun Designs mit `bash quickshell/lockscreen/scripts/gallery.sh`. Dies ändert die Auswahl nicht; Anmeldung und Energieaktionen sind in der Galerie deaktiviert. Clockwork nutzt prozedurales QML. Coffee, Pillow, Material und Nothing behalten ihre lizenzierten Anordnungen mit neuen Bildern und installierter JetBrainsMono Nerd Font. Zusätzliche mitgelieferte Schriften oder Videos sind nicht erforderlich.

**Design-Hintergrundbild** zeigt das aktuelle Hintergrundbild mit Uhr oben links und Passworteingabe unten rechts. Die Walker-Vorschau zeigt das aktuelle Bild. Spätere Änderungen erscheinen beim nächsten Sperren oder Öffnen der Vorschau; Ctrl+P zeigt das gesamte Design ohne Sperren. Der Anmeldebildschirm kann deinen persönlichen Ordner nicht lesen. Er nutzt eine Kopie, die Eitr beim Auswählen dieses Designs und bei jedem Bildwechsel speichert. Fehlt sie, wird ein anderes Bild des aktuellen Designs oder der Eitr-Standard verwendet.

Auf PCs mit mehreren Konten zeigt der Anmeldebildschirm den ausgewählten Benutzer. Ein Klick auf die linke oder rechte Hälfte der Benutzerauswahl oder Ctrl+Left / Ctrl+Right wählt ein anderes Konto; Enter sendet weiterhin das Passwort und Escape behält seine bisherige Funktion. Mit einem Konto bleibt die Anmeldung optisch unverändert. Der Sperrbildschirm zeigt nach Möglichkeit den echten Namen der gesperrten Sitzung und akzeptiert nur das Passwort dieses Kontos.

Bei mehreren Bildschirmen erscheint der Anmeldebildschirm nur auf dem größten; die anderen bleiben schwarz.

Benutzer wechseln (Ctrl+Alt+U) öffnet die SDDM-Anmeldung und lässt die ursprüngliche Sitzung gesperrt. Zurück in der gesperrten Sitzung klicken Sie einmal in das Passwortfeld, bevor Sie tippen. Die Aktion erscheint nur bei mehreren geeigneten Konten und wenn SDDM den Wechsel unterstützt. Vorschau und Galerie verwenden drei fiktive Konten und authentifizieren nie.

Integrierte Themen gehören zu Eitr und können nicht entfernt werden. Der Papierkorb bei einem heruntergeladenen Thema löscht dessen installiertes Paket; das aktuelle Thema kann nicht entfernt werden.

## Technische Hinweise

Das Limine-Startmenü verwendet die aktuellen Designfarben, einen EITR-Titel und eine größere Schrift. Neue Installationen richten das ein; nach einem Designwechsel folgt das Menü beim nächsten Herunterfahren. Ist dein Design nicht lesbar, werden Standardfarben verwendet. Starteinträge bleiben unverändert und `limine.conf` wird vor jeder Änderung gesichert. Bei aktiviertem Secure Boot wird die Gestaltung übersprungen: Eine Änderung der Limine-Konfiguration würde bei registriertem Konfigurationshash den Start verhindern.

## Hintergrundvorschau und Zuweisungen

Unter Einstellungen > Erscheinungsbild > Thema & Hintergrund zeigt ein Klick auf ein Bild dessen Standbild auf dem Desktop. Anwenden speichert es; Vorschau abbrechen, Seitenwechsel oder Schließen stellt die gespeicherte Auswahl wieder her. Die Palette bleibt gleich. Walker > Einstellungen > Desktop > Erscheinungsbild > Hintergrund öffnet das Karussell beim gewählten Bild. Pfeile zeigen die Vorschau, Eingabe wendet an, Escape oder ein Klick außerhalb bricht ab.

Über den Hintergrundbildern des Karussells wechseln **Dieses Theme** und **Alle Themes** zwischen den Bildern des aktuellen Themes und denen aller installierten Themes (auch mit Strg+Tab). Unter jedem Bild steht sein Name (bei allen Themes auch das Theme, aus dem es stammt), und Tippen durchsucht Namen und Themes; deine eigenen Bilder kommen zuletzt. Die Auswahl ändert nur das Hintergrundbild; die Farben des Themes bleiben.

Hintergrund pro Bildschirm unter Einstellungen > Erscheinungsbild > Thema & Hintergrund (oder Walker > Einstellungen > Desktop > Erscheinungsbild > Hintergrund pro Bildschirm) ist standardmäßig aus: Auswahl und Vorschau ändern alle Bildschirme. Eingeschaltet wird nur der Bildschirm geändert, den du bei der Bildauswahl verwendest. Ohne eigene Auswahl zeigt ein Bildschirm den globalen Hintergrund.

Bildschirmzuweisungen und Schalter bleiben lokal. Ausschalten stellt sofort überall den globalen Hintergrund wieder her und behält die Bildschirmwahl; Einschalten stellt diese wieder her. Anmeldung und erneuter Anschluss stellen jeden Ausgang unabhängig wieder her. Ein Themenwechsel löscht alle Bildschirmzuweisungen, behält den Schalter und verwendet den neuen Themenhintergrund. Eine reine Hintergrundauswahl behält die Zuweisungen. Nicht verfügbare Bilddateien werden aus den Zuweisungen entfernt. Runestones Animation setzt nach der Vorschau wieder ein; Softwarerendering zeigt dasselbe Standbild.
