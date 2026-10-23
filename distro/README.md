# Eitr

This repository contains the complete desktop configuration and its installers.
`build-iso.sh` builds the Eitr installer ISO with an offline payload: its guided
install sets up the complete desktop, AUR packages included, without a network
(`download.eitr.info` serves the current one). `install.sh` installs onto an
existing Arch system instead. The live ISO is not a preinstalled graphical session.

## What is included

- Development > Git Accounts configures a default Git identity and folder
  overrides for GitHub/GitLab, with separate SSH keys and CLI profile logins.
  `github-cli` and `glab` are in the official manifest. Setup is opt-in: no
  identities, keys, remotes or global CLI accounts are changed by installation.
  `eitr-git cli ...` runs the provider CLI for the selected folder/default account;
  ordinary `gh`/`glab` remain unchanged. See the Handbook's Git Accounts chapter
  for confirmations, private token storage, backups and worktree limitations.

- `packages.txt`: official Arch packages for Hyprland, Quickshell, Walker's
  dependencies, theme switching, audio, networking, capture tools, fonts,
  LazyVim, AWS CLI, Docker, and the terminal.
- `apps.txt`: the remaining general applications from the current installation,
  including Firefox as the default browser. It includes Steam and other optional
  apps on purpose, for later review.
- `aur-packages.txt` and `aur-apps.txt`: AUR desktop and application packages,
  including Walker and Elephant. Packages EITR may not redistribute
  (`redistribution.json`: VS Code, 1Password, Chrome, Postman, Slack) never enter
  these lists; Walker → Install offers them instead.
- `local-packages.txt`: reviewed local recipes in `pkg/`. cmux TUI ships as
  `eitr-cmux-tui-bin`, using an official commit-pinned binary and SHA-256 checks.
  It installs `/usr/bin/cmux`, without editing shell profiles or installing Node,
  Rust or Zig. The payload builder includes it in the offline repository and
  installer transactions; rebuild the payload and ISO to ship changes.
  `less` is already included in `packages.txt` for terminal document viewing.
  The AUR `cmux-tui` is an unrelated serial-debugging program, not this app.
  When updating the recipe, review the upstream license and corresponding-source
  distribution requirements before publishing an ISO; the upstream release
  manifest's license label differs from its repository LICENSE.
- `hardware/`: detects CPU vendor and PCI display-controller IDs, then installs
  matching CPU microcode and 64-/32-bit GPU drivers. AMD and Intel use Mesa and
  their Vulkan drivers. Virtual GPUs use software Vulkan. NVIDIA needs an
  explicit driver choice because older cards require a different driver. If a
  non-default kernel (for example `linux-lts` or `linux-zen`) is installed,
  `nvidia-open-dkms` and headers for every installed kernel replace `nvidia-open`.
  A system battery (`BAT*`) or laptop DMI chassis adds `laptop.txt`
  (`power-profiles-daemon`); the installer enables it only when installed.
- Steam, GameMode, Gamescope, MangoHud, 32-bit graphics libraries, and
  `lib32-systemd` for Steam networking with systemd-networkd.
- FFmpeg, Qt Multimedia's FFmpeg backend, and GStreamer with base/good/bad/
  ugly/libav plugins for common audio and video formats, including MP4.
- Repository config directories: Quickshell bar/lockscreen, Hyprland, Walker,
  Elephant, themes and wallpapers, Neovim/LazyVim, and app styles. Quickshell
  owns notifications.
- `HOME_FILES`: files installed elsewhere under `$HOME`: Zsh, Powerlevel10k and
  `LS_COLORS`; the `~/.local/bin` Walker wrapper link, the selected lockscreen
  design. Quickshell starts with the desktop session and owns notifications.
  The installer does not copy credentials or account state.
- Yay is built from AUR if absent. AUR builds disable detached debug packages;
  SwayNC, CEF, and Walker/Mongosh debug packages are deliberately excluded.
  Quickshell owns notifications.
