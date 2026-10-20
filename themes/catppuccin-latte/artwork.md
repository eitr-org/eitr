# catppuccin-latte Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/02-cloud-orchard.jpg`
- `backgrounds/03-porcelain-coast.jpg`
- `backgrounds/01-ribbon-hare.jpg`
- `backgrounds/04-wandering-greenhouse.jpg`


Batch 01: original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future additions use written briefs only, following `branding/ART-DIRECTION.md`, with no external image inputs.

## 02-cloud-orchard

File: backgrounds/02-cloud-orchard.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. An airy orchard of small rounded flowering trees on pastel terraces floating above a sea of clouds, gentle sunrise, tiny curved footpaths. Elegant gouache illustration with matte texture and precise shapes. Bright Catppuccin Latte palette #eff1f5, muted rose #dc8a78, lavender, soft teal #179299, blue #1e66f5 accents; predominantly light.

## 03-porcelain-coast

File: backgrounds/03-porcelain-coast.jpg

Prompt:

Original desktop wallpaper, ultrawide 21:9 horizontal composition suitable for 3440x1440. One full-bleed scene, no text, letters, logos, watermark, frame, collage, UI or existing franchise characters. Calm upper edge for desktop bar, balanced wide composition, fine textures and clearly readable silhouettes. Original arrangement, not a reproduction of a reference artwork. Sunlit white limestone coastal village with rounded terracotta roofs, delicate pink flowering vines, blue inlet and a distant sailboat, broad open sky. Refined hand-painted travel illustration, original architecture, pale airy mood. Latte #eff1f5, blue #1e66f5, rose #dc8a78, restrained green #40a02b.

## Removed in batch 04: 03-soft-contours

Replaced by `01-ribbon-hare` in batch 04; the original prompt is retained below as history.

Former file (removed): backgrounds/03-soft-contours.jpg

Reference-led character/graphic/object direction instead of generic city/nature vistas. Attached contact sheet was a mood, medium and palette reference only; output is a new single composition. Lanczos-upscaled to 3440 x 1440, as in batch 01.

Prompt:

Create ONE new original ultrawide 21:9 desktop wallpaper. The attached contact sheet is ONLY a reference for the theme's visual language, texture, subject category and palette, not an edit target. Do not copy its compositions, characters, logos or writing. Output a single full-bleed artwork, NOT a contact sheet, poster, screenshot or mockup. No lettering, text, signatures, watermarks, logos or border. Avoid city panoramas, mountain landscapes, forests, lakes, sunsets, architecture vistas and generic scenery. Spacious balanced desktop composition. Pure minimalist abstract layered flowing bands, sweeping horizontal asymmetric curves with gentle thickness and tactile matte paper grain. High-key Catppuccin Latte white #eff1f5, pale peach, dusty pink #dc8a78, diluted lavender, muted mint and pale blue. No landscape, objects, architecture, hard shadows or dramatic saturated colors. Graceful original curve arrangement, spacious upper half, subtle delicate soft shading. Closely reflect the calm pastel abstraction category of original color-fade.


## 04-wandering-greenhouse

File: backgrounds/04-wandering-greenhouse.jpg

Built-in image generation. Native output 1672×941, Lanczos-exported at
3840×2160 with a minimal 16:9 crop. Film-inspired atmosphere with an original
composition and characters; source and exact prompt retained in `references/`.

```text
Create one original full-bleed 16:9 desktop wallpaper requested3840x2160 orhighestavailable, Catppuccin Latte light palette. Hand-painted Japanese animation background inspired by the cozy magic, quiet adventure and emotional warmth of Howl's Moving Castle and Spirited Away, without copying a movie frame. An original charming wandering greenhouse-cottage on four slender brass bird-like legs, traveling slowly along a soft grassy meadow on the RIGHT half. An asymmetrical small cream plaster house, faded blue roof, compact glass conservatory full of pastel flowers, laundry fluttering and gently puffing crooked chimney, softly weathered whimsical mechanical details, modest scale, entirely new silhouette. A young adult traveler in simple cream coat and straw hat, small and seen from behind, walking alongside with a little suitcase; a tiny round original spirit peeking from a basket. Broad calm pale morning sky on left and top, a few soft clouds and distant soft blue hills, no busy scenery. Soft drawn ink outlines, delicate watercolor/gouache texture, painterly flat cel shading, expressive charming shapes, gentle sunlight. Strong Catppuccin Latte colors: warm pale #eff1f5 and cream sky, slate #4c4f69 outlines, cornflower #1e66f5 roof accents softened with sky blue, soft mauve #8839ef, muted pink #ea76cb flowers, sage #40a02b grass and ochre #df8e1d brass. Pastel and airy, never harsh saturated, preserve calm desktop negative space on the left, entire cottage and legs fully inside frame. No photorealism, no3D, no menacing monster machinery, no recognizable movie characters or exact film castle design. No lettering, signs, words, logos, watermark, signature, clock, UI or borders. One cohesive original illustrated wallpaper.
```

