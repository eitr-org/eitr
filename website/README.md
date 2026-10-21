# Eitr website

The Astro + CSS website, published at **https://eitr.info** (and www) by the
Cloudflare Worker `eitr`, which serves the built files. Cloudflare's Workers Builds
rebuilds it on every push to `main` that touches what the site reads; other
branches get preview builds. The domain's DNS and the `reports@eitr.info` and
`contact@eitr.info` email forwarding are also on Cloudflare's free plan.

| Worker build setting | Value |
| --- | --- |
| Repository, branch | `eitr-org/eitr`, `main` |
| Path (root directory) | `/website` |
| Build command | `npm ci && npm run build` |
| Deploy command | `npx wrangler deploy --assets=./dist --name=eitr --compatibility-date=2026-10-01` |
| Preview command | `npx wrangler versions upload --assets=./dist --name=eitr --compatibility-date=2026-10-01` |
| Build watch paths | `website/**`, `distro/release.json`, `distro/RELEASES.md`, `themes/**`, `branding/**`, `quickshell/desktop-bar/handbook/**`, `distro/software.json`, `distro/packages.txt` |
| Node.js | from `website/.node-version` |

The build reads the release, roadmap, theme artwork, branding and the generated
English Handbook catalog from the rest of the repository, hence the watch paths.
Add the Handbook and software-manifest paths to the existing Workers Builds
watch list before shipping these routes; the repository cannot change that dashboard setting by itself. The `workers.dev` addresses are off;
eitr.info and www.eitr.info are the Worker's custom domains.

## Run on your Mac