- Development languages, frameworks, JavaScript tools and AI CLIs are optional:
  Walker → Install → Development Languages / JavaScript Tools / AI CLIs.
  `software.json` records optional package recipes. Java uses SDKMAN
  with the latest available Oracle JDK LTS and Maven; Node uses NVM's latest LTS.
  Python remains a system dependency for desktop helpers; uv-managed development
  Python is optional. Rust uses rustup; Ruby/Rails uses mise; PHP/Composer,
  Elixir/Erlang and .NET use Arch packages. A separate mise option installs only
  the Arch package; shell activation is manual and may conflict with nvm/uv for
  the same runtime. No managers, development SDKs or AI
  CLIs are bootstrapped by default. Dependencies may still pull their own runtimes.
  Existing SDKs and account state on the owner's desktop are not uninstalled.
- Lazygit and Lazydocker are included from Arch's official repositories. Gaming
  includes Steam and the official NVIDIA GeForce NOW user Flatpak, installed
  from NVIDIA's signed remote. It requires a separate account and compatible
  hardware/network; it does not install NVIDIA GPU drivers on AMD/Intel systems.
- Snapper creates recovery points only through System Update on distro installs.
  Terminal commands `eitr update pacman|aur|full` intentionally do not request snapshots. Supported fresh installs require Btrfs
  root with `/usr`, `/etc`, and `/var/lib/pacman` inside that root subvolume.
  Boot/EFI archives are separate; see [recovery instructions](RECOVERY.md).
- `bootloader/`: optional Snapper snapshot boot entries. `setup.sh` detects
  GRUB (`grub-btrfs`) or Limine (AUR `limine-snapper-sync`), installs that
  loader's manifest and runs `eitr-system snapshots-boot-setup` only after typed
  confirmation. systemd-boot cannot boot snapshots and is refused.
- Security offers password changes, fingerprint enrollment, FIDO2-key enrollment,
  and separately confirmed optional authentication policy. Password fallback is
  preserved. Each policy change backs up the PAM files and can be undone with
  `eitr-system auth-restore`; see [recovery instructions](RECOVERY.md). Hardware support and real authentication still require testing.
  Security → TPM Disk Unlock adds (or removes) a PCR 7 TPM2 slot on a LUKS2
  root after a typed confirmation, offering a recovery key first and keeping the
  passphrase. It refuses the busybox `encrypt` initramfs hook and never runs
  from the installer.
  Secure Boot is documentation only: [SECURE-BOOT.md](SECURE-BOOT.md) (sbctl,
  Option ROM risks, GRUB/Limine snapshot entries, undo), bundled in
  Walker → Learn → EITR Handbook → Secure Boot.
- Laptops: Walker → System → Devices & Input → Battery Charge Limit runs
  `eitr-system battery-limit <60-100|off>`, which writes
  `charge_control_end_threshold` and installs `eitr-battery-limit.service` to
  restore it at boot and after resume. Desktops have no threshold and are refused.
- Direct helper dependencies include `lm_sensors` for hardware temperatures,
  `qrencode` for Wi-Fi sharing, and `desktop-file-utils` for launcher registration.
- Bruno, ngrok, kubectl, Helm, Minikube, printing packages (CUPS, HPLIP and
  System Config Printer), and Wacom input support are excluded from defaults.
  Existing installations are not uninstalled by changes to these manifests.

## Install on a new machine

For Linux/KVM, see the [temporary VM testing guide and coverage](LINUX-VM-TESTING.md).

For Apple Silicon Macs, follow the [temporary VM testing guide](MAC-VM-TESTING.md).
It uses x86_64 emulation, not a supported ARM port. Remove that guide and this
link once installation and release testing is complete.

