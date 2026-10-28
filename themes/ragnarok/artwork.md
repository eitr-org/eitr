# Ragnarök

Palette: the owner's Ragnarök palette (2026-10-28), accent #c44750 and second #e7ad67. All dark.

Background, surface and raised roles are recorded separately in `colors.toml`. Terminal black uses surface, white uses text, bright black uses muted, and bright colours mix 25% white into each normal colour. Body and selection text retain the approved text colour.

Editor and icon base: gruvbox; integration files are generated from `../integrations.json`.

## Wallpapers

- `01-blood-eclipse.jpg`: a complete black celestial disk with a restrained crimson ring, faint charcoal haze and a low mountain silhouette.
- `02-fenrir-devours-the-sun.jpg`: a colossal wolf in profile, connected jaws surrounding the eclipsed sun, crimson rim light and dark negative space.
- `03-dying-yggdrasil.jpg`: the complete dying World Tree beneath a blood moon, crimson bark cracks, sparse gold highlights and barren dark ground.
- `04-world-tree-pyre.jpg`: a burning World Tree and darkening sun above a ruined distant landscape, in crimson and gold.

The first three are the owner's approved batch 08 selections. Their ultrawides
are separately generated panoramic compositions from the same written briefs,
with no reference-image inputs. The full disks, jaws and tree canopy stay in
frame, with calm dark space across the top for the bar. Native masters and exact
prompts, rendering styles, dimensions, SHA-256 hashes and framing are in
[Batch 08](../artwork-batch-08.json); rebuild with
`branding/sources/wallpapers/batch-08/export.py`.

World Tree Pyre's native masters and exact prompts are recorded in
[Batch 06](../artwork-batch-06.json); rebuild with
`branding/sources/wallpapers/batch-06/export.py`.

The owner explicitly permits scenic environments and painterly dark fantasy
for this set. All compositions are original, without readable lettering,
runes, logos or third-party likenesses. Native-size panoramic inspection checks
anatomy, complete framing, banding and unwanted marks. Exports are crop-to-fill
Lanczos-resampled JPEGs: 3840×2160 in `backgrounds/` and 3440×1440 in
`backgrounds-ultrawide/`, never stretched or padded. These are export sizes,
not native generated detail. The theme's independent `preview.png` is preserved.
Artwork license: CC-BY-4.0, credited to the EITR project.
