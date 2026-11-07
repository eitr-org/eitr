# Kontrollzentrum

Einstellungen und Leistenpanels verwenden dieselben Auswahlsteuerungen. Kurze Auswahlen erscheinen als Segmente; längere Listen öffnen sich als schwebende, scrollbare Auswahllisten. Schalter behalten ihre Aktionen. Goldene Beschriftungen und gravierte Schrift gehören zur Fensterfamilie der Einstellungen: Einstellungen, Handbuch sowie Themes und Plugins.

Auswahllisten unterstützen die Navigation durch Tippen, wenn das Auswahlfeld oder die Liste den Fokus hat. Tippe den Anfang einer Beschriftung, um den ersten Treffer hervorzuheben; Großschreibung und Akzente werden ignoriert. Innerhalb von 800 ms getippte Zeichen bilden das Präfix; nach einer Pause beginnt ein neues. Wiederholtes Tippen desselben Buchstabens wechselt zwischen Treffern. Enter übernimmt die hervorgehobene Auswahl, Escape bricht ab. Listen zeigen höchstens acht Zeilen und lassen sich scrollen. Sie öffnen unter dem Feld, auch über den Rand eines Leistenpanels hinaus, oder nach oben, wenn dort mehr Bildschirmplatz ist.

**SUPER + ,** öffnet Einstellungen mit **System**, Profil und Systemübersicht. Themes und Plugins haben ein eigenes Katalogfenster. **SUPER + I** öffnet das Kontrollzentrum.

## Einstellungen

Die Gruppen heißen Übersicht, Geräte, Desktop, Apps und Tasten, Konten und Sicherheit sowie System. Runen-Überschriften und eine gleitende goldene Markierung erleichtern die Navigation. Jede Seite hat einen Titel, eine Beschreibung und Karten mit beschrifteten Einstellungen. Das Fenster bleibt deckend. Das Handbuch sowie Themes und Plugins nutzen denselben Rahmen, dieselbe Seitenleiste, Seitenüberschrift und Karten und folgen derselben Farbwahl.

Verbindungen hat die Tabs **Wi-Fi** (mit Backend-Auswahl) und **Bluetooth**. Die Anzeige trennt **Bildschirme** und **Nachtlicht**. Erscheinungsbild trennt **Design und Hintergrundbild**, **Schriften & Zeiger** und **Terminal**. Links/Rechts wechselt den fokussierten Tab; die Suche öffnet den passenden Tab. `settings show connections/bluetooth` öffnet Bluetooth; `network` bleibt ein Alias. Bildkarten zeigen Leistenlayouts, Bildschirmkanten, Oberflächen, Medienanzeige, Fensterabstände, Ecken und Sperrbildschirme. Unter Erscheinungsbild wählt **Einstellungsfarben** zwischen **Theme-Farben** und **Eitr-Website** für Einstellungen, Handbuch sowie Themes und Plugins. Die lokale Datei `eitr/settings-app.json` speichert die Auswahl; `settings palette theme` und `settings palette website` ändern sie ebenfalls. Die Desktop-Farben bleiben davon unabhängig.

System zeigt eine Übersicht mit Profilbild, CPU/GPU/RAM-Auslastung, Hauptbildschirm, Betriebszeit, Eitr-Version, Update-Kanal und Theme-Palette. Hardwaredaten werden nur bei sichtbarer Übersicht aktualisiert. Das große Bild zeigt derzeit das Hintergrundbild. Der gemeinsame Datendienst liefert keine Netzwerkübertragungsraten.

**SUPER + F2**, **Weitere Themes** unter Darstellung und das **+** im Karussell öffnen den eigenständigen Katalog mit **Themes und Plugins**-Seitenleiste und Schließen-Schaltfläche. Einstellungen bleibt beim Klick außerhalb geöffnet; Escape oder Schließen beendet es. **SUPER + I** öffnet das Kontrollzentrum.

