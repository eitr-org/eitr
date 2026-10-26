# Geräte und Eingabe

Diese Bedienelemente findest du unter **System > Geräte und Eingabe** oder über die entsprechenden Symbole in der Leiste. Das Kontrollzentrum bietet ebenfalls die alltäglichen Schalter und Regler.

## Audio und Mikrofon

Lautstärke wählt den Standardausgang und regelt die Gesamtlautstärke sowie laufende Wiedergabeanwendungen. Geräte erscheinen mit lesbarem Namen und Typsymbol; klicke auf das aktuelle Gerät, um ein anderes zu wählen, und benenne ein Gerät mit seinem Stift-Knopf auf diesem Computer um. Mikrofon wählt den Standardeingang, die Verstärkung und die Stummschaltung. Die Live-Pegelanzeige läuft nur bei geöffnetem Mikrofonpanel und schreibt kein Audio auf die Festplatte. Andere Einstellungen zu öffnen startet keine Mikrofonüberwachung.

Die Regler reichen bis 100 %; ein bereits höherer Wert bleibt bis zum Bewegen erhalten. Ein Wechsel des Standard-Audiogeräts kann ein Gespräch beeinflussen: Nimm ihn bewusst vor. Wiedergabesteuerung und Standardgeräteauswahl sind getrennt.

## Bildschirm und Helligkeit

Das Bildschirm-Panel listet aktive Monitore auf. Klicke einen an, um seine Einstellungen innerhalb der Karte zu öffnen; erneutes Klicken schließt sie. Der als **Haupt** markierte Monitor trägt Leiste, Panels und Benachrichtigungen. Aktiviere **Hauptbildschirm** bei einem anderen Monitor, um sie dorthin zu verschieben. Wird er getrennt, zeigt ein anderer **Haupt** an und übernimmt die Leiste bis zu seiner Rückkehr; deine Auswahl bleibt gespeichert.

Jeder Monitor bietet Auflösung, Bildwiederholrate, Skalierung und bei mehreren Monitoren die Position neben einem anderen oder Spiegelung. Der Hauptbildschirm bleibt an seiner Position; die übrigen werden darum angeordnet. Seine Positionszeile weist darauf hin. Ein Monitor kann neben jedem anderen platziert werden, außer einem, dessen Position bereits von ihm abhängt.

Jede Einstellung zeigt den aktuellen Wert in einer Zeile; klicke für die Auswahl. Position, Ausrichtung, Skalierung, Spiegelung und Hauptbildschirm werden sofort angewendet und gespeichert. Eine neue **Auflösung oder Bildwiederholrate** könnte ein schwarzes Bild verursachen. Dafür fragt das Panel unten **Diese Einstellungen beibehalten?** Ohne **Beibehalten** innerhalb von 15 Sekunden wird automatisch zurückgeschaltet, auch bei geschlossenem Panel. Die Einstellungen dieses Rechners liegen in `~/.config/hypr/displays.json`.

So lassen sich beliebig viele Monitore anordnen: jeweils links, rechts, über oder unter einem anderen und an dessen oberer, mittlerer oder unterer Kante ausgerichtet (links, mittig oder rechts bei vertikaler Anordnung). Die Beziehungen bleiben gespeichert: Ändert sich Auflösung oder Skalierung, folgen die benachbarten Monitore. Überlappende Anordnungen werden mit einer Meldung abgelehnt. Jeder angeschlossene Monitor erhält eine genaue Position, damit Hyprland beim Ändern eines Monitors nicht die anderen verschiebt.

**Anordnung manuell bearbeiten** öffnet `~/.config/hypr/local.lua` für nicht abgedeckte Fälle wie gedrehte Bildschirme oder einem Monitor zugewiesene Arbeitsflächen. Eine neue Datei enthält auskommentierte Beispiele für drei Monitore, Hochformat, vertikale Anordnung, Spiegelung und einen angedockten Laptop. Erst wenn du ein Beispiel aktivierst und `hyprctl reload` ausführst, ändert sich etwas. Dort konfigurierte Monitore haben Vorrang; entferne die Einträge, um diese Monitore wieder im Panel zu verwalten.

