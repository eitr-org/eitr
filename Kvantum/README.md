# Kvantum

Each theme's `dolphin.theme` names a Catppuccin Kvantum theme such as
`catppuccin-latte-mauve`. The base themes come from the
`kvantum-theme-catppuccin-git` package in `/usr/share/Kvantum`.

`walker/scripts/themes/system.sh` regenerates the `<name>#` override folder on
every theme switch by copying the base theme and enabling Dolphin transparency.
Kvantum prefers a `<name>#` folder in `~/.config/Kvantum` over the base theme.

The `#` folders here are generated snapshots, not sources. A theme whose
override is missing (for example `catppuccin-latte-mauve#`) still works: it is
created the first time that theme is applied, and can be synced here afterwards.
