# Leiste und Arbeitsflächen

Die Leiste hält Datum und Uhrzeit mittig. Links steht zuerst das Eitr-Logo, das das Kontrollzentrum öffnet, danach folgen Übersicht, Arbeitsflächenmarkierungen, Hardware, KI-Nutzung und automatische Sperre; rechts Geräte- und Statussteuerung. **Symbole anzeigen** blendet diese rechte Gruppe ein oder aus.

## Aktualisierungen

Das Updatesymbol rechts vor Benachrichtigungen prüft kurz nach der Anmeldung und alle sechs Stunden auf Paket- und AUR-Updates. Bei verfügbaren Updates bietet eine Benachrichtigung die Systemaktualisierung an. Während der Prüfung dreht es sich, danach zeigt es einen Haken bei aktuellem System oder ein Updatesymbol mit Anzahl und Downloadgröße im Tooltip. Klicken startet die Systemaktualisierung; Rechtsklick prüft erneut. Nach einer Systemaktualisierung wird automatisch neu geprüft. Offline zeigt es das System als aktuell und prüft bei der nächsten Anmeldung wieder. Eine private Kopie der Paketdatenbanken verhindert, dass das System teilweise aktualisiert zurückbleibt.

## Position und Erscheinungsbild

- Doppelklicke mit links auf **leere Leistenfläche**, um zwischen Unschärfe/Designfarbe zu wechseln; Neuinstallationen beginnen mit Designfarbe.
- Ein rechter Doppelklick auf leere Fläche wechselt Voll → Zentriert → Laschen → Voll.
- Ziehe leere Fläche nach oben, unten, links oder rechts, um die Leiste zu verschieben.
- Dieselben Einstellungen findest du unter **Stil > Desktopleiste** und Kontrollzentrum > Stil.
- **Bildschirme** (Anzeigen auf) zeigt die Leiste standardmäßig nur auf dem Hauptbildschirm oder auf allen Bildschirmen. Bei mehreren Leisten markiert jede die Arbeitsfläche ihres Bildschirms; Kürzel wie SUPER + , öffnen auf dem gerade genutzten Bildschirm, Benachrichtigungen erscheinen nur auf dem Hauptbildschirm. Wähle diesen im Bildschirm-Panel.

Im mittigen Modus bleibt nur die Uhr sichtbar, bis du den Mauszeiger darüber bewegst. Symbole klappen in gewohnter Reihenfolge aus. Die Stecknadel zwischen Medien und Uhr hält sie offen; geöffnete Panels ebenfalls. Bei voller Leiste schließen Panels direkt an, bei mittiger liegen sie daneben. Beide öffnen und schließen mit derselben flüssigen Animation. Jede Seite passt sich ihrem Inhalt an; die Uhr bleibt an jeder Bildschirmkante genau in der Bildschirmmitte.

Laschen zeigt einen durchgehenden 7-px-Streifen und drei inhaltsgroße Laschen für die linke, mittlere und rechte Gruppe. Die Laschen behalten die volle Leistentiefe (horizontal 30 px), feste trapezförmige Übergänge mit geraden 45°-Schrägen außerhalb des Innenabstands. Die Uhr bleibt auch mit Medien exakt in der Bildschirmmitte. Panels schweben wie im zentrierten Modus als abgerundete, abgelöste Flächen neben der Leiste, wie bei Voll links, mittig oder rechts ausgerichtet und mit dem äußeren Abstand zum Bildschirmrand, mit dem aktuellen Hyprland-Fensterabstand und derselben 320-ms-Animation. Lücken lassen Klicks durch. Die volle Tiefe bleibt für Fenster reserviert. Ein rechter Doppelklick wechselt Voll → Zentriert → Laschen → Voll. Die Knicke sind leicht geglättet und unabhängig von der Eckeneinstellung; die Enden am Bildschirmrand bleiben eckig und gefüllt. Laschen zeigt alle rechten Steuerelemente ohne Ein-/Ausblendpfeil. Das Wetter bleibt verborgen, bis der mittlere Tab berührt wird, und gleitet dann in 320 ms hinter der festen Uhr hervor. Nach kurzer Verzögerung beim Verlassen wird es eingeklappt; bei geöffnetem Wetterpanel bleibt es sichtbar. Nur die nachfolgende Seite wächst entlang der Balkenachse, mit 4 px Abstand nach dem letzten sichtbaren Element.

## Arbeitsflächen

Die Leiste beginnt mit 1–5 und wächst bis zur aktuellen beziehungsweise höchsten belegten Arbeitsfläche, höchstens bis 10. Höhere leere Markierungen verschwinden, sobald sie nicht mehr gebraucht werden. Ein Rechtsklick auf eine Markierung bietet Punkte, Glyphe, Zahlen oder Runen mit Live-Beispielen. Runen ist Standard und stellt 1 bis 10 durch die ersten zehn Runen des älteren Futhark dar (ᚠ ᚢ ᚦ ᚨ ᚱ ᚲ ᚷ ᚹ ᚺ ᚾ). Die aktive Markierung zeigt das Zeichen in der Akzentfarbe ohne gefüllten Hintergrund.

**SUPER + 1–9/0** wechselt die Arbeitsfläche; **SUPER + Shift + 1–9/0** verschiebt ein Fenster. **SUPER + Tab** öffnet die Übersicht. Klicke eine Vorschau oder verwende Pfeile und Enter; 1–9/0 wechselt direkt. Nur belegte nummerierte Arbeitsflächen erscheinen, ihre Vorschauen bleiben im Arbeitsspeicher. Escape oder ein Klick außerhalb schließt die Übersicht.

**SUPER + S** schaltet die spezielle Arbeitsfläche um, unabhängig von der Übersicht. **SUPER + Shift + Space** blendet die Leiste ein/aus, nicht den Benachrichtigungsdienst.

Mausgesten für Hintergrundbilder und Themen auf leerem Desktop stehen unter **Lernen > Mausgesten**. Verwende im Zweifel die Tastenkürzel der Karussells.

Audio/Mikro öffnet ein gemeinsames Panel mit getrennten Bereichen für Audioausgabe und Mikrofon. Tailscale und Streaming stehen direkt vor OBS. Ein Schalter im Kopfbereich verbindet Tailscale oder startet die Freigabe, darunter folgen Details und Geräte, und Einrichtungs- oder Diagnoseaktionen liegen im Menü „…“. Symbolschaltflächen zeigen ihren Hintergrund beim Darüberfahren; Panels aktualisieren sich beim Öffnen selbst, ein Aktualisierungssymbol dreht sich nur während des Ladens, und Tooltips erscheinen am Mauszeiger. Schalter und eingebettete Aktionsschaltflächen verwenden gemeinsame kompakte Größen.

**Musikvisualisierer** unter **Haupt > Werkzeuge** öffnet cava in den Theme-Farben. Ein Rechtsklick auf den Medien-Equalizer öffnet denselben Visualisierer; ein Linksklick öffnet weiterhin die Mediendetails. **q** oder **Esc** schließt ihn. Auf bestehenden Desktops wird cava bei Bedarf zuerst installiert.
