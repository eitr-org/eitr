# rose-pine Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-heron-and-thread.jpg`
- `backgrounds/02-petal-terraces.jpg`
- `backgrounds/03-rose-courtyard.jpg`


Batch 01: two original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future additions use written briefs only, following `branding/ART-DIRECTION.md`, with no external image inputs.

## 02-petal-terraces

File: backgrounds/02-petal-terraces.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. Abstract but recognizable terraced botanical garden formed from sculptural pale pink clay, rounded mauve paths, sparse teal leaves and a still pale water channel. Elegant tactile 3D-like painted landscape with matte paper textures, airy light mood. Rose Pine Dawn #faf4ed #b4637a #56949f #907aa9 #d7827e.

## 03-rose-courtyard

File: backgrounds/03-rose-courtyard.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. A tranquil pale stone courtyard with a flowering rose tree, shallow reflection pool, softly curved archways and distant low mauve hills under a bright morning sky. Original refined watercolor and gouache architectural illustration, luminous not dark. Dawn #faf4ed mutedrose #b4637a teal #56949f mauve #907aa9 peach #d7827e.

## Removed in batch 04: Batch 02: 01-paper-play

Replaced by `01-heron-and-thread` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/01-paper-play.jpg

Reference-led character/graphic/object direction instead of generic city/nature vistas. Attached contact sheet was a mood, medium and palette reference only; output is a new single composition. Lanczos-upscaled to 3440 x 1440, as in batch 01.

Prompt:

Create ONE new original ultrawide 21:9 desktop wallpaper. The attached contact sheet is ONLY a reference for the theme's visual language, texture, subject category and palette, not an edit target. Do not copy its compositions, characters, logos or writing. Output a single full-bleed artwork, NOT a contact sheet, poster, screenshot or mockup. No lettering, text, signatures, watermarks, logos or border. Avoid city panoramas, mountain landscapes, forests, lakes, sunsets, architecture vistas and generic scenery. Spacious balanced desktop composition. Light abstract graphic composition made of asymmetrically arranged irregular dusty-rose, muted teal and mauve paper shapes, thin wandering hand-drawn contour lines, sparse short dash patterns and delicate concentric arcs. Full-width balanced original composition, NOT centered logo. Flat 2D screenprint with slight paper texture, Rose Pine Dawn #faf4ed #b4637a #56949f #907aa9 #d7827e, large breathing spaces. Playful refined graphic design, no representational landscape, plants or architecture. Echo the funky-shapes reference.

## 01-heron-and-thread

File: backgrounds/01-heron-and-thread.jpg

Ultrawide: backgrounds-ultrawide/01-heron-and-thread.jpg

Native source: `branding/sources/wallpapers/batch-04/rose-pine-01-heron-and-thread.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Use case: stylized-concept. Create an entirely original Norse-fantasy desktop wallpaper from this written brief ONLY. No reference images, no image inputs, no borrowed character designs. Request native 3840x2160 landscape 16:9 if supported. Clearly hand-drawn screenprint illustration: bold expressive black pen contours, simplified anatomy and shapes, flat limited spot colors, two-tone cel shading, rhythmic confident brush strokes, restrained dry-ink flecks. Not photographic, realistic, 3D, metallic engraving or cinematic painting. One full-bleed composition, no collage, no UI, no border, no text, no letters or legible runes, no logos, signatures or watermark. No forest, mountains, landscape, horizon or scenic backdrop. Keep the entire important subject comfortably inside x=15–85%, y=23–77%, including all extremities, so it survives a centered ultrawide crop. Do not fill the whole frame: retain generous calm empty areas and quiet top/bottom edges. Varied original compositions, no mandatory crown, circular ornament or knotwork frame. A single elegant stylized heron stands on one leg, its neck folded into an angular S, holding a very short piece of knotted coral-colored weaving thread in the tip of its beak. Slightly tousled feathers and expressive small eye, entire body, raised foot, beak and thread visible. Slender vertical subject in the left-middle x=26–47%, y=25–76%; right half remains quiet. Original peaceful Norse folk screenprint, sophisticated and light. Light-theme paper background #faf4ed, warm pale areas #f2e9e1, bold deep-plum/black ink contours #575279, teal #56949f and #286983, dusty rose #b4637a, coral #d7827e, very small ochre #ea9d34. Flat colors, sparse generous shapes. No marsh, reeds, water, landscape, halo or frame.
```

### 01-heron-and-thread ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/rose-pine-01-heron-and-thread-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```
