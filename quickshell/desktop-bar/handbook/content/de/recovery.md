# Wiederherstellungs-Snapshots von Eitr

Snapshots sind Wiederherstellungspunkte, **keine Sicherungen auf einem anderen Gerät**. Ein Laufwerksausfall kann System und Snapshots gemeinsam zerstören. Bewahre unabhängige Sicherungen auf.

Eitr unterstützt Snapper auf einem Btrfs-Root-Dateisystem, in dem `/usr`, `/etc` und `/var/lib/pacman` im selben Root-Subvolume liegen. `/home` darf getrennt sein; ein Root-Snapshot umfasst es nicht. Nicht unterstützte Anordnungen verhindern die Aktualisierung, bevor Änderungen erfolgen. `install.sh` formatiert keine Laufwerke und ordnet vorhandene Subvolumes nicht um. Nur `eitr-guided-install` auf der ISO löscht das von dir bestätigte Laufwerk und erstellt diese Anordnung (siehe geführte Installation im README).

## Vor Aktualisierungen

Die Installation aktiviert `/etc/eitr/system-update-policy.conf`. Bevor System → Instandhaltung → Aktualisieren → Systemaktualisierung offizielle und AUR-Pakete aktualisiert, werden folgende Schritte ausgeführt:

1. Unterstützte Anordnung und Snapper-Konfiguration für das Root-Dateisystem prüfen.
2. `/boot` und `/efi` nur bei getrennten Einhängepunkten archivieren. Ein Verzeichnis `/boot` innerhalb des Btrfs-Root-Dateisystems ist bereits im Root-Snapshot enthalten. Die Archive liegen unter `/var/lib/eitr/boot-backups/<snapshot-number>/` und sind nur für Root zugänglich.
3. Einen Root-Snapshot vor der Aktualisierung erstellen.
4. Die Aktualisierung abbrechen, wenn die Sicherung der Startdateien oder die Snapshot-Erstellung fehlschlägt.

Nach Abschluss, Fehlschlag oder Ablehnung einer Aktualisierung wird der zugehörige Nachher-Snapshot erstellt. Seine Beschreibung hält das Ergebnis fest ("after package upgrade", "after failed package upgrade"). Wurde der Ablauf vorher beendet, schließt die nächste Systemaktualisierung zuerst den offenen Vorher-Snapshot mit einem Nachher-Snapshot namens "after interrupted package upgrade" ab. Bei einem Fehlschlag bleiben Vorher-Snapshot und Startdateiarchive in jedem Fall erhalten. Flatpak-Aktualisierungen, SDKMAN/NVM-Laufzeitumgebungen und Dateien auf getrennten Home-Subvolumes sind dadurch nicht geschützt. Erweiterte Aktualisierungen und direkte pacman/yay-Befehle erzeugen absichtlich keine automatischen Snapshots. Früher manuell installierte Eitr-Snapshot-Hooks müssen für diese Richtlinie entfernt werden.

Neue Snapper-Konfigurationen behalten über den Bereinigungs-Timer bis zu 10 normale und 5 wichtige nummerierte Snapshots. Bestehende Richtlinien bleiben erhalten. Bei jeder Systemaktualisierung werden nur die 10 neuesten Startdateiarchive behalten, passend zum Standardlimit für Snapshots. Entfernt Snapper einen Snapshot zuerst, kann dessen Archiv noch vorhanden sein. Prüfe daher vor der Wiederherstellung, ob der Snapshot existiert. Ein volles Laufwerk verhindert die Aktualisierung, statt den Schutz zu überspringen.

## Startschutz

Nach einer erfolgreichen Systemaktualisierung auf einer geführten Eitr-Installation hält der Startschutz den Vorher-Snapshot der Aktualisierung bereit (`/var/lib/eitr/boot-guard.json`). `eitr-boot-guard.service` zählt jeden Start früh im Startvorgang. `eitr-boot-guard-healthy.service` wertet ihn als erfolgreich, sobald der Anmeldebildschirm 45 Sekunden lang geöffnet war; damit wird der Schutz deaktiviert.

Erreichen zwei aufeinanderfolgende Starts nach der Aktualisierung diesen Punkt nicht, stellt der dritte Start automatisch wieder her. Dabei werden die getesteten Schritte des Zurücksetzens auf Werkseinstellungen verwendet:

1. Die Startdateien des Snapshots (`/var/lib/eitr/boot-backups/<number>/boot.tar`) werden auf die EFI-Partition kopiert, nachdem die aktuellen Dateien zur möglichen Rücknahme gesichert wurden.
2. Das fehlgeschlagene Root-Subvolume wird in `@eitr-guard-failed` umbenannt. Eine beschreibbare Snapshot-Kopie wird zu `@`; Snappers Speicher `.snapshots` wird dorthin verschoben.
3. Der Rechner startet mit dem wiederhergestellten System neu. Scheitert ein Schritt, werden Subvolumes und Startdateien in ihren vorherigen Zustand versetzt; es erfolgt kein Neustart.

Das wiederhergestellte System löscht `@eitr-guard-failed`, sobald es den Anmeldebildschirm erreicht. Bei der nächsten Anmeldung erscheint eine Benachrichtigung. Persönliche Ordner bleiben unverändert. Startet der Kernel selbst nicht, hilft dieser Schutz nicht. Starte stattdessen den Snapshot der Aktualisierung über das Startmenü (unten). Bei anderen Laufwerksanordnungen wird der Schutz nie aktiviert.

## Änderungen an der Authentifizierung

Sicherheit → Fingerabdruck/FIDO2 aktivieren sichert `/etc/pam.d/hyprlock`, `sddm` und `sudo` vor Änderungen unter `/var/lib/eitr/pam-backups/<timestamp>/`. Scheitert ein Schreibvorgang, werden alle drei wiederhergestellt. Fingerabdruck wird allen drei hinzugefügt; "nur Passwort" gilt daher auch für den Sperrbildschirm. pam_fprintd kann die Passwortabfrage um bis zu 10 Sekunden verzögern. So kehrst du über eine funktionierende Root-Shell oder ein TTY zu einer früheren Richtlinie zurück:

```sh
sudo ls /var/lib/eitr/pam-backups
sudo /usr/lib/eitr/eitr-system auth-restore <timestamp>
# Without the eitr-desktop package, the helper is /usr/local/lib/eitr/eitr-system.
```

## TPM-Laufwerksentsperrung

Sicherheit → TPM-Laufwerksentsperrung kann einem LUKS2-Root-Laufwerk einen TPM2-Schlüsselslot hinzufügen. Damit wird das Laufwerk beim Start ohne Passphrase entsperrt. Nichts davon wird vom Installationsprogramm ausgeführt. Das Root-Hilfsprogramm (`luks-tpm-check`, `luks-recovery-key`, `luks-tpm-enroll`, `luks-tpm-remove`) lehnt den Vorgang ab, sofern das Gerät nicht LUKS2 verwendet, kein TPM2-Gerät unter `systemd-cryptenroll --tpm2-device=list` erscheint oder noch kein Passphrasen- beziehungsweise Wiederherstellungsslot vorhanden ist. Es **fügt nur einen Slot hinzu**; die Passphrase bleibt erhalten.

- **Zuerst der Wiederherstellungsschlüssel.** Walker bietet `systemd-cryptenroll --recovery-key` an. Der Schlüssel erscheint einmal im Terminal und wird niemals gespeichert. Notiere ihn offline. Er funktioniert bei der normalen Passphrasenabfrage.
- **PCR-Auswahl.** Eitr bindet die Entsperrung an PCR 7 (Secure-Boot-Zustand und Schlüssel). Firmware-Aktualisierungen ändern ihn selten, Änderungen an Secure-Boot-Schlüsseln hingegen schon. PCR 7 bietet nur bei aktiviertem Secure Boot mit eigenen Schlüsseln nennenswerten Schutz (siehe [SECURE-BOOT.md](SECURE-BOOT.md)). Andernfalls kann jeder diesen Rechner mit einer geänderten Kernel-Befehlszeile starten und ein entsperrtes Laufwerk erhalten. Für stärkeren Schutz richte manuell eine PIN ein: `sudo systemd-cryptenroll --tpm2-device=auto --tpm2-pcrs=7 --tpm2-with-pin=yes <device>`.
- **Initramfs.** Der busybox-Hook `encrypt` kann keine TPM2-Token verwenden. Solange er eingerichtet ist, wird die Registrierung abgelehnt. Der Wechsel zu `systemd` und `sd-encrypt` in `HOOKS` (mit `rd.luks.name=<LUKS-UUID>=root` statt `cryptdevice=` in der Kernel-Befehlszeile oder mit `/etc/crypttab.initramfs`) ist eine startkritische Änderung, die Eitr dir überlässt. Nimm die Änderung vor, führe `sudo mkinitcpio -P` aus und aktualisiere den Starteintrag. Bestätige einen erfolgreichen Start mit Passphrase, **bevor** du das TPM registrierst.

