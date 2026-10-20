# Eitr artwork direction

## Approved visual language

Wallpapers and website illustrations use clearly drawn Norse fantasy poster
art. The owner approved the graphic Sköll/Hati, Huginn/Muninn and Yggdrasil
studies: bold contours, flat color areas, expressive shapes and knotwork crowns.
The durable reference is the Norse wallpaper `themes/norse/backgrounds/04-huginn-muninn.jpg`.

- Use strong visible black pen contours, simplified anatomy, two-tone cel
  shading, rhythmic flowing strokes and restrained ink splatter.
- Pure black is the primary background. Leave useful negative space and keep
  subjects readable against it. Green is optional, not the overall color cast.
- Use a limited palette of ivory, slate blue and muted ochre; sun/fire scenes
  may use burnt orange. Small emerald accents are appropriate when intentional.
- Crowns, braided rings, interlace and chains are optional accents, not a
  universal frame. Vary composition, brush treatment and palette by subject.
  Some images should have no ornament at all. Do not repeat one arrangement
  across an entire wallpaper set just because one example was approved.
- Subjects are original interpretations, not game/movie likenesses. Ornament
  is artistic; do not claim historical authenticity for invented symbols.
- Keep subjects fully in frame. Shipped wallpapers target 3840×2160 (16:9), with
  a 3440×1440 (21:9) version for ultrawide monitors (themes/ARTWORK.md);
  website heroes need quiet space for copy and mobile cropping. Existing raster
  wallpaper conversions crop around the main subject and use Lanczos resampling.
- No landscape backdrop by default: no trees, lakes, mountains or scenic
  horizon. A tree can be the subject (Yggdrasil) without a surrounding forest.

## Avoid

Photorealism, 3D rendering, realistic skin/fur/metal, cinematic volumetric
lighting, metallic engraving masquerading as drawing, all-green scenes,
unrequested scenery, lettering, watermarks and copied reference compositions.
Do not use external reference images as distributed assets or remove their
watermarks; use them only to guide an original composition.

## Reusable prompt

> Original Norse fantasy screenprint illustration with bold hand-inked black
> contours, stylized expressive shapes, flat limited spot colors and two-tone
> cel shading. Pure black background with useful negative space. Ivory,
> a subject-specific limited palette. Choose a distinct composition and ink
> treatment; add ornament only when requested or useful. Clearly drawn,
> not realistic, photographic, 3D or
> metallic engraving. No landscape backdrop, words, watermark or copied
> character design. Keep the subject fully in frame.

Append the subject and composition. Supply an approved graphic study as the
style reference, not earlier realistic paintings. Request the intended aspect
ratio and export resolution, then inspect and report the actual pixel dimensions.
Keep review drafts separate from production assets. Promote selected artwork
with stable names, provenance and synchronized generators/consumers.

## Written-brief replacements

The selected batch 04 replacements in `themes/artwork-batch-04.json` were
generated from written briefs only, with no reference-image inputs. Approved
native masters and their export script live in
`branding/sources/wallpapers/batch-04/`. Light themes retain their own pale
paper ground and limited palettes. Ultrawide exports crop to fill without stretched pixels or side padding.
Choose the crop around the main subject; when its silhouette cannot fit,
create a separately composed ultrawide version rather than stretching edges. For Afterglow and Moss only, the owner explicitly overrides the flat ink style:
Afterglow uses soft, richly lit painterly Norse portraits in amber, ember and
rose on near-black; Moss uses dark chiaroscuro Norse oil painting in olive,
moss, bone and umber. They retain original written-brief subjects, no franchise
likenesses and no reference-image inputs. Their approved batch 04 replacements
are recorded with the other native masters.
