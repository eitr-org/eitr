# Focus

![Focus-Tabstreifen mit Beispielfenstern und zwei verbundenen Bereichen.](assets/focus-strip.png)

Focus ersetzt die Leiste durch einen 28 px hohen Tabstreifen oben auf jedem
Bildschirm. Öffne **Einstellungen > Stil > Focus** oder **Kontrollzentrum > Stil > Focus**, oder
starte `eitr focus on`. `eitr focus status` zeigt `on` oder `off`, ohne Hyprland
abzufragen. `eitr focus off` stellt die normale Leiste, Effekte und Tastenkürzel
wieder her. Es gibt kein eigenes Tastenkürzel zum Umschalten.

Die Einstellung liegt in `~/.config/eitr/focus.json` (unter `$XDG_CONFIG_HOME`,
falls gesetzt). Sie bleibt nach Neustarts, Updates und Themewechseln erhalten.
Die Einstellungen der normalen Leiste bleiben getrennt und werden nicht ersetzt.

## Tabs und Bereiche

Offene Fenster, auch schwebende und solche auf dem speziellen Arbeitsbereich,
werden in nativen Hyprland-Gruppen gesammelt. Eine Gruppe füllt den Bildschirm
unter dem Streifen. Abstände, Rahmen, runde Fensterecken, Unschärfe, Schatten und
Animationen sind aus. Der Streifen folgt dem Theme, hat wie das Tabs-Layout eckige
Enden und zeigt nur Titel, Uhr und Netzwerk-/Akkustatus. Der Akku erscheint nur
bei einem Systemakku. Lange Titel werden gekürzt; viele Tabs lassen sich scrollen.
Der hervorgehobene Tab kennzeichnet das aktive Fenster. Akzentlinien verbinden
die sichtbaren geteilten Bereiche. Anwendungsinterne Dialoge und Menüs dürfen
ihren eigenen Stil behalten.

- **SUPER + 1–9** wählt Tab 1–9 auf dem aktiven Bildschirm.
- **SUPER + Tab / SUPER + Shift + Tab** wählt den nächsten/vorherigen Tab.
- **SUPER + backslash** teilt die Gruppe mit ihrem nächsten Tab nebeneinander.
- **SUPER + minus** stapelt diesen Tab darunter.
- **SUPER + H/J/K/L** fokussiert links/unten/oben/rechts.
- **SUPER + Shift + H/J/K/L** macht schmaler/höher/niedriger/breiter, wie auf dem normalen Desktop.
- **SUPER + Shift + backslash** bringt das aktive Fenster in eine bildschirmfüllende Tabgruppe zurück und vereint alle geteilten Bereiche in Tabs.

Teilen erfordert einen weiteren Tab in der aktiven Gruppe. Höchstens vier Bereiche
sind möglich: zwei nebeneinander oder gestapelt; drei oder vier in einem 2×2-Raster
(der dritte füllt die untere Zeile bis zum vierten). Die Größenänderung verschiebt
die gemeinsamen Rasterteiler. Das Rückkehrkürzel stellt mit einem Tastendruck eine bildschirmfüllende Gruppe wieder her. Tabnummern folgen der Fensterreihenfolge des Compositors, die auch der
Streifen nutzt. Normale Kürzel für Arbeitsbereiche, Schweben, Fensterbewegung und
Leistensichtbarkeit sind inaktiv. Starter, Fenster schließen, Kontrollzentrum und
Handbuch bleiben verfügbar. Lernen > Tastenkürzel zeigt die Focus-Tasten, solange
der Modus aktiv ist.

## Bildschirme und Wiederherstellung

Jeder Bildschirm hat eigene Fenster, einen Streifen und bis zu vier Bereiche.
Tabkürzel gelten für den aktiven Bildschirm; Richtungsfokus kann zum nächsten
Bildschirm wechseln, wenn in der Richtung kein Bereich liegt. Anschließen erzeugt
einen Streifen. Nach dem Trennen verschiebt Hyprland Fenster auf einen verfügbaren
Bildschirm; Focus sammelt sie dort. Die Bildschirmauswahl der normalen Leiste
begrenzt die Focus-Streifen nicht.

Ausschalten löst Gruppen auf und verteilt Fenster auf normale nummerierte
Arbeitsbereiche, zwei je Arbeitsbereich, auf ihren aktuellen Bildschirmen. Alte
Positionen, schwebende Geometrie und Vollbildzustände der Anwendungen bleiben
nicht erhalten. Ein leerer Desktop und wiederholte on/off-Befehle funktionieren.
Stürzt der Streifenprozess ab, bleiben native Gruppen und Tastaturbedienung aktiv.
Starte `eitr focus off` in einem Terminal, um den Desktop ohne Streifen wiederherzustellen.
Ein Hyprland-Neuladen wendet die Einstellung an und sammelt neue Fenster, ohne
bestehende Teilungen aufzulösen; Teilergrößen und die Ausrichtung zweier Bereiche
werden zurückgesetzt. Fehlgeschlagene Befehle zeigen den Fehler. Wiederhole
`eitr focus off`, sobald Hyprland erreichbar ist. Beim Schließen eines Bereichs
werden die übrigen Bereiche vergrößert.
