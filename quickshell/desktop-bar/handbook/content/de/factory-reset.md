# Auf Werkseinstellungen zurücksetzen

Mit der Eitr-ISO installierte Rechner können über Walker → System → Instandhaltung → Werkseinstellungen zum Zustand der ersten Anmeldung zurückkehren. Die Wiederherstellung erfolgt lokal aus einer schreibgeschützten Kopie auf demselben Laufwerk. Das ist weder eine Datensicherung noch sicheres Löschen: Fällt das Laufwerk aus, gehen System und Wiederherstellungspunkt gemeinsam verloren.

## Der Wiederherstellungspunkt

Im letzten Schritt führt die geführte Installation `eitr-factory-reset capture` aus. Die fertige Installation wird im Btrfs-Subvolume `@eitr-factory` auf oberster Ebene gespeichert:

| Pfad | Inhalt |
|---|---|
| `root` | schreibgeschützter Snapshot von `@` (System, Konten, Einstellungen) |
| `home` | schreibgeschützter Snapshot von `@home` (vorbereitete persönliche Ordner) |
| `boot.tar` | Dateien der EFI-Partition: Limine, sein Menü, Kernel und initramfs |
| `manifest.json` | Erstellungszeit, UUIDs von Dateisystem und EFI-Partition, Konten, SHA-256 von `boot.tar` |

Danach wird auch `@eitr-factory` selbst schreibgeschützt. Es liegt neben `@`, nicht in `@/.snapshots`. Snapper listet es daher nie auf und entfernt es nicht bei der Bereinigung; Walker bietet keine Löschfunktion dafür. Root kann es weiterhin löschen; Formatierung oder ein Laufwerksausfall zerstören es ebenfalls. Seine Snapshots teilen Daten mit dem laufenden System. Anfangs benötigen sie wenig Platz; wenn Aktualisierungen Originaldateien ersetzen, wächst der Platzbedarf.

`capture` ersetzt keinen vorhandenen Wiederherstellungspunkt. Installationen ohne die ISO haben keinen; die Funktion Werkseinstellungen meldet dies.

## Die beiden Varianten

**Alles löschen** stellt den Zustand der ersten Anmeldung wieder her: Später installierte Anwendungen, geänderte Einstellungen, nachträglich angelegte Konten und sämtliche Dateien in den persönlichen Ordnern werden entfernt.

**Eigene Dateien behalten** stellt System, Anwendungen und Einstellungen wieder her und erhält die persönlichen Ordner. Bei jedem Konto des Wiederherstellungspunkts werden die aktuellen versteckten Einträge (`~/.config`, `~/.local`, `~/.ssh`, Browserprofile usw.) in einen sichtbaren Ordner namens `Settings before reset <date time>` im persönlichen Ordner verschoben. Anschließend werden die versteckten Einträge des Wiederherstellungspunkts zurückkopiert. Im persönlichen Ordner wird nichts gelöscht. Nach der Installation hinzugefügte Konten werden mit dem System entfernt; ihre Ordner bleiben jedoch unter `/home` bestehen.

Beide Varianten erhalten die Passphrase der Laufwerksverschlüsselung (der LUKS-Header wird nie verändert) und das aktuelle Passwort jedes Kontos, das auch im Wiederherstellungspunkt vorhanden ist. Ein TPM-Entsperrslot bleibt im LUKS-Header erhalten. Das wiederhergestellte initramfs fragt jedoch nach der Passphrase, bis die TPM-Entsperrung erneut eingerichtet wurde. Protokolle (`@log`) und Paketcache (`@pkg`) bleiben erhalten.

## Bestätigung

Die Walker-Aktion zeigt zwei getrennte Warnungen im Terminal:

1. Was die gewählte Variante entfernt und erhält. Nur `y` oder `yes` setzt den Vorgang fort; Enter bricht ab.
2. Welcher Rechner zurückgesetzt wird, dass er sofort neu startet und dass ungespeicherte Arbeit verloren geht. Du musst exakt `RESET MY COMPUTER` eingeben.

Das Root gehörende Hilfsprogramm (`/usr/lib/eitr/eitr-factory-reset`) prüft den eingegebenen Satz erneut und kontrolliert vor jeder Änderung:

