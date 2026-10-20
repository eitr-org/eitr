# stillwater Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-ashen-stag.jpg`
- `backgrounds/02-the-iron-key.jpg`
- `backgrounds/03-summit-shelter.jpg`
- `backgrounds/04-silent-wings.jpg`


Batch 01: two original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future additions use written briefs only, following `branding/ART-DIRECTION.md`, with no external image inputs.

## 03-summit-shelter

File: backgrounds/03-summit-shelter.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. A small mountaineering refuge perched above a wide alpine glacial lake, jagged distant ridges, tiny empty trail and quiet low clouds. Original finely hatched ink and graphite landscape illustration, sparse near-monochrome cool tones with tiny ember window accent. #101315 #798186 #cacccc #a5aeb4 tiny #de6145.

## Removed in batch 04: Batch 02: 02-the-listener

Replaced by `02-the-iron-key` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/02-the-listener.jpg

Reference-led character/graphic/object direction instead of generic city/nature vistas. Attached contact sheet was a mood, medium and palette reference only; output is a new single composition. Lanczos-upscaled to 3440 x 1440, as in batch 01.

Prompt:

Create ONE new original ultrawide 21:9 desktop wallpaper. The attached contact sheet is ONLY a reference for the theme's visual language, texture, subject category and palette, not an edit target. Do not copy its compositions, characters, logos or writing. Output a single full-bleed artwork, NOT a contact sheet, poster, screenshot or mockup. No lettering, text, signatures, watermarks, logos or border. Avoid city panoramas, mountain landscapes, forests, lakes, sunsets, architecture vistas and generic scenery. Spacious balanced desktop composition. Original monochrome manga-like illustration: a solitary young adult with loose jacket and headphones, seated sideways on a battered train seat in the right third, thoughtful profile looking toward an impossible dark circular void beyond a wide window. Outside is abstract scratched graphite and stardust, NOT a city or landscape. Strong hand-drawn contour lines, densely crosshatched folds, coarse vintage halftone grain, flat aged gray paper #cacccc and near-black ink #101315, subdued steel gray #798186. Figure is clearly the subject, mostly empty left half; moody existential surrealism. Clearly a drawing, no photorealism. Echo the archived Stillwater character-focused manga mood.


## Removed in batch 04: Batch 03: weightless

Replaced by `01-ashen-stag` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/01-weightless.jpg

Original reference-led AI-generated artwork, Lanczos-upscaled to 3440 x 1440.

```text
Use case: stylized-concept. Create ONE original full-bleed 21:9 ultrawide desktop wallpaper. Attached contact sheet is reference ONLY for visual language and palette, not an edit target. Stay faithful to its illustration/abstract/portrait identity; invent a new composition. Single artwork, not collage or screenshot. No text, lettering, logos, watermarks, signatures, borders, existing franchise characters, city panoramas, mountain vistas, forest landscapes or generic scenery. Calm upper edge and sophisticated spacious horizontal composition. Theme visual language: Black-and-white manga drawing, coarse halftone, crosshatching, aged gray paper #cacccc and ink #101315; surreal existential mood. New artwork: A solitary young adult in a loose dark coat floating sideways in a vast blank paper void, thin headphone cable curving in a loose arc, hair drifting, small ink fragments dissolving from the coat hem, no starscape or landscape; clearly hand-drawn, calm horizontal negative space.
```


## Removed in batch 04: Batch 03: the observer

Replaced by `04-silent-wings` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/04-the-observer.jpg

Original reference-led AI-generated artwork, Lanczos-upscaled to 3440 x 1440.

```text
Use case: stylized-concept. Create ONE original full-bleed 21:9 ultrawide desktop wallpaper. Attached contact sheet is reference ONLY for visual language and palette, not an edit target. Stay faithful to its illustration/abstract/portrait identity; invent a new composition. Single artwork, not collage or screenshot. No text, lettering, logos, watermarks, signatures, borders, existing franchise characters, city panoramas, mountain vistas, forest landscapes or generic scenery. Calm upper edge and sophisticated spacious horizontal composition. Theme visual language: Black-and-white manga drawing, coarse halftone, crosshatching, aged gray paper #cacccc and ink #101315; surreal existential mood. New artwork: Close profile of a young adult looking into an oval hand mirror whose reflection is an impossible black circular void, cropped shoulder and hand on right, scratched gray blank paper extending left; dense ink hatching and surreal graphic simplicity.
```

## 01-ashen-stag

File: backgrounds/01-ashen-stag.jpg

Ultrawide: backgrounds-ultrawide/01-ashen-stag.jpg

