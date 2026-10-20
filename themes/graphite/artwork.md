# graphite Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-fragments-of-touch.jpg`
- `backgrounds/02-ember-harbor.jpg`
- `backgrounds/03-thread-and-shadow.jpg`


Batch 01: two original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future batch: number new wallpapers after the last one and continue the reference-led visual language, without reproducing an existing composition or franchise.

## 02-ember-harbor

File: backgrounds/02-ember-harbor.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. A tiny unmarked sailboat crossing a charcoal harbor below immense layered storm clouds, narrow amber light through cloud break, intricate black engraved wave lines. Original woodcut-inspired illustration, dark restrained composition. Graphite #121212 #bebebe with sparing #e68e0d amber.

## Batch 02: 01-fragments-of-touch

File: backgrounds/01-fragments-of-touch.jpg

Reference-led character/graphic/object direction instead of generic city/nature vistas. Attached contact sheet was a mood, medium and palette reference only; output is a new single composition. Lanczos-upscaled to 3440 x 1440, as in batch 01.

Prompt:

Create ONE new original ultrawide 21:9 desktop wallpaper. The attached contact sheet is ONLY a reference for the theme's visual language, texture, subject category and palette, not an edit target. Do not copy its compositions, characters, logos or writing. Output a single full-bleed artwork, NOT a contact sheet, poster, screenshot or mockup. No lettering, text, signatures, watermarks, logos or border. Avoid city panoramas, mountain landscapes, forests, lakes, sunsets, architecture vistas and generic scenery. Spacious balanced desktop composition. Two original monochrome sculptural hands reaching toward each other across horizontal negative space, left hand emerging from low-left and right from upper-right, not touching, fingertips breaking into sparse crisp stippled particles. Black #121212 void, silver-gray #bebebe dot shading, subtle etched texture, no writing or ASCII characters. Refined abstract pointillist digital illustration, different gesture and placement from reference; not the Creation of Adam composition. Minimal, balanced, no landscapes.

## Batch 03: thread and shadow

File: backgrounds/03-thread-and-shadow.jpg

Original reference-led AI-generated artwork, Lanczos-upscaled to 3440 x 1440.

```text
Use case: stylized-concept. Create ONE original full-bleed 21:9 ultrawide desktop wallpaper. Attached contact sheet is reference ONLY for visual language and palette, not an edit target. Stay faithful to its illustration/abstract/portrait identity; invent a new composition. Single artwork, not collage or screenshot. No text, lettering, logos, watermarks, signatures, borders, existing franchise characters, city panoramas, mountain vistas, forest landscapes or generic scenery. Calm upper edge and sophisticated spacious horizontal composition. Theme visual language: Monochrome stipple and engraving illustration; black #121212, silver-gray #bebebe, highly refined dot shading and tactile etched details; large negative space. New artwork: A sculptural silver-gray strip twisting into an open irregular loop, one end unraveling into fine dotted threads, horizontal arrangement and dark void, precise pointillist illustration, no text or ASCII glyphs.
```

## 01-fragments-of-touch — left-hand recreation

File: backgrounds/01-fragments-of-touch.jpg

The owner approved a newly drawn left hand with one thumb and four separated
fingers. Both exports use the corrected native master tracked in
`themes/artwork-batch-04.json`; the previous edit prompt is retained there as
superseded provenance. Rebuild with
`python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Replace the entire LOWER LEFT HAND with a completely NEW and much SIMPLER anatomically correct hand. Remove the current layered cupped fingers entirely. Draw a single hand reaching diagonally up-right, palm facing the viewer almost flat, fingers gently spread in ONE SINGLE PLANE with NO OVERLAP. EXACTLY FIVE visible digits in total, each one clean silhouette with a black gap from the next: thumb at upper-left of palm, index at upper-right, middle longest to the right, ring below middle, little shortest at lower-right. One thumb plus four fingers, five fingertips total, one palm, one wrist. Do not draw two rows of fingers or stacked fingertips; no extra small finger tucked underneath. The palm should be broad and fingers simple smooth shapes, realistic human proportions in the existing monochrome graphite drawing. Preserve the right-side reaching hand, black background, particle-dissolving wrists, original composition and ultrawide aspect43:18. Focus exclusively on believable five-digit anatomy. No text, numbers, labels, watermark, color or border. The old left-hand pose is explicitly discarded: create the new open flat hand rather than modifying existing fingers.
```