**SUPER + I** öffnet oder schließt das Kontrollzentrum. Es öffnet am aktuellen Leistenrand und schließt mit Escape oder einem Klick außerhalb. Beim Schließen wird auf Allgemein zurückgesetzt. Mit einer Full-Leiste am linken oder rechten Rand beginnt das Kontrollzentrum am oberen Bildschirmrand. Der Inhalt hat Innenabstand innerhalb der mit der Leiste verbundenen Fläche.

Seine Seiten sind Allgemein, Plugins und Werkzeuge. Die Zahnrad-Schaltfläche darunter, **Alle Einstellungen**, schließt das Kontrollzentrum und öffnet die Einstellungen mit Darstellung, Leiste, Geräten, Tastatur, Bildschirmen und System. Einklappbare Abschnitte beginnen normalerweise geschlossen; ein Klick auf den Titel schaltet sie um und bleibt bis zur Abmeldung gespeichert. Hat die Leiste ein eigenes Panel, etwa OBS, WiFi oder Bluetooth, öffnet das Kontrollzentrum dieses.

## Allgemein

- **Verbindungen:** WiFi- und Bluetooth-Schalter sowie Flugmodus.
- **Schnellaktionen:** automatische Bildschirmsperre, Absturzbenachrichtigungen, Nicht stören, Spielmodus (Effekte, Unschärfe und Popups aus, Leistungsprofil an, bis du ihn ausschaltest) und Nachtlicht. Ein eingeschalteter Schalter füllt sich mit der Akzentfarbe des Designs. Darunter führen Leiste ausblenden (SUPER+Shift+Space holt sie zurück) und Bildschirmschoner einmalig eine Aktion aus.
- **Ton:** Lautstärke sowie Mikrofonverstärkung und Stummschaltung, dazu zwei optionale, standardmäßig ausgeschaltete Schalter: **Benachrichtigungstöne** (ein Klang, ein anderer für dringende Benachrichtigungen; unwichtige bleiben still) und auf PCs mit Akku **Ladetöne** beim An- und Abstecken des Ladegeräts. Beide schweigen bei Nicht stören und im Spielmodus.
- **Bildschirm:** Helligkeit, auf Laptops mit eingebautem Bildschirm.
- **Medien:** Cover, Interpret, Wiedergabesteuerung und Positionswahl, sofern unterstützt.
- **Energie:** Sperren sowie **Ein/Aus…**, das Abmelden, Bereitschaft, Neustart und Ausschalten aufklappt.

Der Flugmodus merkt sich gesperrte Funkverbindungen und stellt nur diese wieder her. Nicht stören unterdrückt Popups, ohne den Verlauf zu löschen. Automatische Sperre ist nicht dasselbe wie das Verhindern des Schlafmodus; beachte den Schutz deines Bildschirminhalts.

## Werkzeuge

Screenshots (Auswahl, Vollbild, Fenster oder Auswahl direkt in die Zwischenablage), Aufnahme (OBS-Steuerung, Aufnehmen, Aufnehmen + Audio und Stopp), OCR, QR-Codes, Farbauswahl, Transkodieren, Erinnerungen und LocalSend-Freigabe. Das Panel schließt vor Beginn einer Auswahl oder Aufnahme.

## Schnellchat

Das Chatsymbol neben den Seiten öffnet eine flüchtige Unterhaltung mit dem unter Entwicklung > KI gewählten Standardassistenten. Ohne Standard oder bei deaktivierender Organisationsrichtlinie bleibt es verborgen. Enter sendet, Shift+Enter fügt einen Zeilenumbruch ein. Escape oder Zurück kehrt zu den Seiten zurück. Neuer Chat, Verlassen des Chats oder Schließen des Kontrollzentrums löscht alle Nachrichten und bricht ausstehende Antworten ab.