Native source: `branding/sources/wallpapers/batch-04/stillwater-01-ashen-stag.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Use case: stylized-concept.
Asset type: original Stillwater-theme desktop wallpaper review draft, landscape 16:9, request 3840x2160 native output if supported.
Title for tracking only, DO NOT render title: Ashen Stag.
Create from this written brief alone. No input images or visual references. Original Norse-fantasy hand-inked screenprint illustration: a peaceful adult stag resting with its legs tucked beneath its body, head lifted watchfully and turned toward the left. Its expressive branching antlers sweep in irregular asymmetric arcs; they are natural antlers, not a crown. Make the complete animal and antlers clearly visible within the middle vertical band of the image, roughly x=52–83%, y=24–76%, so the composition survives both 16:9 and centered 21:9 cropping. The left half is generous calm empty near-black. Along the top and bottom retain dark breathing room.
Medium: visibly drawn bold black pen contours, rhythmic flowing strokes, simplified sculptural anatomy, flat spot-color shapes, two-tone cel shading, very restrained dry-ink flecks close to the animal. Emphasize elegant silhouette and quiet mythic presence rather than realistic fur. No enclosing ornamental ring, no decorative frame.
Strict Stillwater palette: near-black #080a0b and charcoal #101315 dominate; slate #343d41, muted steel #798186, soft silver #cacccc, pale cool highlight #d9dbdc, tiny warm gray #cbc2be accents. No green or golden color cast. Matte flat ink, no photographic lighting, gradients, 3D or metallic rendering.
No landscape, forest, trees, mountains, lakes, horizon, architectural backdrop or scenery. No people or recognizable fictional characters. No words, letters, rune lettering, logos, signatures, watermarks, UI or borders. One full-bleed artwork, not a collage or mockup. Entirely new subject and composition created solely from this brief.
```

## 02-the-iron-key

File: backgrounds/02-the-iron-key.jpg

Ultrawide: backgrounds-ultrawide/02-the-iron-key.jpg

Native source: `branding/sources/wallpapers/batch-04/stillwater-02-the-iron-key.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Use case: stylized-concept. Create an entirely original Norse-fantasy desktop wallpaper from this written brief ONLY. No reference images, no image inputs, no borrowed character designs. Request native 3840x2160 landscape 16:9 if supported. Clearly hand-drawn screenprint illustration: bold expressive black pen contours, simplified anatomy and shapes, flat limited spot colors, two-tone cel shading, rhythmic confident brush strokes, restrained dry-ink flecks. Not photographic, realistic, 3D, metallic engraving or cinematic painting. One full-bleed composition, no collage, no UI, no border, no text, no letters or legible runes, no logos, signatures or watermark. No forest, mountains, landscape, horizon or scenic backdrop. Keep the entire important subject comfortably inside x=15–85%, y=23–77%, including all extremities, so it survives a centered ultrawide crop. Do not fill the whole frame: retain generous calm empty areas and quiet top/bottom edges. Varied original compositions, no mandatory crown, circular ornament or knotwork frame. A solitary ancient hand-forged iron key lies diagonally from lower left toward upper center, loosely tied to a small folded strip of linen. The key has an irregular openwork diamond-shaped bow, a sturdy crooked shaft and two blunt asymmetrical teeth; a tactile practical object, no symbolic lettering. The linen trails in two short angular folds, not a long ribbon. Oversized but contained in the left-center third, about x=22–49%, y=34–68%; most of the right is empty charcoal. Quiet, austere, contemplative, soft steel on near-black. Palette ONLY #080a0b, #101315, #343d41, #798186, #cacccc, #d9dbdc, tiny #cbc2be. Flat ink and cloth planes, no realistic metal shine.
```

## 04-silent-wings

File: backgrounds/04-silent-wings.jpg

Ultrawide: backgrounds-ultrawide/04-silent-wings.jpg

Native source: `branding/sources/wallpapers/batch-04/stillwater-04-silent-wings.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Use case: stylized-concept. Create an entirely original Norse-fantasy desktop wallpaper from this written brief ONLY. No reference images, no image inputs, no borrowed character designs. Request native 3840x2160 landscape 16:9 if supported. Clearly hand-drawn screenprint illustration: bold expressive black pen contours, simplified anatomy and shapes, flat limited spot colors, two-tone cel shading, rhythmic confident brush strokes, restrained dry-ink flecks. Not photographic, realistic, 3D, metallic engraving or cinematic painting. One full-bleed composition, no collage, no UI, no border, no text, no letters or legible runes, no logos, signatures or watermark. No forest, mountains, landscape, horizon or scenic backdrop. Keep the entire important subject comfortably inside x=15–85%, y=23–77%, including all extremities, so it survives a centered ultrawide crop. Do not fill the whole frame: retain generous calm empty areas and quiet top/bottom edges. Varied original compositions, no mandatory crown, circular ornament or knotwork frame. Two Arctic terns in flight, clearly drawn graceful angular birds rather than realistic feather studies. One tern banks with wings gently open in the upper center, the other glides lower right in the opposite direction, forming a loose offset diagonal, not a ring and not mirror symmetry. The complete two-bird group occupies x=43–79%, y=28–70%, leaving a wide empty left half. Cool silver feathers, ink-black wing tips, muted slate shadows, no colored beaks. Calm and weightless against a blank near-black field. Palette ONLY #080a0b, #101315, #343d41, #798186, #cacccc, #d9dbdc.
```

### 01-ashen-stag ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/stillwater-01-ashen-stag-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```

### 02-the-iron-key ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/stillwater-02-the-iron-key-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```

### 04-silent-wings ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/stillwater-04-silent-wings-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```
