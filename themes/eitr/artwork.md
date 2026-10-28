# Eitr Artwork

Eitr uses the Primordial Venom palette: black background, green-tinted surface
and raised roles, pale text and a yellow-green accent. Terminal black uses
surface, white uses text, bright black uses muted, and bright colors mix 25%
white into normal colors. Selection uses raised and the approved text color.
Neovim and VS Code use Eitr's own themes from this palette.

## Wallpapers

The owner’s order is:

1. `01-primordial-drop.jpg` — a complete venom teardrop enclosing a faint liquid echo of Eitr’s emblem in black void. This is the default.
2. `02-eitr-runestone.png` — the procedural bronze-gold EITR emblem within an Elder Futhark ring beneath an aurora.
3. `03-elivagar.jpg` — the primordial venom rivers winding through dark volcanic stone.
4. `04-venom-rootlight.jpg` — a fine venom thread spreading into mineral light veins across black stone.

All four ship at 3840×2160 in `backgrounds/` and 3440×1440 in
`backgrounds-ultrawide/` (the runestone’s ultrawide is JPEG).
Batch 09 preserves the three owner-approved native PNGs byte-for-byte and uses
separately generated panoramic compositions for their ultrawides. The owner
explicitly approved painterly cinematic dark fantasy for these images,
overriding the usual ink illustration direction. Only the drop uses an input:
Eitr’s own emblem as a shape reference. Exact final prompts, native sizes,
SHA-256 hashes and framing are in `../artwork-batch-09.json`; rebuild with
`branding/sources/wallpapers/batch-09/export.py`. Lanczos exports do not imply
native 4K detail.

`references/generate-wallpapers.py` generates the runestone and its live layers
in `motion/02-eitr-runestone/`. The static runestone remains the lockscreen
fallback. The procedural carousel preview is preserved for a later live retake.
`../build-vscode-themes.py` builds `vscode.vsix` from the theme palette.
Artwork is CC-BY-4.0, credited to the EITR project.
