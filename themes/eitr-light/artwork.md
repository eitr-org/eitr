# Eitr Light Artwork

The light counterpart of Eitr's Primordial Venom palette uses pale green-tinted
background, surface and raised roles, dark green text, venom yellow-green accent
and jade/emerald secondary color. Every normal and bright chromatic terminal
color is dark enough for AA text on all three pale surfaces. Neovim and VS Code
use Eitr's own palette-driven themes in light mode. Generate their integrations
with `../build-theme-files.py` and `../build-vscode-themes.py`.

## Wallpapers

1. `01-gates-of-yggdrasil.jpg` — The Gates of Yggdrasil: carved bears facing across a monumental gate, ravens, a lone figure and the world tree. The new default; owner-approved ink screenprint with bold contours and flat cel shading.
2. `02-rune-seal.jpg` — the Eitr emblem and venom drip within gold rune rings; owner-approved neon seal, recoloured in forest green and bronze on pale parchment with a gentle sheen.
3. `03-primordial-drop.jpg` — the complete venom teardrop in pale mist.

All ship at 3840×2160 in `backgrounds/` and 3440×1440 JPEG in
`backgrounds-ultrawide/`. Batch 11 preserves eight owner-approved native PNGs
byte-for-byte: four 16:9 masters and four separately generated panoramic edits.
These are subject-centred Lanczos exports, without stretching or padding,
not native 4K generations. Exact supplied prompts, earlier draft inputs, edit
history, native sizes, SHA-256 hashes and framing are in
`../artwork-batch-11.json`; rebuild with
`branding/sources/wallpapers/batch-11/export.py`. These originals were made with
Codex image generation, including edits with image inputs. References guided
the original drawings; they are not distributed wallpaper assets.

Primordial Drop retains its owner-approved painterly style and provenance in
`../artwork-batch-10.json`. Élivágar and Venom Rootlight are removed;
their prompts remain in those manifests as history. Saved selections migrate
to the renamed image or the new Gates default.

The independent `preview.png` remains the isolated Calendar panel capture over
Primordial Drop described in `../ARTWORK.md`; the exporter preserves it.
All three wallpapers are still images; Theme Wallpaper uses the selected image
on the lockscreen.

Artwork is CC-BY-4.0, credited to the EITR project.

## Contrast

WCAG relative luminance (AA text threshold 4.5:1), using the shared editor
contrast helper and the same sRGB transfer as PanelStyle. Ratios below are
against background, surface and raised, respectively.

| Role | Color | Background | Surface | Raised |
| --- | --- | ---: | ---: | ---: |
| foreground | `#17291e` | 13.99:1 | 12.78:1 | 11.43:1 |
| muted | `#404d43` | 8.13:1 | 7.43:1 | 6.64:1 |
| accent | `#3e5212` | 7.93:1 | 7.24:1 | 6.48:1 |
| second | `#1f4d31` | 8.87:1 | 8.10:1 | 7.25:1 |
| alert | `#7d2c34` | 8.41:1 | 7.68:1 | 6.87:1 |

All normal and bright chromatic ANSI inks pass on all three neutral surfaces.
All editor text roles also pass on their generated surface, raised, line,
visual-selection and search backgrounds (minimum 4.59:1).
Secondary panel text at PanelStyle’s 72% opacity passes on the neutral surfaces
and the selected row fill (minimum 4.84:1 on a selected row).
