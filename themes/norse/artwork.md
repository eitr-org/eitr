# Norse Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-eitr-runestone.png`
- `backgrounds/02-odin-allfather.jpg`
- `backgrounds/03-mimir-well-of-wisdom.jpg`
- `backgrounds/04-huginn-muninn.jpg`
- `backgrounds/05-valkyrie.jpg`
- `backgrounds/06-odin.jpg`
- `backgrounds/07-fenrir.jpg`
- `backgrounds/08-jormungandr.jpg`


The Norse theme follows EITR's Norse identity: Niflheim night, the green glow of
eitr (the primordial venom of the myths), aurora teal and violet, and bronze.

Default: backgrounds/01-eitr-runestone.png.

The runestone is original procedural artwork rendered at 3840 × 2160 by
`references/generate-wallpapers.py`. Its carved Elder Futhark strokes need no
fonts. The generator writes only the runestone wallpaper.
`references/build-vscode-theme.py` builds `vscode.vsix` from the same palette.

The carousel preview is original procedural aurora artwork. Replace it with a
privacy-safe desktop screenshot in this theme.

## 01-eitr-runestone

File: backgrounds/01-eitr-runestone.png

The bronze-gold EITR emblem inside a matching bronze ring of two Elder Futhark
rows, inscribed facing the centre like a runestone, under a faint aurora.

## 02-odin-allfather

File: backgrounds/02-odin-allfather.jpg

Generated with Codex's built-in image generator. Owner-supplied references
1, 4, 7 guided mood, texture and contrast only; no source artwork was copied.

Generated at 1935 × 812; Lanczos-upscaled to
3440 × 1440 PNG with a minimal centered aspect-ratio crop. Not a native
3440 × 1440 generation.

```text
Create one original full-bleed ultrawide 21:9 desktop wallpaper at 3440x1440, or the largest supported same-ratio canvas. Dark, intimidating, painterly Norse myth concept art with coarse visible brushwork, charcoal texture, deep chiaroscuro and hard selective rim lighting. Mostly near-black blue #0b1015 and deep fjord #18212b; restrained eitr green #7ee0b5 highlights, very subtle aurora teal #4fc3c9 and violet #a78bd6, aged bronze #c4914f metal and sparse frost white #e9eef1. Crushed atmospheric shadows, powerful silhouette, ominous sacred presence. Subject isolated in the right half/right third; left half calm nearly black negative space, top 10% quiet and empty, no important elements cropped. Close, graphic and subject-focused, not a scenic fantasy panorama. NO mountains, waterfalls, fjord vistas, castles, villages, floating cities, decorative landscapes or bright aurora skies. One artwork only, no text, letters, logos, watermarks, signatures, UI, borders, posters or collages; small carved runes on objects are allowed. Original Edda-based designs only, no resemblance to Marvel, God of War, Assassin's Creed Valhalla, Vikings TV or other film/game/comic characters. Attached images are mood/texture/contrast references ONLY: do not copy faces, poses, layouts, costumes, symbols, artwork, watermarks or signatures. Anatomically coherent eyes, hands and animal heads.

Odin, an ancient terrifying wanderer, in a close chest-up three-quarter portrait on the right. Deep rough dark hood, no crown, no throne. Long unkempt silver beard, aged gaunt distinct face with realistic proportions, worn leather patch fully covers his left eye; the one visible eye is dim eitr green, with one coherent pupil and natural eyelids. One hand holds an ash spear close beside his shoulder; the bronze tip fits completely below the quiet top margin. Exactly two ordinary black ravens beside his shoulders, their heads separated clearly from the human silhouette: each has one normal smooth raven head, one closed black beak, no human face, no teeth, no extra eyes or beaks. Both ravens perched, folded wings, no flying bird. Feathers dissolve subtly into charcoal dust and black mist at the edges. Only smoky black backdrop and tiny green motes. Severe, mysterious, unsettling, detailed face and raven anatomy; all focal features readable without becoming bright.
```

## 03-mimir-well-of-wisdom

File: backgrounds/03-mimir-well-of-wisdom.jpg

Generated with Codex's built-in image generator. Owner-supplied references
1, 5 guided illustrative marks, mood and contrast only; no source artwork was copied.

Generated at 1935 × 812; Lanczos-upscaled to
3440 × 1440 PNG with a minimal centered aspect-ratio crop. Not a native
3440 × 1440 generation.

```text
ONE original 21:9 ultrawide EITR wallpaper, requested 3440x1440. STYLIZED DARK FANTASY ILLUSTRATION, emphatically NOT photorealistic or hyperrealistic. Hand-painted charcoal, ink and rough gouache aesthetic: broad visible strokes, dry-brush edges, simplified angular shapes, expressive silhouettes, limited detail, flattened graphic shadow shapes. No rendered skin pores, individual hair strands, photographic lighting, shiny 3D rendering, intricate armor microdetail, or realistic portrait finish. Mature, grim and powerful, not cute or cartoon comedy. Mostly near-black #0b1015 and deep blue #18212b with a FEW glowing eitr-green #7ee0b5 accents; restrained teal #4fc3c9, violet #a78bd6, bronze #c4914f and frost-white #e9eef1. Strong dark silhouette on right half; calm nearly black left half and upper 12% left empty for desktop controls. All faces, bird heads and key objects BELOW that top margin. Backdrop is abstract ink washes and smoke ONLY: no mountains, waterfalls, cities or landscape panorama. Full bleed, no border, text, logos, signatures, watermark, UI or collage. Original Edda-based Norse designs, never Marvel, God of War, Assassin's Creed or any other entertainment franchise. References guide ONLY mood, loose illustrative marks, dissolving edges and contrast, never copy faces, costumes, compositions or symbols. The intended result reads as an expressive painted illustration even at thumbnail size, NOT a photograph of a fantasy character.

Mímir: a sacred eerie still life, an ancient preserved head with broad silver beard shapes on the rim of a black well, no body, neck hidden by herbs, no blood or wounds. Expressive aged face painted in a few restrained rough planes with barely visible green eyes. Bronze beard rings reduced to simple muted marks. A small patch of dark water shows a single sacrificed eye as a subtle green almond-shaped glint. One huge twisted root suggested behind in shadow. Everything dissolves to black on the left. Sparse green smoke; no ravens, no scenery. Mysterious ink-and-gouache illustration, no realistic skin texture.
```

## Graphic illustrations

Files 04–08 are native ultrawide drawn illustrations, following
`branding/ART-DIRECTION.md`: flat colors, bold ink and black negative space.
Crowns are optional; Fenrir and Jörmungandr are unframed. `references/graphic-artwork.json` records sources, prompts and
actual dimensions; generated outputs were not enlarged to 3440×1440.
The website generates its WebP copies from these same theme sources; its
Yggdrasil illustration lives in `website/assets/norse/`.