Die Helligkeit nutzt bevorzugt eine geeignete native Hintergrundbeleuchtung, sonst einen externen Monitor per DDC. Die Verfügbarkeit hängt vom Monitor und den Berechtigungen ab. Nachtlicht bietet einen manuellen Schalter und einen optionalen Zeitplan mit bearbeitbaren Zeiten.

**HDR** erscheint nur bei Monitoren, deren EDID PQ oder HLG unterstützt. Es zeigt den Desktop in HDR; Spiele können HDR auch bei ausgeschaltetem Schalter nutzen. Beim Ein- oder Ausschalten musst du die Änderung ebenfalls innerhalb von 15 Sekunden bestätigen, sonst wird sie zurückgesetzt. Bei aktivem HDR regelt **Helligkeit von SDR-Inhalten** SDR-Inhalte von 1,0× bis 2,0× und speichert sofort. HDR-Spiele im Vollbild können den Monitor auch bei ausgeschaltetem Desktop-HDR automatisch umschalten. In beiden Fällen nutzt Eitr die Spitzen- und Schwarzwerte aus der EDID des Monitors. Unter dem Schalter zeigt **Spitzenhelligkeit** diesen Spitzenwert in Nits.

## Tastatur

Belegungen fügst du in Walker unter System > Geräte und Eingabe > Tastatur hinzu oder entfernst sie dort. Tastaturbelegung hinzufügen listet alle Sprachen und Varianten (tippen zum Suchen); wähle eine Belegung und drücke Entf, um sie zu entfernen. Bis zu vier sind erlaubt, Duplikate werden abgelehnt, und mindestens eine muss bleiben. **Alt + Shift** wechselt zwischen ihnen. Ab zwei Belegungen zeigt die Leiste das Kürzel der aktiven (etwa US oder BR); ein Klick darauf oder das Kontrollzentrum wechselt sie. Tastaturbelegung und Systemsprache beziehungsweise Gebietsschema sind unabhängig.

Der Desktop startet mit der im Installationsprogramm gewählten Tastatur. US richtet US und US International ein; Akzente sind damit über Alt + Shift erreichbar.

### Optionale Navigation mit Caps Lock

Die optionale keyd-Konfiguration `distro/keyd/navigation.conf.example` sendet bei kurzem Drücken von Caps Lock Escape. Halte Caps Lock und drücke H/J/K/L für Links/Unten/Oben/Rechts. Andere Tasten behalten ihr Verhalten.

Installiere das Beispiel nach einer Neuinstallation als `/etc/keyd/navigation.conf` und aktiviere `keyd.service`, um diese Einstellung wiederherzustellen. Sie gilt für alle Tastaturen, auch außerhalb von Hyprland, und ist standardmäßig nicht aktiv. Zum Rückgängigmachen entferne die Konfiguration und lade keyd neu; deaktiviere den Dienst, wenn keine weiteren Zuordnungen ihn benötigen. Sprache und Belegung werden weiterhin separat gewählt.

## Laptop-Energie und Akku

Akku- und Energieprofilsteuerung erscheinen nur bei einem Systemakku, nicht allein wegen einer kabellosen Maus oder eines Headsets. Energiesparen/Ausgeglichen/Leistung erfordern power-profiles-daemon; nicht unterstützte Profile bleiben deaktiviert. Schätzwerte und Akkuzustand erscheinen nur, wenn die Hardware sie liefert.

Das Akkuladelimit benötigt eine unterstützte Firmware-sysfs-Schnittstelle und eine eingetippte Bestätigung. Aus erlaubt Laden bis 100 %. Nicht jeder Laptop unterstützt dies.

Bei 10 % erscheint eine Meldung, bei 5 % eine dringende, jeweils einmal pro Entladung. Auf Laptops installiert das Installationsprogramm außerdem die für neuere Modelle erforderliche Audio-Firmware (`sof-firmware`) und auf Intel-Laptops `thermald` zur Temperaturregelung.

Diese Funktionen sind **experimentell**, bis erste Nutzer sie auf echten Laptops bestätigen: Tasten für die Tastaturbeleuchtung und Zuklappen bei angeschlossenem externem Monitor. Dabei wird das Laptop-Display ausgeschaltet und der Desktop auf den externen Monitor verschoben; Aufklappen bringt ihn zurück. Ohne externen Monitor führt Zuklappen wie gewohnt zum Bereitschaftsmodus. Ruhezustand auf Festplatte wird nicht automatisch eingerichtet.
