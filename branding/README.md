# Eitr branding

## Rune wordmark

The approved EITR wordmark preserves the original E rune and adds a narrow I,
arrow-shaped T, and open angular R. These are custom rune-inspired letters,
rather than a historical alphabet transcription. There is no liquid pool.

- `sources/logos/eitr-wordmark-master.svg`: approved vector master.
- `svg/eitr-wordmark.svg`: themeable `currentColor` export.
- `svg/eitr-wordmark-{black,white,green}.svg`: fixed-color vectors.
- `png/eitr-wordmark-{black,white,green}-{512,1024,2048}.png`: transparent
  exports named by width, with proportional height.

The repository README uses the green wordmark. Desktop icon assets remain
available separately below. Regenerate the wordmark with:

```sh
uv run --with pillow branding/scripts/export-wordmark.py
```

The master uses closed polygon paths with M/L/Z commands; retain that format
when editing it so both vector and raster exports stay synchronized.

## Desktop mark

The Eitr logo, the **Eitr rune mark**, is an angular E in negative space inside
an organic liquid pool. `sources/logos/eitr-logo-master.png` is the transparent raster
source; `sources/logos/eitr-logo-concept.png` preserves the selected concept presentation.

The transparent asset was extracted with the built-in image-generation tool.
Prompt: Extract the exact black liquid-pool logo and angular rune E; remove the
caption and white background, including the E interior, to produce genuine
transparent negative space. Preserve the contours and rune geometry; no redesign,
bubbles, drips, text, shadows or glow.

The installed copy is `fastfetch/assets/eitr-logo.png`. Keep it identical to
`sources/logos/eitr-logo-master.png`.
Walker Settings → System → About renders the alpha silhouette as theme-colored terminal
half-blocks, so the mark follows the active accent on both light and dark themes.

## Production exports

- `svg/eitr-logo.svg`: scalable paths using `currentColor` (black by default).
- `svg/eitr-logo-{black,white,green}.svg`: fixed-color vector variants.
- `png/`: transparent square logos at 16, 24, 32, 48, 64, 128, 256, 512,
  1024, 2048 and 4096 px, in black, white and forest green.
- `pdf/`: vector versions for print and design tools.
- `icons/eitr.ico`: multiresolution icon with a light background.
- `banners/`: matching 1920×1080 dark/light compositions as SVG and PNG.

Use SVG for resolution-independent layouts, PNG for applications requiring raster
images, and ICO for favicon/Windows icon consumers. Raster sizes are rendered
from paths, not enlarged from the source PNG. Small sizes retain the same mark;
they are not separately hand-tuned pixel icons. The original carousel artwork
remains in the desktop shell assets.

Regenerate with:

```sh
uv run --with cairosvg --with pillow branding/scripts/export-logo.py
```

The exporter traces the raster alpha mask into outer and inner contours, retaining
the rune hole with an even-odd fill. Contours are simplified within 0.8 source
pixels. Dependencies are development-only, not additional distro runtime packages.
