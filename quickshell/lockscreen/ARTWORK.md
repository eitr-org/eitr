# EITR lockscreen artwork provenance

Nine designs use installed system fonts, procedural QML/SVG and still
backgrounds. No bundled fonts or videos are required. Preview using
`bash quickshell/lockscreen/scripts/gallery.sh`; authentication and power actions
are disabled. Preview images contain only mock EITR account/session data.

## Code and asset provenance

Clockwork is original procedural QML. Other layouts are adapted from the
Qylock-based designs already in this repository; their GPL notices and
`LICENSE` remain applicable. Material retains its existing abstract color
families and card layout, with an original EITR rune-ring ornament taken from
`branding/svg/eitr-rune-ring.svg`. Rune strokes are decorative, not a translation.
Clockwork adds Elder Futhark marks around its dial and below its rolling tapes.
Nothing retains its original three-card arrangement and procedural dot clock.

## Resolution and exports

All shipped PNG backgrounds and previews are **3840×2160, 16:9**. Material SVGs
have the same intrinsic dimensions while retaining scalable geometry. QML
renders at the actual screen resolution; Clockwork scales with 4K rather than
capping its instruments at their smaller-screen size.

The built-in image generator produced the Girl artwork below at less than 4K.
Native sources are retained in `references/girl-coffee.png` and
`references/girl-pillow.png`. `references/build-artwork.py` uses a centered
aspect-ratio fit and Lanczos resampling to export 3840×2160 PNGs. These are 4K
exports, not claims of native 4K image generation. The same script builds
Material's ornamented SVGs from `references/material-{light,dark}.svg`.

`references/render-previews.py` renders each full design at 3840×2160 using
`render-preview.qml`, an offscreen screen and mock authentication. It never
captures the real desktop or invokes a session lock.

## Girl · Coffee

Asset: `themes/girl-coffee/background.png`.
Fresh built-in illustration generated from a written brief only, without any
input or reference images. The owner approved the fair-skinned, blonde woman
in everyday Norse-inspired clothing, seated with her drink on a cushion.
Native output: 1672×941, retained as `references/girl-coffee.png`; exact prompt
and native hash are also in `references/girl-coffee.json`. The 3840×2160 PNG is
a Lanczos export. The left side remains quiet for the actual clock/login card.
Rebuild just this background with `python3 references/build-artwork.py girl-coffee`
and its mock offscreen preview with `python3 references/render-previews.py girl-coffee`.

```text
Generate a fresh original illustration solely from this written brief. No input images, no visual references and no recognizable fictional characters. Landscape 16:9, request native 3840x2160 if supported. Clearly drawn artwork with confident hand-inked contours, flat limited spot colors and simple two-tone cel shading. No photorealism, 3D, cinematic lighting, words, lettering, logos, signature, watermark, borders or UI. A calm cozy illustration of a fair-skinned adult young woman with long golden-blonde hair in one loose thick braid, a few soft loose strands, and a gentle relaxed smile. She sits sideways with legs comfortably folded on a simple dusty-rose floor cushion. She wears a cream linen tunic and muted teal wool apron dress with understated woven geometric hem trim and one small bronze clasp, everyday Norse-inspired clothing, no armor or weapons. Gentle oblique three-quarter view, her gaze resting on a warm clay mug held comfortably in one hand near her knee, the other hand resting on the cushion. A short curl of steam, warm peaceful expression. Entire figure, cushion and mug contained in the RIGHT third, x=58–87%, y=26–78%. The LEFT HALF and top 20% must be calm empty muted teal for an actual clock and tall login card: do not draw those UI elements. Delicate expressive ink contours, simplified features and anatomy, soft flat cel shading, no realistic skin. Palette muted teal #6eb3ac background, cream #fdfaf6, dusty rose #da9ead, natural pale golden blonde, fair ivory skin, deep ink #324746. Only the woman and floor cushion against a plain teal field; no scenic or furnished-room backdrop. Fresh new illustration from text only.
```

## Girl · Pillow

Asset: `themes/girl-pillow/background.png`.
Built-in image generation edited the previous EITR pillow illustration. The
composition keeps the top and bottom quiet for the real clock and login field.