- `/` ist das Subvolume `@`, `/home` ist `@home` auf demselben Btrfs-Dateisystem und `/boot` ist die FAT-formatierte EFI-Partition.
- Der Wiederherstellungspunkt und seine Snapshots sind weiterhin schreibgeschützt. Das Manifest nennt dieses Dateisystem und diese EFI-Partition; `boot.tar` stimmt mit seiner SHA-256-Prüfsumme überein.
- Secure Boot ist ausgeschaltet: Wiederhergestellte Startdateien sind nicht mit den registrierten Schlüsseln signiert.
- Kein früheres Zurücksetzen ist noch ausstehend.

`sudo /usr/lib/eitr/eitr-factory-reset status` (Walker → Zurücksetzungsstatus) führt dieselben Prüfungen ohne Änderungen aus.

## Ablauf des Zurücksetzens

Die laufenden Root- und Home-Dateisysteme werden niemals beschrieben. Unter dem neuen Subvolume `@eitr-reset-previous` auf oberster Ebene führt das Hilfsprogramm Folgendes aus:

1. Es erstellt einen beschreibbaren Snapshot des Root-Dateisystems des Wiederherstellungspunkts, legt darin Snappers Subvolume `.snapshots` erneut an, kopiert die aktuellen Passwörter hinein und aktiviert dort `eitr-factory-reset-finish.service`.
2. Es erstellt das neue Home-Dateisystem: einen beschreibbaren Snapshot des Home-Dateisystems des Wiederherstellungspunkts (Alles löschen) oder einen Snapshot des aktuellen `@home`, in dem die Einstellungen wie oben beschrieben beiseitegelegt werden (Eigene Dateien behalten).
3. Es archiviert die aktuellen Dateien der EFI-Partition in `boot.tar` und entpackt das Archiv des Wiederherstellungspunkts zum anschließenden Kopieren.

Ein Fehler bis hierhin entfernt `@eitr-reset-previous` und lässt den Rechner unverändert. Danach kopiert das Hilfsprogramm die wiederhergestellten Startdateien auf die EFI-Partition (bei einem Fehler stellt es das gerade erstellte Archiv wieder her), benennt `@` und `@home` innerhalb von `@eitr-reset-previous` in `old@` und `old@home` um, benennt die vorbereiteten Subvolumes in `@` und `@home` um und startet neu. Scheitert eine Umbenennung, werden die vorherigen Namen und Startdateien wiederhergestellt.

Beim nächsten Start bestätigt `eitr-factory-reset-finish.service`, dass das laufende Root-Dateisystem das wiederhergestellte ist. Der Dienst löscht `@eitr-reset-previous` einschließlich der Snapper-Snapshots des alten Systems und deaktiviert sich selbst.

## Unterbrochenes Zurücksetzen wiederherstellen

Ein Stromausfall während der Umbenennungen kann dazu führen, dass `@` oder `@home` fehlt. Starte die Eitr-ISO, verlasse den Assistenten mit Escape, entsperre gegebenenfalls das verschlüsselte Laufwerk (`cryptsetup open /dev/<partition> root`) und prüfe:

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # or the Btrfs partition itself
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- `@` und `@home` sind vorhanden und `@eitr-reset-previous/new-root` ist verschwunden: Der Austausch ist abgeschlossen. Starte neu; der Abschlussdienst bereinigt die Reste.
- `@` oder `@home` fehlt: Benenne das passende `@eitr-reset-previous/old@` oder `old@home` zurück um (`mv /mnt/@eitr-reset-previous/old@ /mnt/@`). Entpacke danach `@eitr-reset-previous/boot.tar` auf die EFI-Partition, damit sie zum alten System passt, und starte neu.

Lösche `@eitr-reset-previous` mit `btrfs subvolume delete --recursive` erst, wenn das System korrekt startet. Bis dahin enthält es das vorherige System.

## Überprüfung

Getestet in UEFI-VMs ohne Netzwerk (siehe [LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)): beide Varianten bei einer unverschlüsselten Neuinstallation mit Laufwerkslöschung und bei einer LUKS2-Installation neben einem Laufwerk mit Windows-ähnlicher Struktur. Danach gelangen jeweils Start, Anmeldung und Bereinigung durch den Abschlussdienst. Noch nicht getestet: echte Hardware, Stromausfall während des Austauschs und Erhalt des Wiederherstellungspunkts über Online-Systemaktualisierungen hinweg (die VMs hatten kein Netzwerk).