Entsperrt das TPM nicht mehr (Firmware- oder Secure-Boot-Änderung, TPM-Zurücksetzung), erscheint die Passphrasenabfrage wie zuvor. Gib die Passphrase ein, entferne die Registrierung und richte sie erneut ein. Zum vollständigen Rückgängigmachen verwende die Aktion zum Entfernen der TPM-Entsperrung oder eine funktionierende Shell:

```sh
sudo systemd-cryptenroll /dev/<luks-partition>            # list slots
sudo systemd-cryptenroll --wipe-slot=tpm2 /dev/<luks-partition>
```

## Werkseinstellungen

Mit der Eitr-ISO installierte Rechner behalten außerdem einen schreibgeschützten Wiederherstellungspunkt der ersten Anmeldung außerhalb von Snapper. Walker → System → Instandhaltung → Werkseinstellungen kehrt dorthin zurück, wahlweise mit oder ohne Dateien der persönlichen Ordner. Siehe [FACTORY-RESET.md](FACTORY-RESET.md).

## Wiederherstellungspunkte prüfen

Verwende Walker → System → Instandhaltung → Snapshots oder diese rein lesenden Prüfungen:

```sh
sudo snapper -c root list
findmnt -o TARGET,SOURCE,FSTYPE / /boot /efi
sudo du -sh /var/lib/eitr/boot-backups
```

Fällt der Desktop aus, startet das System aber noch, wechsle zu einer Textkonsole oder verwende eine selbst eingerichtete SSH-Verbindung. Startet es nicht, verwende die offizielle Arch-Installations-ISO und hänge das Btrfs-Dateisystem ein. Ermittle vor jeder Änderung das richtige Laufwerk, die Verschlüsselungszuordnung, das Root-Subvolume, die Snapshot-Nummer und den EFI-Einhängepunkt. Übernimm Befehle anderer Rechner nicht ungeprüft.

## Snapshots des persönlichen Ordners

Standardmäßig ausgeschaltet. **System > Instandhaltung > Momentaufnahmen > Snapshots des persönlichen Ordners** aktiviert sie nach Rückfrage; Ausschalten löscht sie. Snappers Konfiguration `home` behält dann einen Snapshot von `/home` pro Stunde für einen Tag und einen pro Tag für eine Woche. Sinkt der freie Speicher unter 20 %, werden die ältesten gelöscht.

Caches, `~/Downloads`, VM-Laufwerksordner (`~/.local/share/libvirt/images`, GNOME Boxes, `~/VirtualBox VMs`) und die Steam-Bibliothek bleiben ausgeschlossen. Beim nächsten Start, vor jeder Anmeldung, wandelt `eitr-home-exclusions.service` sie in verschachtelte Btrfs-Subvolumes um, die Home-Snapshots nicht erfassen. Dateien bleiben mittels Reflinks erhalten; das Verschieben benötigt keinen zusätzlichen Speicher. Die Variante Eigene Dateien behalten übernimmt diese Subvolumes in das wiederhergestellte Home-Dateisystem: versteckte in den Ordner "Settings before reset"; Caches werden verworfen. Kann eines nicht verschoben werden, bleibt das vorherige Home-Dateisystem zur Prüfung erhalten, statt gelöscht zu werden.

**Momentaufnahmen > Wiederherstellen einer Datei oder eines Ordners** (oder `eitr restore PATH`) listet Snapshots auf, die den Pfad enthalten, und kopiert die gewählte Version neben die aktuelle als `NAME (restored DATE)`. War sie gelöscht, wird sie am ursprünglichen Ort wiederhergestellt. Nichts wird überschrieben.

## Änderungen je Aktualisierung

Prüfe vor einer Rücknahme, was du rückgängig machen würdest. **System > Instandhaltung > Momentaufnahmen > Was jedes Update geändert hat** (oder `eitr snapshots changes`) listet jedes Vorher/Nachher-Paar mit der Anzahl aktualisierter, herabgestufter, installierter und entfernter Pakete auf. `eitr snapshots changes <before number>` zeigt jedes Paket einer Aktualisierung mit alter und neuer Version. Verglichen werden die Paketdatenbanken beider Snapshots. Fehlt der Nachher-Snapshot noch, wird mit dem laufenden System verglichen.

