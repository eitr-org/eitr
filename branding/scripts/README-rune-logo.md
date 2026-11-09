# About rune emblem

`python3 branding/scripts/export-rune-logo.py` exports
`fastfetch/assets/eitr-runes.txt` and its transparent Settings preview
`fastfetch/assets/eitr-runes.png` from `branding/svg/eitr-logo.svg`.

Requires rsvg-convert, Pillow, fontTools and fontconfig. Fontconfig selects
JetBrainsMono Nerd Font and its Runic fallback (Noto Sans Runic on Eitr).
The text is font-independent; the PNG reflects the installed fonts. A font report
is written to `/tmp/rune-logo-previews` (override with `--preview-dir`).

The alpha mask is cropped, sampled with area averaging into 38 columns and
20 rows, then filled at 50% coverage. The 24 Elder Futhark letters cycle in
reading order. Cells are 12×24 pixels. Leading spaces and the E cut-out are
retained; trailing spaces are omitted. About supplies the current theme accent
and reserves the actual text width plus its existing six padding cells.

The 20-row choice leaves 76 information columns in a 120-column terminal and
56 in a 100-column terminal. A 28-row, 53-column rendition would leave only
61 and 41 columns respectively.
