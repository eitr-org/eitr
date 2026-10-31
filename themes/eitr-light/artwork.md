# Eitr Light Artwork

The light counterpart of Eitr's Primordial Venom palette uses pale green-tinted
background, surface and raised roles, dark green text, venom yellow-green accent
and jade/emerald secondary color. Every normal and bright chromatic terminal
color is dark enough for AA text on all three pale surfaces. Neovim and VS Code
use Eitr's own palette-driven themes in light mode. Generate their integrations
with `../build-theme-files.py` and `../build-vscode-themes.py`.

## Wallpapers

1. `01-primordial-drop.jpg`: a complete translucent jade venom drop in pale mist; the default.
2. `02-elivagar.jpg`: primordial jade rivers winding through bone-green mineral terrain.
3. `03-venom-rootlight.jpg`: a fine venom thread branching into hairline mineral light veins.

Each ships at 3840×2160 in `backgrounds/` and 3440×1440 in
`backgrounds-ultrawide/`, as JPEG. The ultrawides are separate panoramic
compositions. These are Lanczos exports, not native 4K generations.
The owner requested the painterly cinematic batch 09 style on pale mist, bone
and parchment green, with venom light as the only vivid accent.

Exact generation prompts, the Élivágar cleanup edit, native sizes, SHA-256
hashes and crop framing are in `../artwork-batch-10.json`. Masters and the
reproducible export script live in `branding/sources/wallpapers/batch-10/`.
All are original built-in image generations from written briefs, without image
references, lettering or logos. Agent-inspected; awaiting owner visual review.

The optional Runestone is not included: the existing procedural renderer
embeds rune lettering and the Eitr logo, with no compatible light mode. These
three wallpapers are still images and need no motion layers. Theme Wallpaper
uses the selected still image on the lockscreen through the existing workflow.

`preview.png` is an isolated offscreen production Calendar panel capture over the
default wallpaper. Its reproduction command is in `../ARTWORK.md`; it contains
no live desktop content. Artwork is CC-BY-4.0, credited to the EITR project.

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