```text
Preserve the delicate pastel anime medium, pale cool-gray background, adult
woman's short dark-brown bob, sleepy closed eyes and gentle smile, curled-up
pose hugging a pale-blue pillow and the surrounding cream/lavender pillows.
Replace modern sleepwear with a modest cream linen sleeping tunic and a loose
lavender wool wrap, soft socks, subtle woven Nordic trim, one bronze clasp and
a small temple braid. No weapons, armor, horns, aggression, landscape, text,
UI or watermark. Keep the full woman-and-pillows cluster small and centered,
inside x=30–70%, y=34–72%, leaving the top 32% and bottom 25% plain for controls.
Landscape 16:9, same cozy sleepy mood, clearly drawn rather than realistic.
```

## Theme Wallpaper

`themes/theme-wallpaper/Main.qml` adapts the previously shipped Sword layout,
retaining its GPL provenance. The background is resolved from the owner's current
desktop selection at launch; no personal wallpaper is copied into this repository
or into SDDM. The public 3840×2160 preview uses
`themes/eitr/backgrounds/02-eitr-runestone.png`, whose provenance is documented
in `themes/eitr/artwork.md`. The selected wallpaper keeps its native resolution;
Qt scales/crops it to the lockscreen surface without generating a second copy.

## Eitr

The default design for fresh installations. Original QML presentation on a pure
black ground (dark themes), so an OLED leaves those pixels off.

- **Wordmark:** a byte-identical copy of `branding/svg/eitr-wordmark.svg` for
  self-contained SDDM packaging, filled with the theme's accent; no logo paths are
  redrawn.
- **Rune ring:** the boot splash's (`distro/plymouth/eitr/export.py`): the 24 Elder
  Futhark letters in Noto Sans Runic and runestone gold `#c4914f` with a soft glow,
  drawn as text so they stay sharp while turning. It ticks six degrees each second,
  a turn per minute, over a translucent dark disc.
- **Clock:** hours and minutes only, in Eitr's own Norse glyphs
  (`themes/eitr/NorseGlyphs.js`): digits, colon and A/P/M built from the wordmark's
  parts (thick even strokes, straight stems, 30° and 45° diagonals, flat cut ends,
  no curves), drawn as vector strokes.
- **Sky:** `shaders/sky.frag` draws a starfield in three sizes and a Milky Way band
  with dust lanes once (no time input, so its layer is reused); a few brighter
  stars glow. Thirty stars on top scintillate quickly and gently without fading
  out, and now and then a shooting star crosses the upper sky.
- **Aurora:** the desktop's single `quickshell/desktop-bar/shaders/aurora.frag.qsb`,
  drawn as the live wallpaper draws it (`LiveWallpaperScene.qml`): half resolution
  scaled twice, with time advancing every 50 ms at twice the wallpaper's drift, in
  fixed northern-lights greens rising to teal and violet, with a gentle saturation
  boost. Pale themes tint the curtain alpha with a ColorOverlay instead.
- **Password field:** no placeholder; a block caret in the accent. Each typed
  character carves one rune in typing order (never derived from the character, so
  only the length shows): it falls, lands white-hot with a flash and sparks, jolts
  the field and cools to gold. Arrows, Home and End move the caret; Backspace and
  Delete crumble the rune beside it into falling pieces. Selection is off, so every
  edit is a plain insert or delete.
- **Unlock:** `unlockEffect` in `theme.conf` picks `lightning` (default) or
  `bifrost`. Lightning is the website's hold-to-strike bolt
  (`website/src/scripts/realm/mjolnir-charge.ts`): a jagged bolt from the top to
  the centre, re-rolled once at 140 ms and faded by 420 ms, a faint 90 ms flash and
  a small burst where it lands; then `shaders/burn.frag` burns the lockscreen away
  from the centre like paper, a ragged circle with a glowing ember rim and charred
  edge. Bifröst drops a spectrum beam down the middle that splits and opens like a
  gate.

Reduce motion holds every layer still and skips the strike, crumbling and unlock
effect. The caret blinks on a timer, never a looping animation, so the scene
redraws about twenty times a second instead of at the monitor's refresh rate.
`shaders/build.sh` regenerates the brand, sky and burn shaders; the desktop owns
the aurora source and bytecode. Offscreen review executes the canonical aurora
GLSL through surfaceless Mesa OpenGL; it does not establish hardware GPU cost.
Preview unlock frames reveal only a synthetic desktop, and real unlock snapshots
stay in memory. No photos, new generated artwork, bundled fonts or video are used.
