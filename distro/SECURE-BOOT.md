# Secure Boot with sbctl

Eitr documents Secure Boot but **never enrolls keys or signs files for you**.
A mistake here can leave a machine that refuses to boot or shows no picture, so
follow these steps by hand, on a machine you can reach firmware setup on, with
your disk passphrase and [recovery instructions](RECOVERY.md) at hand. Nothing in
this guide has been verified on Eitr test hardware yet.

## Before you start

- UEFI boot only. Note how to open firmware setup (often F2, Del or F12) and set a
  firmware administrator password, or anyone can turn Secure Boot off again.
- If TPM disk unlock is enrolled, keep the passphrase ready: enrolling keys
  changes TPM PCR 7, so the next boot asks for it once. Re-enroll TPM unlock
  afterwards (Security → TPM Disk Unlock: remove, then enroll).
- In firmware setup, put Secure Boot into **Setup Mode** (often "Clear keys" or
  "Reset to Setup Mode"). Do not delete keys you cannot restore; most firmware has
  "Restore factory keys".

## sbctl workflow

```sh
sudo pacman -S --needed sbctl
sbctl status                      # must report "Setup Mode: Enabled"
sudo sbctl create-keys            # private keys stay in /var/lib/sbctl (root-only)
sudo sbctl enroll-keys -m         # -m keeps Microsoft's keys; see risks below
sudo sbctl verify                 # lists EFI files and whether they are signed
sudo sbctl sign -s <file>         # once per unsigned file listed by verify
```

`sign -s` saves the file in sbctl's database; sbctl's pacman hook re-signs saved
files after kernel and boot loader updates. Run `sudo sbctl verify` after each
change, then enable Secure Boot in firmware and reboot. Back up `/var/lib/sbctl`
offline and privately: it holds signing keys. Never copy it into this repository.

## Risks

- **Option ROMs and vendor keys.** Graphics cards, NVMe drives and network cards
  often run firmware (Option ROMs) signed by Microsoft's UEFI CA. Enrolling only
  your own keys without `-m` can make the firmware refuse them: no display, no
  boot disk, and on some laptops no way back into firmware setup. Keep `-m`
  unless you know the hardware has no such firmware. `sbctl enroll-keys
  --tpm-eventlog` can add the hashes of the Option ROMs used at this boot
  instead, but they change with hardware or firmware updates.
- **Unsigned files.** Every EFI binary in the boot path must be signed with your
  keys. A missed file stops the boot; disable Secure Boot in firmware to recover.
- **Dual boot.** Windows keeps booting only with `-m`.

## Boot loaders and snapshot entries

- **GRUB:** reinstall with
  `sudo grub-install --target=x86_64-efi --efi-directory=<esp> --bootloader-id=GRUB --modules="tpm" --disable-shim-lock`,
  then sign the new `grubx64.efi` and the kernels in `/boot`. In this setup
  GRUB does not check kernel signatures, so grub-btrfs snapshot entries keep
  booting, but the protection covers the GRUB binary rather than every kernel.
  Re-run `grub-install` and `sbctl sign` after GRUB updates that change the image.
- **Limine:** sign the Limine EFI binary (`sbctl sign -s <esp>/EFI/limine/BOOTX64.EFI`
  or wherever it is installed). Limine protects its config and kernels with
  hashes rather than signatures. If you enroll the config hash into the binary
  (`limine enroll-config`), every change to `limine.conf`, including each new
  snapshot entry from limine-snapper-sync, must re-enroll and re-sign it. Confirm
  that your `limine-mkinitcpio-hook` settings do this (it uses sbctl when
  installed) before enabling Secure Boot, or the next snapshot sync makes the
  loader refuse its menu.
- **systemd-boot:** sign `systemd-bootx64.efi` and the kernels or unified kernel
  images it loads. It does not support snapshot boot entries.
- Snapshot entries for older kernels must still pass your loader's checks. After
  enabling Secure Boot, boot one snapshot entry once to confirm it works before
  you need it.

## Undo

1. Enter firmware setup and disable Secure Boot, or choose "Restore factory keys"
   to return to the vendor key set. The installed system keeps booting with
   Secure Boot off.
2. Optionally remove saved files from sbctl's database with
   `sudo sbctl remove-file <file>`; signatures on the files themselves are harmless.
3. If TPM unlock was enrolled while Secure Boot was on, PCR 7 changes again:
   enter the passphrase once and re-enroll.

References: [sbctl](https://github.com/Foxboron/sbctl),
[Arch Wiki: Secure Boot](https://wiki.archlinux.org/title/Unified_Extensible_Firmware_Interface/Secure_Boot).