## 04-wandering-greenhouse — generated ultrawide variant

File: backgrounds-ultrawide/04-wandering-greenhouse.jpg

Generated with the built-in image tool as a panoramic expansion of the 4K
artwork, preserving the original subjects. Native output 1938×811;
Lanczos-exported at 3440×1440 with a minimal aspect-ratio crop. The 4K version
is unchanged. Native source and exact prompt: `references/wandering-greenhouse-ultrawide.json`.
## 01-ribbon-hare

File: backgrounds/01-ribbon-hare.jpg

Ultrawide: backgrounds-ultrawide/01-ribbon-hare.jpg

Native source: `branding/sources/wallpapers/batch-04/catppuccin-latte-01-ribbon-hare.png` (1672×941). Fresh built-in image generation from a written brief only, with no image inputs. The 3840×2160 export uses Lanczos resampling; the 3440×1440 export crops to fill without stretching or edge padding. These are exports, not native 4K generations. Rebuild with `python3 branding/sources/wallpapers/batch-04/export.py`.

```text
Use case: stylized-concept. Create an entirely original Norse-fantasy desktop wallpaper from this written brief ONLY. No reference images, no image inputs, no borrowed character designs. Request native 3840x2160 landscape 16:9 if supported. Clearly hand-drawn screenprint illustration: bold expressive black pen contours, simplified anatomy and shapes, flat limited spot colors, two-tone cel shading, rhythmic confident brush strokes, restrained dry-ink flecks. Not photographic, realistic, 3D, metallic engraving or cinematic painting. One full-bleed composition, no collage, no UI, no border, no text, no letters or legible runes, no logos, signatures or watermark. No forest, mountains, landscape, horizon or scenic backdrop. Keep the entire important subject comfortably inside x=15–85%, y=23–77%, including all extremities, so it survives a centered ultrawide crop. Do not fill the whole frame: retain generous calm empty areas and quiet top/bottom edges. Varied original compositions, no mandatory crown, circular ornament or knotwork frame. A graceful white hare suspended in a small diagonal leap above a loose spool of blue wool thread. Oversized expressive ears, long tucked hind legs, black ink linework, a few spare angular thread loops rather than a ribbon backdrop. Both hare and spool fully contained in x=49–78%, y=31–73%, generous empty left. Light-theme treatment: a calm pale paper field #eff1f5 with substantial dark ink accents #4c4f69 and #5c5f77; gentle sky-blue #1e66f5, rose #ea76cb and teal #179299, tiny warm gold #df8e1d. Preserve this light theme's airy mood and pale ground, while retaining bold black hand-inked contours, flat spot colors and Norse folk-print character. No landscape, cinematic sky or recognizable animated-film character. Not cute merchandise art or photorealism.
```

### 01-ribbon-hare ultrawide expansion

The ultrawide version uses a separately generated panoramic expansion of Eitr’s
own native illustration, exported to 3440×1440 with no stretched edge padding.
Source: `branding/sources/wallpapers/batch-04/catppuccin-latte-01-ribbon-hare-ultrawide.png` (1935×812).

```text
Expand and recompose this Eitr original artwork into a true ULTRAWIDE43:18 landscape wallpaper, requested3440x1440 or largest supported2.39:1 canvas. Preserve its SAME subject, character identity, anatomy, pose, colors, medium, lighting and original artwork style. Keep all important subject parts completely visible, including head/helmet, antlers, wings, ears, flowers, hands and objects. Uniformly reduce the subject within the frame if needed, never stretch it. Add natural seamless new painted/drawn background space mainly to the sides, continuing the existing background style, texture and light. Large calm breathing room for desktop windows. No repeated edge columns, smeared bands, mirroring, letterboxing, borders or abrupt seams. Preserve the existing subject composition as far as the new panoramic framing permits; do not add extra subjects, text, logos, signatures, UI or watermarks. This is an expansion of the supplied original, not a different artwork.
```