Antworten bieten auswählbares Markdown und Kopieren. Die Unterhaltung bleibt im Arbeitsspeicher; Eitr schreibt weder Verlauf noch Protokolle. Unter der Eingabe steht der Cloudanbieter oder der Hinweis, dass Ratatoskr auf diesem PC läuft. Cloudanbieter erhalten Nachrichten und bisherige Gesprächsbeiträge. Jede Nachricht enthält außerdem nur Eitr-Version/Kanal, Kernel, CPU/GPU/RAM und Thema als nicht vertrauenswürdigen Kontext. Benutzernamen, Hostnamen, Dateien, E-Mails, WLAN-Namen, Fenstertitel und Zwischenablage werden nicht erfasst. Der Assistent verwendet den schreibgeschützten Aufruf ohne Oberfläche mit dem ausgewählten Konto und kann das System nicht ändern. Fehler erscheinen im Chat.

## Plugins

**Einstellungen > Stil > Themes und Plugins** in Walker, **Weitere Themes** auf der Seite Erscheinungsbild der Einstellungen oder **SUPER + F2** öffnet das Fenster Themes und Plugins. Die Gruppe Plugins zeigt installierte, offizielle und Community-Plugins, installiert und aktualisiert sie nach einer Prüfung im Fenster, sucht nach Updates und entfernt installierte Plugins nach Bestätigung. Die folgenden Terminal-Abläufe bleiben verfügbar.

**Kontrollzentrum > Plugins** zeigt für jedes installierte Plugin eine kompakte Zeile mit Symbol, Namen und Aktivierungsschalter. Wähle eine Zeile, um Autor, Version, Beschreibung, Aktualisieren/Entfernen, Widgets, Leistenelemente und Vorschau zu sehen. Mit Zurück oder Escape kehrst du zur Liste zurück. Aktivieren/Deaktivieren erhält Positionen und stoppt oder startet Dienste, Walker-Einträge, Hooks und visuelle Komponenten; per CLI: `eitr plugin enable ID` oder `eitr plugin disable ID`. Plugins hinzufügen, Aktualisieren und Entfernen öffnen die geprüften Terminalabläufe; Entfernen verlangt Bestätigung. Allgemein behält nur Plugin-Kacheln. Visuelle Fehler haben eine unabhängige Aktion zum erneuten Aktivieren.

Plugins hinzufügen unterstützt auch Repositorys mit mehreren Plugins. Der Index `eitr-plugins.json` im Stammverzeichnis listet IDs und Ordner auf, jeweils mit eigener `eitr-plugin.json`. Wähle anhand von Name, Beschreibung und Symbol ein oder mehrere Plugins und prüfe jedes einzeln. Die Ablehnung eines Plugins genehmigt keine anderen. Ausgewählte Plugins teilen eine heruntergeladene Repository-Kopie und werden einzeln an den exakten Commit gebunden; ein Update lässt die genehmigten Commits der anderen unverändert. Die Details zeigen Repository-URL und Plugin-Ordner. Eine einzelne `eitr-plugin.json` im Stammverzeichnis funktioniert weiterhin wie bisher.

Die Systemaktualisierung prüft nur auf neue Plugin-Commits, auch wenn alle Pakete aktuell sind, und nennt Anzahl und Aktualisierungsweg. Sie prüft keinen Plugin-Code und aktualisiert keine Plugins; Netzwerkfehler werden still ignoriert. Starte **Plugins aktualisieren** unter **Kontrollzentrum > Plugins** neben Plugins hinzufügen oder **Plugins > Plugins aktualisieren**, oder nutze `eitr plugin update`. Die Markierung ↑ in der Zeile und „Aktualisierung verfügbar“ in den Details zeigen die letzte Prüfung des bestätigten Commits. Die separate Aktion behält Diffs, Risikohinweise und Bestätigungen für jedes Plugin bei.

