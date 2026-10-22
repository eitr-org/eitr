# Organization profile package review

The explicit allowlist is `removable-apps.json`. Removing packages uses pacman
without recursive removal or dependency overrides. Its dependency check remains
mandatory. The desktop package derives its dependencies from `packages.txt`;
`aur-packages.txt`, `eitr-artwork` and local packages other than Sunshine are
protected, including the reviewed cmux binary.

Every apps.txt entry was reviewed. Optional candidates accepted:
apache, eog, evince, gamemode, gamescope, git-filter-repo, kdeconnect,
lib32-gamemode, steam, steam-devices, moonlight-qt, tailscale,
mangohud, terraform, totem.

Retained as protected support or conservative defaults:
archlinux-xdg-menu (application menu data), breeze and gnome-themes-extra
(theme integration), btrfs-progs (recovery), cronie (system scheduling),
dmidecode and smartmontools (hardware information), efibootmgr (boot setup),
openrgb (theme lighting integration), file-roller (archive workflow), firefox (default browser), ex-vi-compat, nano,
vim and tree (terminal workflows), gstreamer, gst-libav, gst-plugin-pipewire,
gst-plugins-base, gst-plugins-good, gst-plugins-bad and gst-plugins-ugly
(media support), gvfs-mtp and gvfs-smb (file manager integration), hyprpm
(compositor tooling), impala (network tooling), keyd (input configuration),
libpulse, pipewire-jack and lib32-systemd (runtime libraries), pacman-contrib
(System Update), wget (installer tooling), zram-generator (system defaults).

Every aur-apps.txt entry was reviewed. localsend-bin and watchman-bin are
optional. All four catppuccin-plasma-colorscheme packages (frappe, latte,
macchiato, mocha) remain protected theme support.

Groups are gaming, media, development, sharing and remote_access.
A group policy disables Eitr installation actions for that group and excludes
its allowlisted packages. This list deliberately prefers refusal over guessing
whether a support package is unused.
