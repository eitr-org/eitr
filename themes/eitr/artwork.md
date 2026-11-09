# Eitr Artwork

Eitr uses the Primordial Venom palette: black background, green-tinted surface
and raised roles, pale text and a yellow-green accent. Terminal black uses
surface, white uses text, bright black uses muted, and bright colors mix 25%
white into normal colors. Selection uses raised and the approved text color.
Neovim and VS Code use Eitr's own themes from this palette.

## Wallpapers

1. `01-aurora-fjord.jpg` — the default: a lantern-lit longship beneath venom-green aurora in a dark fjord.
2. `02-dusk-fjord.jpg` — a striped-sail longship in a warm sunset fjord.
3. `03-rune-seal.jpg` — the neon Eitr emblem and venom drip within gold rune rings on true black.
4. `04-eitr-runestone.png` — the animated procedural emblem and rune ring beneath an aurora.

All ship at 3840×2160 in `backgrounds/` and 3440×1440 JPEG in
`backgrounds-ultrawide/`, using subject-centred Lanczos crop-to-fill without
stretching or padding. These exports are not native 4K generations.
Batch 12 preserves four approved PNGs: two 16:9 fjords and two separately
generated panoramic sideways extensions. Exact prompts, input filenames,
native sizes, SHA-256 hashes and framing are in `../artwork-batch-12.json`;
rebuild with `branding/sources/wallpapers/batch-12/export.py`.
The third-party style reference is documented by filename only and is not distributed.
Batch 11 retains the rune seals and Eitr Light Gates with their prompts and sources.
Saved selections follow the migration chain to their renamed image or the new default.

Eitr Gates and Primordial Drop are removed; their provenance remains in batches
11 and 09. `references/generate-wallpapers.py` owns the runestone and unchanged
`motion/04-eitr-runestone/` layers. The independent theme preview is preserved.

Artwork is CC-BY-4.0, credited to the EITR project.
