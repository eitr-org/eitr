# About Eitr

Walker → System → Information → About opens the themed Fastfetch page via `eitr.py`.
Run `eitr-run fastfetch/eitr.py` directly for the same output.

Each invocation reads the active theme's `colors.toml`, `display-name` (falling
back to the cached theme name), and Quickshell appearance setting. It includes
the Eitr logo, actual Arch base/system/hardware information, theme colors, and
all sixteen palette swatches. No theme generator or service restart is needed.
The logo is rendered from its transparent alpha mask using Pillow and terminal
half-blocks; no image protocol dependency, altered source image or stale cache.
The Runic EITR wordmark sits above the information column, rendered in the
same theme accent at 24 cells wide and five text rows tall. The liquid E icon
retains its existing size. Both use alpha masks so light/dark themes work alike.
The wordmark asset is synchronized by `branding/scripts/export-wordmark.py`.

Dependencies: Fastfetch, Python 3.11+, Pillow, and Kitty for the Walker action.
`--config-only` prints the generated JSON; `--no-logo` hides the logo for checks.
