# Backup and Restore

Move your desktop settings, chosen personal folders and installed app lists to another PC or a fresh Eitr installation in one encrypted `.eitrbackup` file.

Snapshots under [Recovery & Snapshots](handbook:recovery) stay on the same disk for rollback after an update. Backup and Restore writes a portable archive compressed with `zstd` and encrypted with your `age` passphrase so you can store it on an external drive or upload it off the machine.

## Open Backup and Restore

- **Settings**: press **SUPER + ,** and open **System > Backup and Restore**.
- **Walker**: press **SUPER + F**, then choose **Settings > System > Backup and Restore**.
- **Terminal**: run `eitr backup` (or `eitr-backup wizard`).

## Create a backup

1. Choose which categories to include:
   - **Eitr settings**: desktop preferences, deliberate overrides under `~/.config/eitr/overrides`, your own themes, wallpapers and lockscreens.
   - **App settings**: non-Eitr folders under `~/.config` (excluding browser profiles and caches).
   - **Personal folders**: top-level folders in `$HOME`, unselected by default so you choose what fits, plus **Add folder…** for subfolders inside `$HOME`. Sizes count in the background while you pick.
   - **Installed apps**: lists of explicit official Arch packages, AUR packages, Flatpak apps, installed Eitr plugins and Store items beyond Eitr's base install.
   - **Machine setup**: off by default; hardware-local display and `hypr/local.lua` overrides for the same PC.
2. Review or untick individual app-setting folders and installed apps (searchable and grouped by source).
3. Pick a destination. External drives appear before `~/Backups`. Saving only on the same disk shows a warning; missing free space refuses early before writing anything.
4. Enter your passphrase twice. Passphrases never appear in command arguments, environment variables or saved files.
5. Check the summary on the **Review** screen and press **Enter** to write the archive atomically, or **Esc** to cancel without creating files.

### What stays out

- Browser profiles, browser caches and lock/socket/temporary files.
- Shipped system code, default files and regenerated theme outputs (rebuilt after restore).
- Account credentials stored outside user preferences: SSH keys, GPG keys, login keyrings, cloud CLIs (`~/.aws`, `~/.azure`, `~/.config/gcloud`, `~/.config/gh`) and saved Git/Wi-Fi account secrets.

## Restore from a backup

1. Pick an archive (from connected drives, `~/Backups`, the last backup location or a custom path) and enter its passphrase.
2. Eitr reads `manifest.json` first and lets you untick categories, folders, app-setting dirs or individual apps before changing anything on disk.
3. Confirm the **Review** step. Replaced files are copied to `~/.local/state/eitr/restore-backups/<id>/` with a journal before replacement.
4. Packages reinstall in order: available official packages in one `pacman` transaction (missing packages are skipped and listed), AUR packages one by one via `yay` continuing past individual failures, then Flatpaks, and finally Eitr plugins and Store themes/wallpapers/lockscreens **through normal review approval** (never silently).
5. Themes and generated configs rebuild without discarding restored per-display wallpapers, and Hyprland reloads if active.
6. After restore, sign back into browsers, cloud CLIs (`gh`, `gcloud`, `aws`, `az`) and any SSH/GPG keys kept outside the backup.

## Undo a restore

If a restore overwrote files you want back, run:

```sh
eitr backup undo <id>
```

Find `<id>` in **Settings > System > Backup and Restore** or with `eitr-backup status`. Undo puts replaced files back, removes newly added files and regenerates desktop theme outputs.

## CLI reference

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Keep passphrases interactive (prompted on `/dev/tty` with echo off) or pass `--passphrase-fd N`. Newer unsupported archive format versions fail clearly before altering any file.
