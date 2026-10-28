# Eitr artwork direction

## Approved visual language

Wallpapers and website illustrations use clearly drawn Norse fantasy poster
art. The owner approved the graphic Sköll/Hati, Huginn/Muninn and Yggdrasil
studies: bold contours, flat color areas, expressive shapes and knotwork crowns.
Durable references are the website illustrations in `website/assets/norse/`
and the unframed Fenrir in `themes/ragnarok/backgrounds/05-fenrir.jpg`.

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

## Batch 07 realm exception

For the realm wallpapers in `themes/artwork-batch-06.json` and `artwork-batch-07.json`, the owner
explicitly permits scenic backgrounds and requests varied media per image.
Follow each recorded rendering style literally: ink, gouache, cel shading,
storybook and poster work must remain visibly drawn, with simplified shapes,
linework or flat colour at thumbnail size. Painterly scenes retain visible
brushwork; only requested realistic treatments may look photographic.
Use original written-brief compositions and characters without image inputs,
readable runes, lettering, logos or signatures. Keep the top approximately
6% calm for the bar. The exception covers only those realm batches.

## Batch 08 Ragnarök exception

The owner explicitly approves scenic painterly cinematic dark fantasy for the
three Ragnarök selections recorded in `themes/artwork-batch-08.json`: Blood
Eclipse, Fenrir Devours the Sun and Dying Yggdrasil. Use visible brushwork,
obsidian and charcoal darkness, restrained blood crimson and sparse muted gold.
Generate panoramic compositions from written briefs only, with complete disks,
coherent connected wolf jaws and full tree canopies inside the frame. Extra
width is calm dark negative space, with the top approximately 6–8% quiet for
the bar. No lettering, runes, logos, watermarks or image references. This
exception applies only to batch 08. Native masters and reproducible exports
live in `branding/sources/wallpapers/batch-08/`.

## Eitr batch 09

The owner approved Primordial Drop, Élivágar and Venom Rootlight in painterly
cinematic dark fantasy, an explicit exception to the ink illustration and
no-scenery defaults for this batch. Native owner-approved PNGs are preserved
byte-for-byte; ultrawides are new panoramic compositions from the same final
written prompts, with only Eitr’s emblem used as the drop’s shape reference.
Exact prompts, hashes, sizes and framing: `themes/artwork-batch-09.json`.
Masters and reproducible exports: `branding/sources/wallpapers/batch-09/`.
Eitr’s order is Drop (default), Runestone, Élivágar, Rootlight; the existing
preview is preserved. Runestone and its live layers are now numbered 02.
