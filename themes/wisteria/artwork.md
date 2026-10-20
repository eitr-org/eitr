# wisteria Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-indigo-bellflowers.jpg`
- `backgrounds/02-cloud-bloom.jpg`
- `backgrounds/03-violet-pavilion.jpg`


Batch 01: two original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future additions use written briefs only, following `branding/ART-DIRECTION.md`, with no external image inputs.

## 02-cloud-bloom

File: backgrounds/02-cloud-bloom.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. Luminous towers of soft lavender and pale peach clouds above distant blue hills, fine wisteria flowers lightly framing far right edge, vast open bright sky. Refined hand-painted dream landscape with delicate brushwork, not photorealistic. Light #fafafa blue #3264eb lavender #8a4ad7 paleviolet #9f85e0, very restrained magenta #c900c4.

## 03-violet-pavilion

File: backgrounds/03-violet-pavilion.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. An airy white garden pavilion with lavender flowering vines beside a quiet blue pond, soft bright clouds, gentle stone paths and low purple hills. Original gouache architectural landscape, delicate clean detail, pale light overall. Wisteria #fafafa #3264eb #8a4ad7 #9f85e0, tiny magenta flower accents.

## Removed in batch 04: Batch 02: 01-glass-ribbon

Replaced by `01-indigo-bellflowers` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/01-glass-ribbon.jpg

Reference-led character/graphic/object direction instead of generic city/nature vistas. Attached contact sheet was a mood, medium and palette reference only; output is a new single composition. Lanczos-upscaled to 3440 x 1440, as in batch 01.

Prompt:

Create ONE new original ultrawide 21:9 desktop wallpaper. The attached contact sheet is ONLY a reference for the theme's visual language, texture, subject category and palette, not an edit target. Do not copy its compositions, characters, logos or writing. Output a single full-bleed artwork, NOT a contact sheet, poster, screenshot or mockup. No lettering, text, signatures, watermarks, logos or border. Avoid city panoramas, mountain landscapes, forests, lakes, sunsets, architecture vistas and generic scenery. Spacious balanced desktop composition. A pure airy abstract composition of long translucent pale-blue glass ribbons curling across a luminous white canvas, hints of lavender refraction at edges, precise gentle layering and soft gray shadows. Large sweeping asymmetric forms from lower left to upper right, no flowers or sky, no landscape. Refined high-key 3D macro artwork, white #fafafa, pale blue, tiny #3264eb and #9f85e0 accents, restrained delicate contrast. Inspired by the original abstract blue-wave images.

## 01-indigo-bellflowers

File: backgrounds/01-indigo-bellflowers.jpg

Ultrawide: backgrounds-ultrawide/01-indigo-bellflowers.jpg

Native source: `branding/sources/wallpapers/batch-04/wisteria-01-indigo-bellflowers.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Generate a fresh original illustration solely from this written brief. No input images, no visual references and no recognizable fictional characters. Landscape 16:9, request native 3840x2160 if supported. Clearly drawn artwork with confident hand-inked contours, flat limited spot colors and simple two-tone cel shading. No photorealism, 3D, cinematic lighting, words, lettering, logos, signature, watermark, borders or UI. A simple airy botanical artwork: one slender gently bent stem bearing three small blue-violet bellflowers and two narrow leaves, plus one detached tiny petal. Delicate but visible near-black hand-drawn ink contours, just a few angular flat color planes and subtle dry-ink variation, no dense texture. Not a bouquet, garden, landscape, vase or ornate frame. Put the entire modest flower sprig in the right-middle, x=60–77%, y=32–69%, leaving generous uninterrupted paper-white negative space across the left half and along top and bottom. The mood is quiet, minimal and graceful, with a subtle Nordic folk-print character. Strict Wisteria palette: matte warm white #fafafa background, near-black #212121 ink, royal blue #3264eb, violet #8a4ad7, indigo #4a2fd0, tiny lavender #9f85e0 accents. No realistic green leaves; the leaves use muted indigo and lavender. Keep it SIMPLE: a small asymmetrical flower study with lots of space, not an elaborate floral pattern. Entire subject remains inside the central vertical band so a 21:9 crop retains all flowers.
```

### 01-indigo-bellflowers ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/wisteria-01-indigo-bellflowers-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```