Die Plugin-Liste zeigt „Dieses Plugin hat Fehler“ und die erste Meldung an. Wählen Sie das Plugin und Fehlerdetails anzeigen, um mehr zu erfahren; über den Schalter deaktivieren Sie es mit einem Klick. Nur Fehler, die eine Datei im Ordner des Plugins nennen, werden erfasst. Plugins haben dieselben Berechtigungen wie der Desktop; installieren Sie daher nur Plugins, denen Sie vertrauen.

## Profilbilder

Öffne Einstellungen > Benutzer (oder klicke in der System-Übersicht der Einstellungen auf dein Bild) und wähle „Bild ändern“. Die Dateiauswahl des Systems öffnet sich schwebend und zentriert über den Einstellungen und zeigt nur Bilder; nach der Auswahl öffnet sich der Zuschneide-Editor als Blatt über den Einstellungen. Ziehe die runde Vorschau zum Verschieben; Mausrad, Schieberegler oder +/− zoomen von 1× bis 4×, die Pfeiltasten verschieben. Speichern (oder Enter) übernimmt den Zuschnitt; Abbrechen oder Escape schließt das Blatt, ohne ihn anzuwenden. „Entfernen“ neben „Bild ändern“ löscht das Bild.

Das Bild erscheint im Kontrollzentrum, auf dem Sperrbildschirm und am Anmeldebildschirm immer rund. Das Kontrollzentrum zeigt das Bild oben in seiner Navigation nur an; ohne Bild zeigt es dort nichts, ebenso Sperr- und Anmeldebildschirm. Die Einstellungen zeigen stattdessen den Anfangsbuchstaben deines Namens auf einem Kreis in der Akzentfarbe. Unterstützt werden PNG, JPEG, WebP, GIF (erstes Bild) und BMP bis 40 MB und 12000 Pixel pro Seite. Eitr korrigiert die Ausrichtung, entfernt Metadaten, speichert ein PNG mit 512×512 Pixeln unter `~/.face` und aktualisiert AccountsService für SDDM. Bei einem Fehler bleibt das Bild für den Sperrbildschirm erhalten; Oberfläche oder CLI melden den Anmeldefehler.

## Weitere Einstellungsseiten

Tastenkürzel zeigt die vollständige Referenz aus Lernen mit Suchfeld. Standard-Apps wählt installierte Programme für Browser, Dateien, Text, Bilder, Video, Musik, E-Mail und PDF; Terminal nutzt dieselbe Einstellung wie Erscheinungsbild > Terminal. Benutzer (dein Konto) zeigt Bild und Anzeigename mit „Bild ändern“ und „Entfernen“. Git & Cloud zeigt gespeicherte Identitäten, Ordnerregeln und Anbieterkontexte; die Bedienelemente rufen die vorhandenen Kontohelfer direkt auf. Sicherheit behält Bestätigungen für privilegierte Änderungen bei. Aktualisierungen zeigt Kanal und ausstehende Pakete; Systemaktualisierung öffnet den vorhandenen Ablauf. Diesen PC prüfen startet schreibgeschützte Diagnosen nur auf Knopfdruck. Über zeigt Version, Kernel, Hardware, Lizenz und Projektlinks. Jede Seite lässt sich bis zur letzten Zeile scrollen und verlinkt das Handbuch.

Panel-Links öffnen die passende Einstellungsseite und schließen das Panel: Netzwerkeinstellungen öffnet Verbindungen > WLAN, Layouts hinzufügen oder entfernen öffnet Eingabe, Fernzugriffseinstellungen öffnet Streaming und KI-Assistenten öffnet KI-Assistenten. Eingebettete Panels bleiben bei Fokuswechseln sichtbar; Rücklinks sind in den Einstellungen ausgeblendet.

Die Einstellungen rufen Konto- und Sicherheitshelfer direkt auf; Auswahl und Bestätigung erfolgen auf der Seite, während Passwortabfragen, getippte Bestätigungen und Einrichtungsformulare ein Aufgabenterminal öffnen.
