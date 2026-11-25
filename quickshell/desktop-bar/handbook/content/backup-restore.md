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
   - **Git accounts** (opt-in secret, off by default): `eitr/git-accounts.json`, its managed includes under `eitr/git-accounts`, `~/.gitconfig`, the SSH keys each account names (private key and `.pub`, kept `0600`), `~/.ssh/config`, `~/.ssh/known_hosts`, and GPG secret keys exported with `gpg --export-secret-keys --armor` (GPG prompts for its own key passphrase).
   - **Cloud accounts** (opt-in secret, off by default): `~/.aws`, `~/.config/gcloud`, `~/.azure`, `~/.kube` and Eitr's cloud labels (`eitr/cloud-contexts.json`, `eitr/cloud-navigation.json`).
   - **WiFi networks** (opt-in secret, off by default): saved iwd (`/var/lib/iwd/*.psk`, `*.8021x`, `*.open`) and NetworkManager (`/etc/NetworkManager/system-connections/*.nmconnection`) profiles exported through `/usr/lib/eitr/eitr-network` behind `pkexec`.
2. Review or untick individual app-setting folders and installed apps (searchable and grouped by source).
3. Pick a destination. External drives appear before `~/Backups`. Saving only on the same disk shows a warning; missing free space refuses early before writing anything.
4. Enter your passphrase twice. Passphrases never appear in command arguments, environment variables or saved files.
5. Check the summary on the **Review** screen (which warns whenever secret categories and secret entries are included) and press **Enter** to write the archive atomically, or **Esc** to cancel without creating files.

### What stays out

- Browser profiles, browser caches and lock/socket/temporary files.
- Shipped system code, default files and regenerated theme outputs (rebuilt after restore).
- Login keyrings, Git CLI tokens (`~/.config/gh`, `eitr/git-accounts/cli`), and short-lived cloud session caches: AWS SSO and CLI caches (`~/.aws/sso/cache`, `~/.aws/cli/cache`), gcloud token and credential databases (`~/.config/gcloud/access_tokens.db*`, `~/.config/gcloud/credentials.db*`, `legacy_credentials`, `logs`), Azure token caches (`~/.azure/msal_token_cache*`, `accessTokens.json`, `msal_http_cache*`, `logs`, `telemetry`, `commands`) and Kubernetes discovery caches (`~/.kube/cache`, `~/.kube/http-cache`).

## Restore from a backup

1. Pick an archive (from connected drives, `~/Backups`, the last backup location or a custom path) and enter its passphrase.
2. Eitr reads `manifest.json` first and lets you untick categories, folders, app-setting dirs or individual apps before changing anything on disk.
3. Confirm the **Review** step. Replaced files are copied to `~/.local/state/eitr/restore-backups/<id>/` with a journal before replacement.
4. Packages reinstall in order: available official packages in one `pacman` transaction (missing packages are skipped and listed), AUR packages one by one via `yay` continuing past individual failures, then Flatpaks, and finally Eitr plugins and Store themes/wallpapers/lockscreens **through normal review approval** (never silently).
5. Non-secret files restore first, and secret categories restore last: SSH and GPG directories keep `0700` permissions while SSH keys (private and `.pub`), GPG files and cloud configs keep `0600`, GPG keys import via `gpg --import`, and WiFi profiles import as `root:root` `0600` via `/usr/lib/eitr/eitr-network` behind `pkexec`.
6. Themes and generated configs rebuild without discarding restored per-display wallpapers, and Hyprland reloads if active. Sign back into browsers and short-lived cloud/Git CLI sessions (`gh`, `gcloud`, `aws`, `az`).

## Undo a restore

If a restore overwrote files you want back, run:

```sh
eitr backup undo <id>
```

Find `<id>` in **Settings > System > Backup and Restore** or with `eitr-backup status`. Undo puts replaced files (including secret files, GPG keyring files and WiFi profiles) back, removes newly added files and regenerates desktop theme outputs.
Restore checks for target conflicts, including directories in place of files and
symlinked parent folders, before replacing files. If it stops partway through,
look for the undo point in the same list.

## CLI reference

```sh
eitr backup status --json
eitr backup inspect PATH/TO/ARCHIVE.eitrbackup
eitr backup create -d /mnt/usb
eitr backup restore PATH/TO/ARCHIVE.eitrbackup
eitr backup undo <id>
```

Keep passphrases interactive (prompted on `/dev/tty` with echo off) or pass `--passphrase-fd N`. Newer unsupported archive format versions fail clearly before altering any file.