## Einen älteren Snapshot starten

Bei GRUB oder Limine kann das Startmenü schreibgeschützte Snapper-Snapshots auflisten. So lassen sich fehlerhafte Aktualisierungen ohne externes Startmedium prüfen und zurücknehmen. Die Installation bietet dies erst nach Eingabe von `yes` an. Auf einem vorhandenen System führe `bash distro/bootloader/setup.sh` aus; `--check` zeigt nur den Status. Prüfe das Ergebnis über Walker → System → Instandhaltung → Snapshots → Status startfähiger Snapshots oder mit `sudo /usr/lib/eitr/eitr-system snapshots-boot-status`.

| Bootloader | Integration | Pakete (`distro/bootloader/`) |
|---|---|---|
| GRUB | `grub-btrfsd.service` erstellt das Untermenü "Arch Linux snapshots" neu, wenn Snapper Snapshots hinzufügt oder entfernt | `grub-btrfs`, `inotify-tools` (offiziell) |
| Limine | `limine-snapper-sync.service` fügt Snapshot-Einträge in `limine.conf` ein | `limine-snapper-sync`, `limine-mkinitcpio-hook` (AUR) |
| systemd-boot | **Nicht unterstützt.** Lädt Kernel nur von der EFI/XBOOTLDR-Partition und kann Btrfs-Snapshots nicht öffnen | Verwende das Verfahren mit externem Startmedium unten |

Die Erkennung liest die GRUB-, Limine- und systemd-boot-Dateien unter `/boot`, `/efi` und `/boot/efi`. Sind mehrere Bootloader eingerichtet, etwa alte systemd-boot-Dateien neben GRUB, wird die Einrichtung abgelehnt, statt zu raten. Entferne veraltete Dateien oder richte Einträge manuell ein. Zuerst werden `grub.cfg`/`limine.conf` nach `/var/lib/eitr/boot-config-backups/<timestamp>/` kopiert und der Dienst für den nächsten Start aktiviert:

- **GRUB:** Die Einrichtung führt einmal `grub-mkconfig -o /boot/grub/grub.cfg` aus. Liegt `/boot` auf einer getrennten Partition, starten Snapshot-Einträge den *aktuellen* Kernel. Stelle nach einer Kernel-Aktualisierung auch das passende Startdateiarchiv wieder her (unten).
- **Limine:** `limine-snapper-sync` verwaltet Einträge von `limine-entry-tool` (aus `limine-mkinitcpio-hook`) und hält Kopien der Kernel aller Snapshots auf der EFI-Partition. Diese benötigt daher Platz; das Projekt empfiehlt 4 GiB. Prüfe `/etc/default/limine` (`SNAPPER_CONFIG_NAME="root"`, bei fehlender Erkennung auch `ESP_PATH`), führe `sudo limine-update` aus, prüfe das Menü und starte dann `sudo systemctl start limine-snapper-sync.service`. Eitr führt `limine-update` nicht für dich aus, da es das Startmenü neu schreibt.

Zum Rückgängigmachen deaktiviere den Dienst und kopiere die Sicherung zurück, etwa mit `sudo systemctl disable grub-btrfsd.service` und `sudo cp /var/lib/eitr/boot-config-backups/<timestamp>/grub.cfg /boot/grub/grub.cfg`.

### Schreibgeschützte Snapshots

Snapper-Snapshots sind schreibgeschützt. Ein direkt gestarteter Snapshot kann `/var` nicht beschreiben. Deshalb können SDDM und andere Dienste ausfallen. Melde dich an einer Textkonsole (Ctrl+Alt+F3) an, falls die grafische Anmeldung nicht startet. Eine Initramfs-Überlagerung erlaubt Schreibzugriffe im RAM; Änderungen verschwinden beim Neustart. Eitr bearbeitet `HOOKS` nicht. Ergänze die Überlagerung und regeneriere das initramfs selbst; nur danach erstellte Snapshots enthalten den Hook:

- GRUB: Hänge `grub-btrfs-overlayfs` an `HOOKS=(...)` in `/etc/mkinitcpio.conf` an und führe `sudo mkinitcpio -P` aus.
- Limine: Ergänze `btrfs-overlayfs` nach `filesystems` (oder `sd-btrfs-overlayfs` bei systemd-Hooks) und führe `sudo limine-update` aus.

### Dauerhaft zurücksetzen

