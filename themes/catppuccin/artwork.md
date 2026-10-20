# catppuccin Artwork

## Current 4K collection

Shipped wallpapers use 3840×2160 (16:9). Existing raster art is cropped to
keep its main subject and Lanczos-resampled; this is not native 4K generation.
Earlier resolution notes below describe the original generation, not the current
exports. See `themes/artwork-4k.json` and `tools/export-wallpapers-4k.py`.

- `backgrounds/01-spirit-station.jpg`
- `backgrounds/02-lunar-conservatory.jpg`


Batch 01: original AI-generated wallpapers, installed at 3440 x 1440 PNG.

Generated with the built-in image generator, then Lanczos-upscaled with a minimal centered aspect-ratio crop. These are not native 3440 x 1440 generations.


Future batch: number new wallpapers after the last one and continue the reference-led visual language, without reproducing an existing composition or franchise.

## 02-lunar-conservatory

File: backgrounds/02-lunar-conservatory.jpg

Prompt:

Original desktop wallpaper, stylized-concept illustration. Ultrawide 21:9 landscape composition. A small abandoned glass botanical observatory on a rocky moon plateau, luminous pastel plants inside, immense quiet starry sky, distant thin planetary rings low on the horizon. No astronaut, no existing fictional characters. Elegant hand-painted animation background with crisp silhouettes and subtle grain. Catppuccin Mocha palette: dark base #1e1e2e, dusty lavender, #89b4fa blue, #f5c2e7 pink, small mint #94e2d5 highlights. Observatory on right third, expansive calm space left and center, subdued top strip for desktop bar. No text, logo, watermark, border, collage. Entire output one wide wallpaper, not a mockup.

## 01-spirit-station

File: backgrounds/01-spirit-station.jpg

Built-in image generation. Native output 1672×941, Lanczos-exported at
3840×2160 with a minimal 16:9 crop. Film-inspired atmosphere with an original
composition and characters; source and exact prompt retained in `references/`.

```text
Create one original full-bleed 16:9 desktop wallpaper, requested3840x2160 orhighestavailable. A cozy hand-painted Japanese animation background inspired by the feeling of Spirited Away and Howl's Moving Castle: wonder, gentle everyday magic and a slightly mysterious journey, not a reproduction of a movie frame. Scene: a tiny quaint lantern-lit spirit railway waiting room and wooden platform on the RIGHT third, with a small original blue-and-cream train stopping quietly beside it, low mist and calm dark water fading across the left. A few small original round woodland spirits waiting with bundles; no recognizable film characters. Warm windows, one hanging red paper lantern, a distant whimsical wandering cottage with brass legs barely discernible through mist on far right. Keep architecture modest and charming, not enormous and ornate. Spacious calm composition, large dark quiet space left and upper edge for desktop windows. Delicately inked outlines, soft gouache-like brush texture, clean expressive silhouettes, flat painterly light, clearly drawn anime background; no photorealism, no3D. Catppuccin Mocha palette: dominant midnight mauve #1e1e2e and #181825, dusty lavender #cba6f7 and blue #89b4fa, muted pink #f5c2e7, mint #94e2d5 and small warm cream #f9e2af window lights. Brooding but comforting, pastel luminosity kept restrained. No text, signs with writing, letters, logos, watermark, signature, UI or borders. Original composition with the nostalgic magical atmosphere of those films.
```

## 01-spirit-station — generated ultrawide variant

File: backgrounds-ultrawide/01-spirit-station.jpg

Generated with the built-in image tool as a panoramic expansion of the 4K
artwork, preserving the original subjects. Native output 1937×812;
Lanczos-exported at 3440×1440 with a minimal aspect-ratio crop. The 4K version
is unchanged. Native source and exact prompt: `references/spirit-station-ultrawide.json`.
