# Eitr Artwork

Eitr uses the Primordial Venom palette: black background, green-tinted surface
and raised roles, pale text and a yellow-green accent. Terminal black uses
surface, white uses text, bright black uses muted, and bright colors mix 25%
white into normal colors. Selection uses raised and the approved text color.
Neovim and VS Code use Eitr's own themes from this palette.

## Wallpapers

1. `01-rune-seal.jpg` — the Eitr emblem and venom drip within gold rune rings; the default, an owner-approved neon seal on true black for OLED displays.
2. `02-gates-of-yggdrasil.jpg` — The Gates of Yggdrasil: carved bears facing across a monumental gate, ravens, a lone figure and the world tree; owner-approved ink screenprint with bold contours and flat cel shading.
3. `03-primordial-drop.jpg` — the complete venom teardrop in black void.
4. `04-eitr-runestone.png` — the procedural bronze-gold emblem and rune ring beneath an aurora; the animated wallpaper.

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
`../artwork-batch-09.json`. Élivágar and Venom Rootlight are removed;
their prompts remain in those manifests as history. Saved selections migrate
to the renamed image or the new Rune Seal default.

`references/generate-wallpapers.py` generates the runestone and live layers in
`motion/04-eitr-runestone/`. Its static image remains the lockscreen fallback.
The independent procedural theme preview is preserved.

Artwork is CC-BY-4.0, credited to the EITR project.