Use Node.js 22.12+ (the current Mac's Node 24 works). From the repository root:

```sh
cd website
npm ci
npm run dev
```

Open the Local URL printed in the terminal, normally http://localhost:4321.
Changes appear automatically. This Astro version runs the development server
in the background. Stop it with `npm run stop`.

```sh
npm run build     # creates static HTML/CSS/assets in dist/
npm run preview   # serves the production build locally
```

## Your first Astro project

- `src/pages/index.astro`: the homepage. Files in `pages/` become routes.
- `src/pages/about.astro`: `/about/`, the distribution's identity, audience and beta scope.
- `src/pages/features.astro`: `/features/`, current desktop, development and recovery capabilities.
- `src/pages/installation.astro`: `/installation/`, target requirements and hardware evidence.
- `src/pages/development.astro`: `/development/`, included tools, optional installs and integrated account/AI workflows.
- `src/pages/guide.astro`: `/guide/`, searchable chapter index and canonical installation/VM links.
- `src/pages/guide/[chapter].astro`: `/guide/<chapter>/`, the server-rendered public Handbook.
- `src/data/handbook.ts`: one adapter for the existing English Handbook catalog and its web links.
- `src/data/site-pages.ts`: public page names, metadata and sitemap entries.
- `src/pages/sitemap.xml.ts`, `robots.txt.ts` and `llms.txt.ts`: static discovery endpoints.
- `tests/product.browser.mjs`: keyboard/mobile discovery, package evidence, Handbook search and release messaging.
- `tests/discovery.browser.mjs`: every public route without JavaScript, metadata, links and canonical chapter-text parity.
- `src/layouts/Layout.astro`: shared HTML, navigation, footer, and bundled fonts.
- `src/components/InnerPage.astro`: wide-screen illustrations and section contents, with missing heading anchors generated from their text.
- `src/scripts/page-navigation.ts`: mobile menu focus/scroll handling and the current section in the contents list.
- `src/scripts/effects.ts`: scroll reveals, parallax, and cursor lighting.
- `src/components/SkySwitch.astro`: the day/night switch and Sköll/Hati sky transition.
- `src/styles/global.css`: the visual system, responsive layout, and reduced motion.
- `public/`: assets served directly, such as `/branding/eitr-wordmark.svg`.

An `.astro` file starts with an optional `---` block for build-time JavaScript.
Below that is HTML-like markup; `{expressions}` insert values. Components render
into static HTML. Small browser scripts add visual effects;
there is no React runtime or server required in production.

## Assets and screenshots

`npm run dev` and `npm run build` synchronize the approved branding from
`../branding/svg/` and generate WebP artwork and a theme catalog from `../themes/`.
Edit those canonical sources and run `npm run sync-assets` during development.
Website copies are generated consumers, not independent logo or artwork sources.
Generated `public/art/` and `src/data/` files are Git-ignored.

The homepage's tour (`#tour`) and its Developers and Gaming sections show real
screenshots from `public/shots/`, captured on the developer's own 2560×1080
desktop with the Afterglow theme: an empty workspace, Do Not Disturb on and the
pointer hidden, each panel or menu opened through the bar's IPC and taken with
`grim`, then cropped to 16:9 around what it shows. Never capture WiFi, Bluetooth,
Weather, AI Usage, Clipboard History, accounts, folder pickers, notifications or
open windows. Keep the shots free of accounts, network names, tokens, private
notifications and project content, save them as WebP and describe them in the
alt text. Everything else uses Eitr's drawn Norse illustrations and the wallpaper
catalog.

The website uses a dark Norse "Blood & Iron" presentation (black-iron surfaces,
bone text, blood-crimson and tarnished-gold accents) with serif/runic
typography. Motion respects reduced-motion preferences. Keep installation claims
consistent with the canonical distro guides; the download button reads
`src/data/download.json`.

The layout, copy, illustrations, colors, and assets here are Eitr's own.

Above 1100 px, information pages and Handbook chapters pair their reading column
with existing artwork and a sticky section list. Below the 1200 px navigation
breakpoint, Menu opens the full-screen navigation with the release badge (the Day/Night
switch stays in the header); Escape, Close or a link dismisses it and restores focus. Without
JavaScript, the existing scrollable navigation remains available.

## Day and night

The header’s Day/Night switch changes the whole site between black iron and
warm parchment. Hati chases away the moon for daylight; Sköll chases away the sun
for night. A small spectral wolf descends straight down with the sun/moon moving just ahead
of its mouth. The whole wolf stays ahead of the V tip with a visible gap after its tail,
and is drawn above the glow and trails. Its two
luminous trails form a widening V behind it; the new theme fills the V's
interior, with its point following the wolf until every corner is revealed.
The 2.5-second flight reuses the original drawn wolf sprites and a View
Transition (an immediate palette change is the fallback without that API).
It works at any scroll position and updates every section without moving the
visitor. Transition captures are bounded to the current viewport and restore
the saved scroll position when finished. The switch stays disabled until the whole transition finishes.
Reduced
motion changes the palette immediately. Hidden tabs finish the change and cancel
the transition. A sustained CC0 solo wolf howl accompanies animated changes
independently of the music toggle, keeping its full four-second playback after
the visual effect ends. Credits live in `public/audio/CREDITS.md`.
A local-only `eitr-appearance` preference remembers the choice
across pages and reloads; blocked storage falls back to dark without errors.

`assets/chase/*-bite.png` are original two-frame transparent sprite sheets;
`sync-art.mjs` exports WebP while preserving the equal frame bounds. Celestial
bodies are CSS shapes. This animates the jaws, not the legs.

`src/components/NorseSymbol.astro` owns original decorative line symbols for
ravens, tree, hammer, spear, serpent and ship. External links open in a new tab;
local site navigation stays in the current tab.

With Chrome, Chromium or Google Chrome installed and the site served
(`npm run build && npm run preview`), run the browser tests:

```sh
npm test                # every browser suite, including day/night and all-page accessibility
npm run test:browser    # effects, navigation, music, responsive widths
npm run test:sky        # day/night, persistence, keyboard, motion and light-mode accessibility
npm run test:a11y       # axe-core: core pages and representative Handbook chapters, both themes and screen sizes
```

Set `EITR_BROWSER_EXECUTABLE` if the executable is outside the usual Mac/Linux
paths, and `EITR_SITE_URL` to test a different local port. The accessibility
suite fails on serious or critical violations.

The version badge, status texts and roadmap come from `distro/release.json` and
the release table in `distro/RELEASES.md`, copied into `src/data/` by
`npm run sync-assets` (part of `dev` and `build`). The site adds only each
codename's myth line, in `src/pages/index.astro`. Consecutive releases with the
same codename share one entry and a compact milestone list, with the current
release marked on its own row.

## Mjölnir entrance study

`/intro/` is an isolated lightweight SVG/CSS animation study: hammer strike,
lightning/cracks, debris and the Eitr logo reveal. It plays once and has a Replay
button. Reduced motion displays the finished mark without impact effects.
The homepage embeds the same scene to the right of its headline on black,
playing once on arrival; on narrow screens it stacks beneath the text.
`src/components/MjolnirScene.astro` owns both versions so fixes stay synchronized.

The enlarged hero logo is a keyboard-accessible button. Activating it plays one
of seven original SVG lightning patterns, selected randomly without consecutive
repeats. Bursts do not overlap; reduced-motion visitors see the static logo.

The hero's click-triggered lightning overlay spans the entire hero without
blocking links. The page uses near-black surfaces, with crimson and gold kept mainly in borders,
symbols and small accents.

Lightning is anchored to the emblem's measured center on each activation. A
single 180 ms white viewport flash peaks at 10% opacity; it is click-through,
shares the burst cooldown, and is disabled/cancelled with reduced motion.

The full outer liquid contour masks the click lightning and its white glow,
including the E counter. Bolts become visible only outside that boundary; the
mask follows the rendered emblem size. The hero scene uses the larger hammer
and logo sizes on desktop, with a separate narrow-screen scale.


## Ambient preview effects and music

The shared Mjölnir scene adds a slow silver highlight tracing the logo's outer
contour, subtle pointer depth across the whole hero (fine pointers only). A shared, fixed
layer adds 24 sparse orange/red embers rising and fading behind every page’s content.
The 3 px particles remain behind text, logos and opaque panels. The logo shimmer
pauses outside the viewport; particles and shimmer pause in hidden tabs and
is disabled with reduced motion. Pointer depth resets on exit or reduced motion.
Decorative Norse symbols briefly illuminate once when they enter the viewport.

The homepage sound control starts off on every load and fetches audio only after
activation. It plays the unedited, locally hosted “Wild West Vikings” by Alexander
Nakarada at 20% volume, repeating during playback. Hidden tabs pause playback;
returning requires another click. The icon toggle sits in the hero’s bottom-right corner; its accessible name states
whether music is on or off. Credits and CC BY 4.0 links open beside the
control and in `public/audio/CREDITS.md`. The track is free with attribution;
no paid license is used. The recording retains its separate CC BY 4.0 license.

Headline accents alternate blood crimson and tarnished gold. The hero headline is white, with animated Bifröst color on the Eitr name.
Eitr names in prose and runic wordmarks share a six-second rainbow cycle, except for
the white header wordmark. The main liquid emblem is white.
The roadmap’s Bifröst heading runs from bone through gold to crimson;
forced-color mode retains readable solid text.

The lightning button accepts pointer clicks on the emblem’s outer silhouette
and runic wordmark only. Empty scene space stays inert; keyboard activation
remains available. Hero-wide pointer depth is independent of the click target.

Section links (Begin, Explore and header section navigation) play a brief,
bright, full-viewport Bifröst wash during native anchor scrolling. The rainbow
shifts within the fixed overlay, keeping every screen edge covered throughout. Links keep their URL,
history and keyboard behavior. Repeated clicks replace the current sweep;
reduced motion and hidden tabs cancel it. External links and the skip link do
not trigger the effect.


## Jörmungandr background passage

The homepage occasionally shows a small, headless section of a scaled serpent
body behind its content. One of five local areas is chosen without consecutive
repeats; the body never crosses the entire screen. The first pass starts after
5 seconds, lasts 8.5 seconds at low opacity, then waits 5 seconds before
another pass. SVG geometry and a scale pattern keep it lightweight. Hidden tabs,
offscreen heroes and reduced motion cancel both passes and pending timers.


## Ragnarök screen bite

Type `ragnarok` outside text fields to summon an angry, face-only Fenrir.
The aligned transparent sprite switches from a snarl to open jaws, lunges
toward the viewer, then closes teeth over the full viewport. A brief black
pause leads into the Eitr rebirth before returning to the page. Click or Escape
skips the sequence. Reduced motion uses only the quiet rebirth; hiding the tab
cancels the sequence. The effect waits for the sprite to load, and falls back
to the quiet rebirth if loading fails. It adds no autoplay audio.

`assets/ragnarok/fenrir-bite.png` is the canonical two-frame source;
`assets/ragnarok/ARTWORK.md` records its prompt and license. Asset sync exports
`public/art/fenrir-bite.webp` without changing frame alignment or transparency.
Run `npm run test:ragnarok` against the local preview to check the sequence,
dismissal, mobile sizing, reduced motion and missing-art fallback.

## Interactive Yggdrasil

Before the six promises, the approved Yggdrasil illustration holds nine realm
buttons. Each opens a native modal dialog about a different part of Eitr:
desktop shell, everyday flow, themes, preferences, Arch and updates, account
tools, the Handbook, installation or recovery. The realm associations are a
website navigation concept, not a historical map. Mobile uses a two-column
button grid over the same tree. Dialogs support keyboard focus, Escape,
outside click and a close button, returning focus to the selected realm.
Section links close the dialog before native scrolling and the Bifröst sweep.

## Realm effects

`src/scripts/realm/` and a few components add the interactive effects. All of
them follow `motion.ts`: nothing moves under reduced motion or in a hidden tab,
and lightning anywhere announces an `eitr:strike` event.

- **Mímir's well** (`mimir-well.ts`): hovering a theme card ripples it and
  tints the site with that theme's colors; clicking it opens the still wallpaper
  (`theme-viewer.ts`, full-size copies generated by `sync-art.mjs`).
- **Charge Mjölnir** (`mjolnir-charge.ts`): hold the mouse on empty space, the
  cursor hides behind gathering sparks, and release strikes lightning that
  cracks the page where it hit.
- **Wield Mjölnir** (`wield-mjolnir.ts`): drag the hero logo and it becomes the
  scene's Mjölnir, head aimed at where the logo was; release to strike there and
  replay the arrival impact. The same hammer, with the logo inlaid on its head,
  strikes on arrival (`MjolnirScene.astro`). `npm run test:mjolnir` checks it.
- **Aurora sky** (`AuroraSky.astro`): daylight uses narrower emerald/violet
  pigment curtains on parchment; night keeps luminous ribbons. The WebGL
  curtains drift independently of the pointer and update immediately when the
  appearance changes.
- **Carved runes** (`RuneCarving.astro`): each section's rune is chiselled as
  it scrolls into view.
- **Yggdrasil's root** (`world-root.ts`): two static SVG paths form a tapered
  wood silhouette with sparse branches and a subtle bark ridge. A single
  pointed polygon clip follows scroll progress; there are no masks, filters,
  per-branch animations or SVG geometry measurements during scrolling.
  Geometry rebuilds only when page dimensions change. Narrow gutters hide it;
  reduced motion shows it fully grown.
  `node tests/world-root.browser.mjs` checks growth, resize and motion preferences.
- **Rune decoder** (`RuneText.astro`, `rune-decoder.ts`): the rune bands show
  Latin letters under the cursor.
- **Huginn and Muninn** (`Ravens.astro`): ravens land beside a heading in view
  and give a tip when clicked, with a tip box that follows the light/dark theme.
- **Ragnarök** (`ragnarok.ts`): type "ragnarok" outside a text field.
- **Thunder** (`thunder.ts`): logo clicks and partial charges use a synthesized rumble; a fully
  charged hold-and-release uses TRP’s CC0 close-thunder recording. Both play
  independently of the music toggle and follow its volume.

## Public identity and discovery

Public descriptions use **Eitr Linux**, an **Arch-based Linux distribution**;
logos keep EITR and the Norse visual identity. The homepage and shared footer
link to About, Features, Installation & Hardware, and the canonical guides.
Information pages separate available workflows, real-hardware evidence and
pending checks. The website does not claim unverified remote-access or hardware
support. A Releases page and external discovery work remain in `../TODO.md`.

`site-pages.ts` owns titles, descriptions and public sitemap paths. Layout emits
canonical and Open Graph metadata. `/sitemap.xml` is built from that catalog;
`/robots.txt` permits search access and advertises it. The `/intro/` motion study
is excluded from the sitemap and uses `noindex, follow`.

These files do not override Cloudflare's crawler/WAF policy or establish search
indexing. The owner still needs to verify crawler access, configure Search
Console/Bing Webmaster Tools and submit the sitemap. This change adds no site
analytics and no training-specific crawler directives.

## Content and product claims

The homepage introduces the desktop, development and system management together.
Development is a first-class workflow, not a claim that Eitr is only for developers.
Keep included packages distinct from optional software recipes and configured services:

| Claim | Canonical evidence |
| --- | --- |
| Included terminal and container tools | `distro/packages.txt` |
| Optional editors, language bundles, AI clients and database tools | `distro/software.json`, `distro/installers.json` |
| Project selection, Git identities and cloud contexts | `elephant/menu-rows/development.json`, Handbook development and Git Accounts chapters |
| Keyboard and mouse reference | Handbook catalog, generated by `handbook-build.py` from Learn's sources |
| AI collaboration permissions and validation limits | Handbook development chapter; do not infer real-account verification from menu availability |
| Installation, hardware and recovery limits | `distro/README.md`, `distro/RELEASES.md`, recovery guides and `src/data/download.json` |

The public reader consumes `quickshell/desktop-bar/handbook/catalog.json` at build
time. Edit its canonical Markdown, rebuild with
`python3 quickshell/desktop-bar/scripts/handbook-build.py`, and run `--check`;
never edit a second copy under the website. The adapter changes links and makes
code blocks keyboard-focusable; it retains commands, tables and body text.
The web reader is English; the installed reader also has pt_BR, es, de and fr.
References to desktop reader buttons are identified as installed-desktop actions.
Source corrections go through the canonical Markdown, not generated HTML.

Beta remains visible with the ISO, on Installation & hardware, in release notes
and the footer. It describes validation/support scope, rather than feature
availability. Do not promise universal hardware support, automatic recovery for
all layouts, or live-provider validation that the source does not establish.
`llms.txt` supplements the same accessible HTML and sitemap; no duplicate
`llms-full.txt` is maintained.

For browser validation, serve a production build and run `npm test`. Set
`EITR_BROWSER_EXECUTABLE` when Chrome/Chromium is outside the detected paths.
`EITR_WEB_REVIEW_CAPTURES=/tmp/eitr-site-review npm run test:product` saves only
headless local website views for visual review, with no live desktop capture.
