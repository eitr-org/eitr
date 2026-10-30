# Factory reset

Computers installed with the Eitr ISO can return to the state of their first
login from Walker → Settings → System → Maintenance → Factory Reset. The reset is local: it restores a
read-only copy saved on the same disk. It is not a backup and not secure
erasure; a failed disk loses the computer and its restore point together.

## The restore point

The guided installer's last step runs `eitr-factory-reset capture`, which saves
the finished installation under the top-level Btrfs subvolume `@eitr-factory`:

| Path | Contents |
|---|---|
| `root` | read-only snapshot of `@` (system, accounts, settings) |
| `home` | read-only snapshot of `@home` (the seeded user folders) |
| `boot.tar` | the EFI partition's files: Limine, its menu, kernel and initramfs |
| `manifest.json` | creation time, filesystem and EFI partition UUIDs, accounts, `boot.tar` SHA-256 |

`@eitr-factory` itself is then made read-only. It lives beside `@`, not in
`@/.snapshots`, so Snapper never lists it or cleans it up, and Walker offers no
way to delete it. Root can still delete it, and formatting or disk failure
destroys it. Its snapshots share data with the running system, so it costs
little space at first and grows as updates replace the original files.

`capture` refuses to replace an existing restore point. Installations made
without the ISO have none, and Factory Reset reports that.

## The two resets

**Erase Everything** returns the computer to its first login: apps installed
since, changed settings, accounts added later and every file in the home
folders are gone.

**Keep My Files** restores the system, apps and settings, and keeps the home
folders. For each account in the restore point, its current hidden entries
(`~/.config`, `~/.local`, `~/.ssh`, browser profiles and so on) move into a
visible folder named `Settings before reset <date time>` in that home folder,
then the restore point's hidden entries are copied back. Nothing in a home
folder is deleted. Accounts added after installation are removed with the
system, but their home folders stay under `/home`.

Both resets keep the disk encryption passphrase (the LUKS header is never
touched) and the current password of every account that the restore point
also has. A TPM unlock slot stays in the LUKS header, but the restored
initramfs asks for the passphrase until TPM unlock is set up again. Logs
(`@log`) and the package cache (`@pkg`) are kept.

## Confirmation

Walker's action shows two separate warnings in a terminal:

1. What the chosen reset removes and keeps. Only `y` or `yes` continues; Enter
   cancels.
2. Which computer is reset, that it restarts immediately and that unsaved work
   is lost. Typing `RESET MY COMPUTER` exactly is required.

The root-owned helper (`/usr/lib/eitr/eitr-factory-reset`) checks the typed
phrase again and validates before changing anything:

- `/` is subvolume `@` and `/home` is `@home` on one Btrfs filesystem, and
  `/boot` is the FAT EFI partition.
- The restore point and its snapshots are still read-only, its manifest names
  this filesystem and EFI partition, and `boot.tar` matches its SHA-256.
- Secure Boot is off: restored boot files are not signed with enrolled keys.
- No earlier reset is still pending.

`sudo /usr/lib/eitr/eitr-factory-reset status` (Walker → Reset Status) runs the
same checks and changes nothing.

## How a reset runs

The running root and home are never written. Under a new top-level subvolume
`@eitr-reset-previous` the helper:

1. Creates a writable snapshot of the restore point's root, recreates Snapper's
   `.snapshots` subvolume in it, copies in the current passwords and enables
   `eitr-factory-reset-finish.service` there.
2. Creates the new home: a writable snapshot of the restore point's home
   (Erase Everything), or a snapshot of the current `@home` with the settings
   moved aside as described above (Keep My Files).
3. Archives the current EFI partition files to `boot.tar` and unpacks the
   restore point's archive for copying.

A failure up to this point deletes `@eitr-reset-previous` and leaves the
computer unchanged. The helper then copies the restored boot files onto the EFI
partition (on failure it restores the archive it just made), renames `@` and
`@home` to `old@` and `old@home` inside `@eitr-reset-previous`, renames the
prepared subvolumes to `@` and `@home`, and restarts. If a rename fails, the
earlier names and boot files are restored.

On the next boot, `eitr-factory-reset-finish.service` confirms the running root
is the restored one, deletes `@eitr-reset-previous` (including the old
system's Snapper snapshots) and disables itself.

## Recovering an interrupted reset

Power loss during the few renames can leave `@` or `@home` missing. Boot the
Eitr ISO, press Escape to leave the wizard, unlock the disk if encrypted
(`cryptsetup open /dev/<partition> root`), and inspect:

```sh
mount -o subvolid=5 /dev/mapper/root /mnt   # or the Btrfs partition itself
btrfs subvolume list /mnt
cat /mnt/@eitr-reset-previous/manifest.json
```

- `@` and `@home` both exist and `@eitr-reset-previous/new-root` is gone: the
  swap finished. Reboot; the finish service cleans up.
- `@` or `@home` is missing: rename the matching `@eitr-reset-previous/old@`
  or `old@home` back (`mv /mnt/@eitr-reset-previous/old@ /mnt/@`), then extract
  `@eitr-reset-previous/boot.tar` onto the EFI partition to match the old
  system, and reboot.

Delete `@eitr-reset-previous` with `btrfs subvolume delete --recursive` only
after the system starts correctly; until then it holds the previous system.

## Verification

Tested in UEFI VMs without a network (see
[LINUX-VM-TESTING.md](LINUX-VM-TESTING.md)): both resets on an unencrypted
erase install, and both on a LUKS2 install next to a Windows-shaped disk, each
followed by a successful boot, login and the finish service's cleanup. Not yet
tested: real hardware, power loss during the swap, and restore point
retention through online system updates (the VMs had no network).
