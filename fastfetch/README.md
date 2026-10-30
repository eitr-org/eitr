# About Eitr

Walker → Settings → System → About opens the themed Fastfetch page via `eitr.py`.
Run `eitr-run fastfetch/eitr.py` directly for the same output.

Each invocation reads the active theme's `colors.toml` and `display-name` (falling
back to the cached theme name). The liquid E logo appears beside three equal-width
boxes: Hardware, Software and Time (system age, uptime and date), each titled with an icon in its colour. Hardware includes the model,
CPU, GPUs, memory and root disk usage with percentages and filesystem. Software
includes the installed Eitr version on Arch Linux, kernel, pacman/Flatpak counts,
shell, login manager, window manager, terminal, configured desktop font (when
saved) and current theme. Sixteen round palette swatches follow on one line. No theme generator or restart is needed.

Fastfetch detects the system information through its native modules. Custom
modules supply borders, theme, release and OS age. A final terminal-cell-aware
pass pads each row and truncates long values with `…`, preserving ANSI colours
and wide characters. Boxes use at most 76 columns and shrink to leave space for
the logo in a 100-column terminal. Guides and icons use palette colours 2, 4 and
3 respectively; borders and centred titles are dimmed. Missing module data is
shown as an error inside its row rather than silently dropping it.

OS age is whole days since the root filesystem birth timestamp (`stat -c %W /`).
If unavailable, it uses the earliest valid timestamp in `/var/log/pacman.log`.
Filesystem recreation or log rotation can make this an estimate of installation
age; missing or future timestamps show Unavailable. No elevated access is needed.

The logo is rendered from its transparent alpha mask using Pillow and terminal
half-blocks; no image protocol dependency, altered source image or stale cache.

The shared wordmark asset is still used by task-terminal banners and setup wizards;
`branding/scripts/export-wordmark.py` continues to synchronize it. About does not
render the wordmark.

Dependencies: Fastfetch, Python 3.11+, Pillow, and Kitty for the Walker action.
`--config-only` prints the generated Fastfetch JSON (before final row fitting);
`--no-logo` hides the logo. Headless captures use the same modules and layout.
