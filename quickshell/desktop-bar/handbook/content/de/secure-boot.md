# Secure Boot mit sbctl

Eitr dokumentiert Secure Boot, **registriert aber niemals Schlüssel und signiert keine Dateien für dich**. Ein Fehler kann dazu führen, dass der Rechner nicht mehr startet oder kein Bild zeigt. Führe diese Schritte deshalb von Hand aus, auf einem Rechner, dessen Firmware-Einstellungen du erreichen kannst. Halte deine Passphrase der Laufwerksverschlüsselung und die [Wiederherstellungsanleitung](RECOVERY.md) bereit. Diese Anleitung wurde noch nicht auf Eitr-Testhardware überprüft.

## Bevor du anfängst

- Nur UEFI-Start. Kläre, wie du die Firmware-Einstellungen öffnest (oft F2, Del oder F12), und lege ein Firmware-Administratorpasswort fest. Sonst kann jeder Secure Boot wieder ausschalten.
- Wenn die TPM-Laufwerksentsperrung eingerichtet ist, halte die Passphrase bereit: Die Schlüsselregistrierung ändert PCR 7 des TPM. Beim nächsten Start wird die Passphrase einmal benötigt. Richte anschließend die TPM-Entsperrung erneut ein (Sicherheit → TPM-Laufwerksentsperrung: entfernen, dann erneut registrieren).
- Versetze Secure Boot in den Firmware-Einstellungen in **Setup Mode** (oft "Clear keys" oder "Reset to Setup Mode"). Lösche keine Schlüssel, die du nicht wiederherstellen kannst. Die meisten Firmwares bieten "Restore factory keys" an.

## Vorgehen mit sbctl

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s` speichert die Datei in der sbctl-Datenbank. Der Pacman-Hook von sbctl signiert registrierte Dateien nach Kernel- und Bootloader-Aktualisierungen erneut. Führe nach jeder Änderung `sudo sbctl verify` aus. Aktiviere anschließend Secure Boot in der Firmware und starte neu. Sichere `/var/lib/sbctl` offline und vertraulich: Dort liegen die Signaturschlüssel. Kopiere diese niemals in dieses Repository.

## Risiken

- **Option ROMs und Herstellerschlüssel.** Grafikkarten, NVMe-Laufwerke und Netzwerkkarten führen häufig Firmware (Option ROMs) aus, die von Microsofts UEFI-Zertifizierungsstelle signiert ist. Registrierst du nur eigene Schlüssel ohne `-m`, kann die Firmware diese Komponenten ablehnen: kein Bild, kein Startlaufwerk und auf manchen Laptops kein Zugang mehr zu den Firmware-Einstellungen. Behalte `-m` bei, sofern du nicht sicher weißt, dass deine Hardware keine solche Firmware verwendet. Alternativ kann `sbctl enroll-keys --tpm-eventlog` die Hashes der beim aktuellen Start verwendeten Option ROMs hinzufügen. Diese ändern sich jedoch bei Hardware- oder Firmware-Aktualisierungen.
- **Unsignierte Dateien.** Jede EFI-Binärdatei im Startpfad muss mit deinen Schlüsseln signiert sein. Eine übersehene Datei verhindert den Start. Deaktiviere Secure Boot in der Firmware, um den Zugriff wiederherzustellen.
- **Dual-Boot.** Windows startet nur weiter, wenn du `-m` verwendest.

## Bootloader und Snapshot-Einträge

- **GRUB:** Installiere GRUB mit `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock` neu. Signiere anschließend die neue Datei `grubx64.efi` und die Kernel unter `/boot`. In dieser Konfiguration prüft GRUB keine Kernel-Signaturen. Die grub-btrfs-Snapshot-Einträge starten weiterhin, aber der Schutz umfasst die GRUB-Binärdatei statt jedes einzelnen Kernels. Führe nach GRUB-Aktualisierungen, die das Image ändern, `grub-install` und `sbctl sign` erneut aus.
- **Limine:** Signiere die Limine-EFI-Binärdatei (`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI` oder den tatsächlichen Installationspfad). Limine schützt seine Konfiguration und die Kernel mit Hashes statt mit Signaturen. Wenn du den Konfigurationshash in der Binärdatei registrierst (`limine enroll-config`), muss diese bei jeder Änderung an `limine.conf` erneut registriert und signiert werden, auch bei jedem neuen Snapshot-Eintrag von limine-snapper-sync. Prüfe vor dem Aktivieren von Secure Boot, dass deine Einstellungen für `limine-mkinitcpio-hook` dies erledigen (bei installiertem sbctl wird es verwendet). Sonst lehnt der Bootloader nach der nächsten Snapshot-Synchronisierung sein Menü ab.
- **systemd-boot:** Signiere `systemd-bootx64.efi` und die geladenen Kernel oder Unified Kernel Images. Snapshot-Starteinträge werden nicht unterstützt.
- Snapshot-Einträge für ältere Kernel müssen ebenfalls die Prüfungen des Bootloaders bestehen. Starte nach dem Aktivieren von Secure Boot einmal über einen Snapshot-Eintrag, um dessen Funktion zu bestätigen, bevor du ihn brauchst.

## Rückgängig machen

1. Öffne die Firmware-Einstellungen und deaktiviere Secure Boot. Alternativ stellt "Restore factory keys" den Schlüsselsatz des Herstellers wieder her. Das installierte System startet mit ausgeschaltetem Secure Boot weiterhin.
2. Optional entferne registrierte Dateien mit `sudo sbctl remove-file <file>` aus der sbctl-Datenbank. Die Signaturen in den Dateien selbst sind unbedenklich.
3. Wurde die TPM-Entsperrung bei eingeschaltetem Secure Boot eingerichtet, ändert sich PCR 7 erneut. Gib die Passphrase einmal ein und richte die Entsperrung erneut ein.

Quellen: [sbctl](https://github.com/Foxboron/sbctl), [Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