1. Install a supported x86_64 Arch system with a Btrfs root, a normal user and sudo access.
   Choose partitioning, encryption, boot loader, locale, timezone and user name
   during the normal Arch install, or let the ISO's
   [guided install](#guided-install) erase one disk and install the complete
   desktop offline (it replaces steps 2 and 3). `install.sh` itself never
   formats disks. Do not run the installer on an existing configured desktop.
2. Enable `[multilib]` in `/etc/pacman.conf` and refresh pacman. Steam and
   `lib32-*` packages require it.
3. Install the preflight prerequisites with
   `sudo pacman -Syu --needed git base-devel python`. Clone this repository,
   run `bash distro/install.sh --check`, then run
   `bash distro/install.sh` as the new **non-root** user. `--check` lists every
   existing config, `~/.local` file, systemd user unit, or theme path that differs
   from this repo and stops; move those aside first. It never overwrites them.
   Paths the installer created are recorded in `~/.local/state/eitr/installed-paths`,
   so after a partial failure you can fix the cause and rerun it: finished steps
   are skipped. Existing Zsh files skip only the Oh My Zsh setup. `--check` also
   verifies that every manifest entry exists in the enabled repositories (AUR
   names once `yay` is available). It does not copy browser, Wi-Fi, SSH, AI,
   or 1Password credentials. The installer downloads official packages,
   builds `yay` from AUR, installs AUR apps, builds and installs the
   `eitr-desktop` package (see [Desktop package](#desktop-package-and-config-updates))
   and seeds your home from it with `eitr-config seed`, configures Snapper and System Update protection,
   and installs GeForce NOW. Development SDKs and AI CLIs are selected later
   from Walker rather than installed automatically. Audit the manifests and
   upstream installers before running them.
   On a supported NVIDIA Turing-or-newer system, review the GPU model first and
   use `DISTRO_NVIDIA_DRIVER=open bash distro/install.sh --check` followed by
   `DISTRO_NVIDIA_DRIVER=open bash distro/install.sh`. On a hybrid machine where
   only the Intel/AMD GPU should be configured, use `DISTRO_NVIDIA_DRIVER=skip`.
   Older NVIDIA cards need manual driver selection; the installer intentionally
   stops instead of guessing. If no supported GPU is detected, it also stops.
4. Review `/etc/systemd/network` and `/etc/resolv.conf`, then reboot. The
   installer enables iwd, networkd, resolved, Bluetooth, and SDDM for next
   boot; it does not restart those system services in the current session. If
   `/etc/resolv.conf` is a regular file, it warns instead of replacing it. The
   user nightlight timer is enabled immediately when a systemd user session
   exists; otherwise the installer prints the command to run after login. It
   configures Zsh as the login shell and installs the selected root-owned SDDM
   design. Docker and cronie are installed but not enabled; the installer prints
   the commands to enable them. Joining the `docker` group is root-equivalent.
5. Fresh installs start with Afterglow and Clockwork Tape; existing user selections
   are preserved. Hyprland's update popup is disabled in favor of Eitr's welcome.
   Sign into apps yourself. Open Walker and apply a theme once to generate
   all application-specific styles. LazyVim installs plugins at first Neovim
   launch. Check the SDDM theme on a spare/test system before using it as your
   only login path; the lockscreen README has recovery instructions.

### Monitors and machine-local overrides

The shared Hyprland config is generic: it reads each connected display's
preferred EDID mode (resolution and refresh rate) at login and positions outputs
automatically, rather than copying the original machine's output names and
resolutions. `preferred` is the safe default, not a guarantee of the highest
advertised Hz; the Display panel reports the active mode. The bar starts on the
largest active display until you pick another one in the Display panel.

Machine-specific settings live in two optional, Git-ignored files:

- `~/.config/hypr/local.lua`: a Lua chunk that runs after `hyprland.lua` and
  uses the same `hl.*` calls (`hl.monitor`, `hl.workspace_rule`, `hl.device`,
  `hl.env`, `hl.config`, ...). Its calls apply only if the whole file runs
  without error; otherwise the generic layout stays and a notification shows
  the error.
- `~/.config/hypr/preferred-outputs`: output names, one per line, that the bar
  prefers before the largest display. A choice saved from the Display panel
  (`~/.config/hypr/primary-display`) still wins.

`hypr/local.lua.example` and `hypr/preferred-outputs.example` hold the original
machine's layout (fixed modes, HDR, positions, workspace-to-monitor rules,
mouse tuning, and the HDMI-A-1/DP-3 bar preference).

**Owner machine migration:** older checkouts applied that layout unless
`hypr/portable.mode` existed; the marker is no longer read. On the original
machine, restore the layout once with:

```sh
cp hypr/local.lua.example ~/.config/hypr/local.lua
cp hypr/preferred-outputs.example ~/.config/hypr/preferred-outputs
hyprctl reload
```

A leftover `~/.config/hypr/portable.mode` on other machines is harmless and can
be deleted.

## Desktop package and config updates

`pkg/eitr-desktop/PKGBUILD` packages the desktop from this tree. A Git checkout
contributes only its committed `HEAD` (via `git archive`), so uncommitted and
ignored machine-local files never ship; the version is the release from
`release.json` plus the commit time and hash (see [RELEASES.md](RELEASES.md)).
It installs:

- the desktop code itself under `/usr/share/eitr` (bar, lockscreen, Walker and
  Elephant menus, Hyprland defaults, themes, generators), classified by
  `layout-manifest.json`, plus the small preference and loader defaults that
  `user-defaults.json` seeds into each home (see [CONFIG-LAYOUT.md](CONFIG-LAYOUT.md));
- launchers in `/usr/bin` (`eitr-shell`, `eitr-run`, `eitr-walker`,
  `eitr-session` and the Hyprland companions) and the package-owned SDDM login
  designs under `/usr/share/sddm/themes/desktop-lockscreen-*`;
- `software.json`, `installers.json`, `RECOVERY.md` and
  `system-update-policy.conf` in `/usr/share/eitr/`;
- the root helper as `/usr/lib/eitr/eitr-system` (earlier manual installs used
  `/usr/local/lib/eitr/eitr-system`, which callers still accept as a fallback);
- `eitr-config` in `/usr/bin` and the systemd user units in `/usr/lib/systemd/user`.

Theme wallpapers and previews ship separately in `eitr-artwork`
(`pkg/eitr-artwork/PKGBUILD`), a dependency of `eitr-desktop`. Its version is the
last commit that changed `themes/*/backgrounds`, `backgrounds-ultrawide`, `motion` or
`themes/*/preview.png`, so a
code update downloads only `eitr-desktop` and the artwork downloads again only
when it changes.

Its dependencies are the official `packages.txt` entries except `base`,
`base-devel`, `linux` and `linux-firmware`, which stay system choices (so
`linux-lts`/`linux-zen` systems are valid). `apps.txt`, hardware drivers and AUR
packages are not hard dependencies; the AUR desktop packages appear as optional
dependencies and `install.sh` installs them with `yay`. Build and install it as
your normal user from an up-to-date system:

```sh
(cd distro/pkg/eitr-artwork && makepkg --clean)
cd distro/pkg/eitr-desktop
makepkg --nodeps --clean   # pacman -U below resolves the official dependencies
sudo pacman -U ../eitr-artwork/eitr-artwork-*.pkg.tar.zst eitr-desktop-*.pkg.tar.zst
```

Packages only update files under `/usr`; your home is changed by `eitr-config`,
run as the desktop user:

- `eitr-config status` lists defaults that are new, outdated (unchanged by you),
  in conflict (changed by you and upstream), or differ without ever being seeded.
  `--all` also lists matching and locally modified files.
- `eitr-config seed` copies missing defaults and never overwrites anything.
  It records each copied file's checksum in
  `${XDG_STATE_HOME:-~/.local/state}/eitr/user-defaults-state.json`.
- `eitr-config update` seeds new defaults, replaces files you never edited, and
  writes `<file>.eitr-new` beside files you edited (like pacman's `.pacnew`).
  After merging one, `eitr-config resolve <file>` accepts it and removes the
  `.eitr-new` copy. Files you deleted stay deleted. `theme/current` is only
  seeded, because theme switches rewrite it. Both commands accept `--dry-run`.

`eitr-config` honours `XDG_CONFIG_HOME` and `XDG_STATE_HOME`. With
`--repo <checkout>` it compares against a checkout instead of the package.

Package updates replace the desktop code; preferences in `~/.config` are not
touched. At the next login `eitr-session` regenerates theme output once for the
new package version, keeping the previous files under
`~/.local/state/eitr/generated-backups`.

### Moving an existing desktop to the package layout

Desktops set up before the package layout run copies of the code from
`~/.config` and keep doing so until their user adopts the layout. Once, in order:

1. `bash distro/system/adopt-unowned-files.sh --check`, then the same with
   `--apply` as root. pacman refuses to install over files no package owns: the
   login designs the old login installer copied, and a network helper installed
   by hand from [NETWORKING.md](NETWORKING.md). The script archives exactly those
   under `/var/lib/eitr/unowned-file-backups` first.
2. `sudo pacman -U eitr-artwork-*.pkg.tar.zst eitr-desktop-*.pkg.tar.zst` (both built above), then, as the desktop user,
   `sudo /usr/bin/python3 -I /usr/share/eitr/quickshell/lockscreen/scripts/install-login.py`
   to point the login selector at the packaged helper. Adoption below also
   replaces old copies of the packaged user units in `~/.config/systemd/user`.
3. `eitr-config adopt-layout --dry-run`. It lists every legacy file to retire,
   files you added in those folders (kept), and blocks on any component you
   edited. For each, choose `--archive-component NAME` (back it up and use the
   package) or `--keep-component NAME` (keep your copy as an override; refused
   while it still calls code that adoption retires). Move personal shell lines to
   `~/.config/eitr/shell.local.zsh` and machine settings to `hypr/local.lua`.
4. `eitr-config adopt-layout --apply` with the same choices, then log out and
   back in. Backups and a journal go to `~/.local/state/eitr/layout-backups`;
   `eitr-config undo-layout ID` restores them. A factory reset to a restore point
   taken before adoption returns that older layout as a whole.

## Build installer ISO

Build on a dedicated, up-to-date Arch machine or VM with `archiso`, `pacman-contrib`
and `python-markdown` (handbook generation/checks), never on a
desktop you use: the payload build installs AUR build dependencies. From a
clean checkout of the commit the ISO ships:

```sh
distro/payload/build-payload.py --work /abs/payload-work --output /abs/payload --sources /abs/sources
EITR_PAYLOAD=/abs/payload EITR_ISO_BUILD_ROOT=/abs/build EITR_ISO_OUTPUT_ROOT=/abs/out \
  bash distro/build-iso.sh
```

[`payload/build-payload.py`](payload/build-payload.py) runs as a regular user.
It builds the AUR manifests, their AUR dependencies, `yay` and `eitr-desktop`
(from committed `HEAD`) into an unsigned `eitr` repository whose database pins
every package's SHA-256, and records each AUR Git commit in `manifest.json`;
review those PKGBUILDs before publishing an image. It then downloads, with an
empty package database, the complete dependency closure of every transaction in
[`payload/transactions.txt`](payload/transactions.txt): archinstall's base
steps and the desktop, once without and once with each hardware manifest. The
official packages keep their Arch signatures and the sync databases they came
from, so pacman verifies them against the image's `archlinux-keyring`. Oh My Zsh
and Powerlevel10k are bundled as pinned Git checkouts. Finally every transaction
is re-resolved from the payload alone and `SHA256SUMS` is written. `--work`
keeps clones, builds and downloads, so reruns are incremental; after each
build, `paccache` (pacman-contrib) keeps only the newest version of each
download and AUR package there. Build-only
toolchains (Rust, Go, the cursor renderer) stay on the build machine; only
runtime packages are shipped. `--sources` receives `makepkg --allsource`
archives of every AUR and local package built, with `SOURCES.json` naming their
AUR commits. They never go into the ISO or the download bucket: they back
`NOTICE.md`'s offer of GPL source, so copy them to the release's offline backup.

`build-iso.sh` refuses a payload built from another commit. It exports the
committed `HEAD` (via `git archive`) into `/opt/desktop-config` on the live
image, so uncommitted, untracked and ignored machine-local files are excluded,
adds the installer's live dependencies and the Eitr boot splash, then stores
the payload on the ISO filesystem as `/eitr`, beside the live image rather than
inside it. Main boot entries use `quiet splash copytoram=n` so the live system
keeps reading the medium; the UEFI menu's "boot messages" entry omits the
splash, and Escape reveals messages during it. The script refuses to reuse an
existing build directory or overwrite an ISO. Keep the image off public mirrors
until it has been tested in a VM. Build public images with
`EITR_PUBLIC_RELEASE=1`, which refuses while any shipped artwork is under review
(see [ARTWORK-LICENSING.md](ARTWORK-LICENSING.md)).

### Guided install

Boot the ISO in **UEFI** mode. Eitr's preparation screen and guided wizard open
automatically on the first console; `eitr-guided-install` can also be run as
root from that live image. No network is needed or asked for: everything is
installed from the medium, and you connect after logging in to the desktop. The
wizard supports arrow keys, type-to-filter lists, Enter and Escape. It:

1. Lists whole, writable disks of at least 64 GiB (never the boot medium)
   with their size, connection, model, contents and usable free space. No disk
   name is assumed. The install type is either **Erase** (the whole disk) or
   **Install alongside**: on a GPT disk with at least 34 GiB unallocated in one
   gap, the EFI partition and Btrfs root are created in the largest gap and
   every existing partition is kept. Make the gap first with the other system's
   own tools (for example by shrinking C: in Windows Disk Management); the
   installer never resizes partitions. Either way, typing the disk's path
   starts the installation.
2. Collects keyboard, hostname, user account, passwords and optional LUKS2
   encryption. English is the default; when online, the timezone is detected by
   HTTPS public-IP geolocation. Offline, it starts as UTC and
   `eitr-timezone.service` detects and sets the zone once the installed system
   is online, then disables itself. Credentials are hidden and
   handed to archinstall through a pipe, never written to a file or command line.
3. Points the live pacman at the payload and runs archinstall offline with
   [`archinstall/user_configuration.json`](archinstall/user_configuration.json):
   a 2 GiB FAT32 ESP at `/boot` and a Btrfs root with subvolumes `@` (`/`),
   `@home`, `@log` (`/var/log`) and `@pkg` (`/var/cache/pacman/pkg`), so `/usr`,
   `/etc` and `/var/lib/pacman` stay in the root snapshot that
   `eitr-system snapshots-check` requires. `/.snapshots` is not a separate
   subvolume because `snapshots-setup` lets Snapper create it. Erase installs
   Limine to the removable fallback path; alongside installs register their own
   "Arch Linux Limine Bootloader" firmware entry instead, leaving the other
   system's loader in place. It also selects
   Limine (kernels on the FAT `/boot`, compatible with bootable snapshot entries),
   linux, zram, Plymouth, PipeWire, Bluetooth, `[multilib]`, iwd with
   systemd-networkd and resolved (no NetworkManager), and the Minimal profile.
4. Installs the desktop packages, the hardware packages `hardware/detect.sh`
   selects for this computer (NVIDIA GPUs get `nvidia-open`; set
   `DISTRO_NVIDIA_DRIVER=skip` before running the installer to keep another
   GPU in charge) and the prebuilt AUR packages.
5. Sets up the new user without a running session: `install.sh --seed-user`
   seeds the defaults, unpacks Oh My Zsh and Powerlevel10k, and generates every
   Afterglow app style; `system/configure-desktop.sh` installs the network files,
   the Clockwork Tape login design, the Hyprland UWSM session as SDDM's default,
   Zsh and the services. Snapper is configured, the Limine menu entry is
   titled Eitr and every Windows Boot Manager found on another EFI partition is
   added below it, the Eitr splash
   is selected, the installed system's pacman is switched to the online mirrors
   in [`payload/mirrorlist`](payload/mirrorlist), and the read-only factory
   reset point is saved (see [FACTORY-RESET.md](FACTORY-RESET.md)).

One progress screen covers every step: it counts completed steps and, inside
package installation, pacman's own installed-package counts, never elapsed
time. When it finishes, it shows the total installation time (each step's time
is kept in `/var/log/eitr-install.log` on the installed system); power off,
remove the medium (the live system runs from it until then) and turn the
computer on. After unlocking the disk,
SDDM shows the Eitr login. Snapshot boot entries, GeForce NOW and Visual Studio
Code theme extensions need the network and stay explicit later actions. BIOS
boot, MBR disks, resizing partitions and other layouts are not handled by the
guided install; use a manual Arch install meeting the requirements above
instead. Windows started from the Limine menu may ask for its BitLocker
recovery key, because chainloading changes the boot measurements; the firmware
boot menu starts it directly.

### Unattended install

To install without answering questions (several machines, or one you are setting
up for someone else), give the ISO an answers drive:

1. Format a small USB stick (or a spare partition) as FAT32 with the label
   `EITRANSWERS` (FAT labels hold 11 characters; on a filesystem that allows
   longer labels, `EITR-ANSWERS` works too).
2. Put a file named `eitr-answers.json` on it:

   ```json
   {
     "disk": "/dev/nvme0n1",
     "layout": "erase",
     "encrypted": true,
     "passphrase": "disk encryption passphrase",
     "hostname": "eitr",
     "username": "alex",
     "password": "login password",
     "keyboard": "us",
     "language": "en_US.UTF-8",
     "timezone": "America/Sao_Paulo"
   }
   ```

   `disk` must be a disk the wizard would offer; check its name with the
   wizard first if unsure. `layout` is `erase` or `alongside`. `passphrase` is
   needed only when `encrypted` is true. Leave out `timezone` to detect it online
   after installation.
3. Boot the Eitr ISO with both drives plugged in. The installer reads the answers,
   validates them like the wizard, shows what it will do and counts down 15
   seconds: **Ctrl+C cancels before any disk is changed.** Then it installs and
   powers off.

The file holds passwords in plain text: keep the stick safe and wipe it when the
installs are done. Without the stick, the ISO starts the normal wizard.

### Organization profiles

Put `eitr-profile.json` on the same `EITRANSWERS` stick, with or without answers.
The wizard Review (or unattended 15-second countdown) lists every removal,
addition, default, policy and setup script before any disk changes. Example:

```json
{
  "version": 1,
  "name": "Example office",
  "remove": ["steam", "moonlight-qt", "eitr-sunshine", "tailscale"],
  "add": {
    "recipes": ["productivity/libreoffice"],
    "packages": ["chromium"],
    "flathub": ["us.zoom.Zoom"],
    "files": [{"file": "packages/office-tools-1-1-any.pkg.tar.zst", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}]
  },
  "defaults": {
    "theme": "norse",
    "wallpaper": {"file": "office.png", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
    "browser": "chromium",
    "update_channel": "stable",
    "repository": {
      "name": "office",
      "server": "https://packages.example.org/$arch",
      "key": {"file": "office-key.asc", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"}
    }
  },
  "setup": {"file": "setup.sh", "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"},
  "policies": {"remote_access": false, "assistants_together": false, "update_channel": "stable", "gaming": false}
}
```

Replace example digests with `sha256sum` output and copy every named file to the
stick. Only version and name are required. Repository/recipe/Flathub additions
need internet; stick packages and their supplied dependencies work offline.
No AUR builds run. Only reviewed optional apps may be removed; desktop packages
are protected. Use `eitr profile check DRIVE` to validate, and `eitr profile apply
DRIVE` to review and type `APPLY PROFILE` on an installed system. The recorded
profile prevents System Update from reinstalling excluded apps. Policies govern
Eitr tools and menus; they are not a lockdown against root. See
[Organization profiles](ORGANIZATION-PROFILES.md) for the schema, supported recipes,
setup retry semantics, signing keys and limitations, and
[VM verification](PROFILE-VM-TESTING.md) for pending VM commands.

## Before calling it a distro

- Test the ISO boot and post-install flow on real AMD, Intel and NVIDIA systems
  (UEFI only); verify networking and graphics separately.
- The development bootstrap has mock tests, not a completed fresh-machine
  installation test. This recipe is not a byte-for-byte system clone: fan-control
  services and other hardware-specific tuning still need target-specific review.
- Test the guided install (LUKS2, Limine, offline payload) on real AMD, Intel
  and NVIDIA hardware, not only in UEFI VMs.
- Audit asset licenses, package updates, security defaults, and the first-run
  experience. Never bundle tokens, logins, saved networks or device identifiers.

The official project name is **Eitr**; the GitHub repository is
[`eitr-org/eitr`](https://github.com/eitr-org/eitr).
Installer paths remain generic. The Eitr logo is in `branding/`;
release branding and fresh-install validation remain in progress.

References: [Archiso](https://wiki.archlinux.org/title/Archiso),
[GPU drivers](https://wiki.archlinux.org/title/Graphics_processing_unit),
[Steam](https://wiki.archlinux.org/title/Steam),
[GStreamer](https://wiki.archlinux.org/title/GStreamer),
[NVIDIA](https://wiki.archlinux.org/title/NVIDIA),
[Hyprland monitor rules](https://wiki.hypr.land/configuring/core/monitors/),
[Claude Code setup](https://code.claude.com/docs/en/setup),
[Codex CLI](https://developers.openai.com/codex/cli/).
Development bootstrap references: [NVM](https://github.com/nvm-sh/nvm),
[SDKMAN installation and CI options](https://sdkman.io/install/).

## Existing desktop: privileged integration

Config/menu changes do not automatically install packages, change PAM, or
configure root snapshots on the owner's running desktop. To enable the root
integration on a reviewed supported Btrfs installation, install the dependencies
and root-owned helper and System Update policy deliberately:

```sh
sudo pacman -S --needed snapper fprintd pam-u2f flatpak lazygit lazydocker pacman-contrib
(cd distro/pkg/eitr-artwork && makepkg --clean)
(cd distro/pkg/eitr-desktop && makepkg --nodeps --clean)
sudo pacman -U distro/pkg/eitr-artwork/eitr-artwork-*.pkg.tar.zst distro/pkg/eitr-desktop/eitr-desktop-*.pkg.tar.zst
sudo /usr/lib/eitr/eitr-system snapshots-setup
sudo install -Dm644 /usr/share/eitr/system-update-policy.conf /etc/eitr/system-update-policy.conf
```

The [package](#desktop-package-and-config-updates) installs the root helper,
the data files read by the Install submenus, development installers and
Snapshots → Recovery Instructions, the Recovery, Secure Boot and Factory Reset guides, and
`eitr-config`. Rebuild and reinstall it
after pulling changes; there is no manual copy step. Installing the package does
not touch `~/.config`: run `eitr-config status` to compare the live files with
the shipped defaults before deciding on `eitr-config update` (it never
overwrites edited files). Copies in `~/.local/share/eitr/` take precedence over
`/usr/share/eitr/`, so remove stale ones from earlier manual installs, and remove
an old `/usr/local/lib/eitr/eitr-system` once the packaged helper is installed.

Run from this repo, as the normal desktop user. If setup rejects the layout,
stop; do not bypass its protection. The initial dependency bootstrap above is
not protected before that policy is enabled. Thereafter, System Update requires
successful snapshot creation before upgrading. Terminal commands `eitr update pacman|aur|full` are unprotected.
Existing desktops without the policy still update normally.
If you installed the old Eitr hooks manually, remove only
`/etc/pacman.d/hooks/05-eitr-snapshot-pre.hook` and
`/etc/pacman.d/hooks/95-eitr-snapshot-post.hook` to adopt this new policy.
Never sudo a helper under a user-writable config path.
Do not restart SDDM or test authentication without a recovery console available.
