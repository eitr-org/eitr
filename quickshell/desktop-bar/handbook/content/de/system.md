# Eine Einstellung finden

**SUPER + ,** öffnet Einstellungen. System ist die Übersicht, kein Ordner für alle Einstellungen.

Suche in der Seitenleiste der Einstellungen nach einer einzelnen Einstellung, etwa **Zeigergröße**, oder einer Seite. Unter dem Namen stehen Seite und Reiter. Wähle mit Auf/Ab und Eingabe oder per Klick ein Ergebnis: Der Reiter öffnet sich, das Bedienelement wird sichtbar und kurz hervorgehoben. Escape leert zuerst die Suche. Bei reduzierter Bewegung erscheint und verschwindet die Hervorhebung ohne Überblendung.

<!-- eitr-figure: settings-window -->

Das Einstellungsfenster hat eine durchsuchbare Seitenleiste und Karten für zusammengehörige Bedienelemente. Es bleibt beim Klick außerhalb offen. Escape, die Schließen-Schaltfläche oder das normale Tastenkürzel zum Schließen beendet es.

Links am unteren Panelrand schließen das Panel und öffnen die passende Einstellungsseite. Alle Einstellungen im Kontrollzentrum tut dasselbe; **SUPER + I** öffnet die Schnellsteuerung. Siehe [Kontrollzentrum](handbook:control-center).

Wähle Einstellungsfarben unter Einstellungen > Erscheinungsbild > Design und Hintergrundbild: Theme-Farben folgt deinem Desktop, Eitr-Website verwendet die Website-Palette. Das betrifft Einstellungen, Handbuch sowie Themes und Plugins, nicht das Desktop-Design.

Den separaten Katalog Themes und Plugins öffnest du mit SUPER + F2 oder Weitere Themes im Erscheinungsbild.

## Eine Seite wählen

Verwende die folgenden Seitennamen. Anleitungen stehen in den verlinkten Kapiteln.

| Seite | Mehr erfahren |
| :--- | :--- |
| System | [System](handbook:information) |
| Bildschirme — Bildschirme, Nachtlicht | [Bildschirme](handbook:devices) |
| Ton | [Ton](handbook:devices) |
| Verbindungen — Wi-Fi, Bluetooth | [Verbindungen](handbook:connectivity) |
| Streaming | [Streaming](handbook:remote-access) |
| Eingabe | [Eingabe](handbook:devices) |
| Erscheinungsbild — Design und Hintergrundbild, Schriften & Zeiger, Terminal | [Erscheinungsbild](handbook:appearance) |
| Desktopleiste | [Desktopleiste](handbook:desktop-bar) |
| Fenster | [Fenster](handbook:appearance) |
| Sperrbildschirm | [Sperrbildschirm](handbook:appearance) |
| Benachrichtigungen | [Benachrichtigungen](handbook:information) |
| Focus | [Focus](handbook:focus) |
| KI-Assistent | [KI-Assistent](handbook:development) |
| Tastenbelegungen | [Tastenbelegungen](handbook:shortcuts) |
| Standard-Apps | [Standard-Apps](handbook:apps) |
| Benutzer | [Benutzer](handbook:security) |
| Sicherheit | [Sicherheit](handbook:security) |
| Aktualisierungen | [Aktualisierungen](handbook:maintenance) |
| Diesen PC prüfen | [Diesen PC prüfen](handbook:troubleshooting) |
| Über | [Über](handbook:information) |

## Dein Profilbild ändern

Öffne Einstellungen > Benutzer (oder klicke in der System-Übersicht der Einstellungen auf dein Bild) und klicke auf dein Bild. Die Dateiauswahl des Systems öffnet sich schwebend und zentriert über den Einstellungen und zeigt nur Bilder; nach der Auswahl öffnet sich der Zuschneide-Editor als Blatt über den Einstellungen. Ziehe die runde Vorschau zum Verschieben; Mausrad, Schieberegler oder +/− zoomen von 1× bis 4×, die Pfeiltasten verschieben. Speichern (oder Enter) übernimmt den Zuschnitt; Abbrechen oder Escape schließt das Blatt, ohne ihn anzuwenden. Das Papierkorbsymbol unter deinem Bild entfernt es nach einer Bestätigung.

Das Bild erscheint im Kontrollzentrum, auf dem Sperrbildschirm und am Anmeldebildschirm immer rund. Das Kontrollzentrum zeigt das Bild oben in seiner Navigation nur an; ohne Bild zeigt es dort nichts, ebenso Sperr- und Anmeldebildschirm. Die Einstellungen zeigen stattdessen den Anfangsbuchstaben deines Namens auf einem Kreis in der Akzentfarbe. Unterstützt werden PNG, JPEG, WebP, GIF (erstes Bild) und BMP bis 40 MB und 12000 Pixel pro Seite.

Eitr korrigiert die Ausrichtung, entfernt Metadaten, speichert ein PNG mit 512×512 Pixeln unter `~/.face` und aktualisiert AccountsService für SDDM. Bei einem Fehler bleibt das Bild für den Sperrbildschirm erhalten; Oberfläche oder CLI melden den Anmeldefehler.

## Dein Passwort ändern

Öffne Einstellungen > Benutzer und wähle Passwort ändern neben deinem Namen. Gib dein aktuelles Passwort ein, dann zweimal das neue: Enter springt zum nächsten Feld und bestätigt im letzten; Escape bricht ab. Die Passwortregeln des Systems entscheiden, was angenommen wird, und ein abgelehntes Passwort zeigt den Grund. Eitr stellt auch den Anmelde-Schlüsselbund auf das neue Passwort um, damit gespeicherte Passwörter bei der Anmeldung weiter entsperrt werden. Eine Passphrase für die Festplattenverschlüsselung ist davon getrennt und bleibt gleich. Walker > Einstellungen > Sicherheit > Passwort ändern tut dasselbe in einem Terminal.

## Konten verwalten

Administratoren haben unter Einstellungen > Benutzer die Register **Benutzer** und **Verwalten**. Standardkonten sehen nur die Benutzerliste. Verwalten bietet Benutzer erstellen…, Typ ändern, Passwort setzen für andere Konten und Entfernen mit einer Auswahl für den persönlichen Ordner. Bestätige im Dialog und drücke dann im Aufgabenterminal Enter zum Fortfahren oder Esc zum Abbrechen; Passwörter werden nur dort eingegeben. Persönliche Ordner bleiben standardmäßig erhalten. [Benutzerkonten](handbook:security) erklärt Berechtigungen, Schlüsselbund-Einschränkungen und Schutzmaßnahmen beim Entfernen.

## Walker als Alternative verwenden

**SUPER + F** öffnet Walker. Sein Einstellungsmenü enthält weiterhin Ordner wie Stil, Geräte und Eingabe sowie System. Das sind Walker-Pfade, keine Seiten der Einstellungs-App.

<!-- eitr-figure: launcher -->

Walkers Einstellungsmenü ist eine Alternative mit eigenen Ordnern. > öffnet ein Untermenü; die Beschreibung unter einer Aktion erklärt ihre Wirkung.

Walker zeigt Ordner vor Aktionen. Tippe zum Suchen, drücke Enter zum Öffnen und Shift + Backspace für Zurück. Die Sprachwahl bleibt unter Walker > Einstellungen > Sprache; siehe [Sprache](handbook:language).