1. Wähle den neuesten Snapshot "before package upgrade" in der Snapshot-Liste des Startmenüs und bestätige, dass das System darin funktioniert.
2. **Limine:** Führe `sudo limine-snapper-restore` aus und wähle den Snapshot. Die Wiederherstellung verwendet die konfigurierte Methode `RESTORE_METHOD` und fügt einen Sicherungseintrag für das ersetzte System hinzu. Damit lässt sich die Wiederherstellung selbst über das Startmenü rückgängig machen.
3. **GRUB:** `snapper rollback` funktioniert nur, wenn Root über das Btrfs-Standard-Subvolume eingehängt ist. Arch verwendet meist `rootflags=subvol=@` (prüfe `findmnt -no OPTIONS /` und `/etc/fstab`), sodass Rollback wirkungslos wäre. Ersetze das Root-Subvolume von einem externen Startmedium aus, nachdem du die Subvolumes auf oberster Dateisystemebene geprüft hast. Das folgende Beispiel gilt **nur** für Eitrs geführte Installation, bei der Snapper das verschachtelte Subvolume `@/.snapshots` angelegt hat. Andere Anordnungen benötigen ihre tatsächlichen Pfade:

   ```sh
   sudo mount -o subvolid=5 /dev/<root-or-mapper> /mnt
   sudo mv /mnt/@ /mnt/@.broken
   sudo btrfs subvolume snapshot /mnt/@.broken/.snapshots/<number>/snapshot /mnt/@
   # A Btrfs snapshot does not include nested subvolumes. Keep the original
   # Snapper store in the restored root instead of deleting it with @.broken.
   sudo rmdir /mnt/@/.snapshots
   sudo mv /mnt/@.broken/.snapshots /mnt/@/.snapshots
   ```

   Scheitert ein Befehl, halte an und prüfe die Lage. Lösche das erhaltene Root-Subvolume nicht. Prüfe vor dem Fortfahren den Snapshot-Speicher unter dem wiederhergestellten Root-Dateisystem und dessen fstab. Ist `/boot` getrennt, stelle das passende Archiv unter `/var/lib/eitr/boot-backups/<number>/` wieder her. Starte über den normalen Eintrag neu, führe `sudo grub-mkconfig -o /boot/grub/grub.cfg` aus und lösche `@.broken` mit `sudo btrfs subvolume delete` erst nach Prüfung des wiederhergestellten Systems.

## Sicher von einem externen Startmedium wiederherstellen

1. Sichere benötigte neuere Dateien. Hänge die oberste Btrfs-Dateisystemebene ein und prüfe die Subvolumes. Finde das Subvolume `snapshot` des gewählten Snapshots. Die Pfade hängen vom Einhängepunkt von `.snapshots` ab.
2. Erhalte das fehlgeschlagene Root-Subvolume durch Umbenennen. Erstelle einen **beschreibbaren Btrfs-Snapshot** des gewählten Wiederherstellungspunkts am ursprünglichen Root-Subvolume-Pfad, passend zu rootflags und fstab des installierten Bootloaders.
3. Hänge dieses wiederhergestellte Root-Dateisystem und seine tatsächlichen Start-/EFI-Partitionen ein. Stelle passende Startdateiarchive wieder her, falls Kernel, initramfs oder Bootloader geändert wurden. Archive müssen zum gewählten Root-Snapshot passen. Mische niemals einen neueren Kernel mit älteren Modulen.
4. Prüfe fstab und Bootloader-Konfiguration. Regeneriere bei Bedarf initramfs oder repariere Starteinträge über `arch-chroot`, passend zu diesem Rechner. Starte erst neu, wenn Root- und Startdateien zusammenpassen.

Dies ist ein manuelles, von der Laufwerksanordnung abhängiges Verfahren, **keine überprüfte Ein-Klick-Rollback-Implementierung**. Snappers Befehl `rollback` allein reicht für beliebige Arch-Subvolume-/Bootloader-Anordnungen nicht aus. Die genannten GRUB- und Limine-Snapshot-Einträge benötigen weiterhin Prüfung auf echter Hardware, bevor automatische Wiederherstellung zugesichert werden kann.

Quellen: [grub-btrfs](https://github.com/Antynea/grub-btrfs), [limine-snapper-sync](https://gitlab.com/Zesko/limine-snapper-sync), [Snapper-Wiederherstellungskonzepte](https://documentation.suse.com/sles/15-SP6/html/SLES-all/cha-snapper.html), [Arch-Installationsanleitung](https://wiki.archlinux.org/title/Installation_guide).
