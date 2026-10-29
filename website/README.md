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
- `src/pages/screenshots.astro`: `/screenshots/`, the complete grouped screenshot gallery.
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
`../branding/svg/` and generate WebP artwork from `assets/norse/` and a theme
catalog from `../themes/`. Mímir, Valkyrie, Jörmungandr and Yggdrasil are
website-only sources; their provenance is in `assets/norse/artwork.json`.
Edit those canonical sources and run `npm run sync-assets` during development.
Website copies are generated consumers, not independent logo or artwork sources.
Generated `public/art/` and `src/data/` files are Git-ignored.

The homepage introduces five features with one screenshot each. `/screenshots/`
shows every image in `public/shots/`, grouped by desktop area, with a keyboard-accessible
full-screen viewer. Without JavaScript, thumbnails link directly to the image.
`src/data/screenshots.ts` owns captions, alt text and dimensions for both pages.
The theme wallpaper gallery and its viewer remain separate.

Capture the owner's 2560×1080 desktop with the Afterglow theme, an empty workspace,
Do Not Disturb on and the pointer hidden. Crop a 1920×1080 window around what the
image shows; never squeeze the ultrawide desktop into 16:9. Export ordinary shots
at 1600×900 WebP; `hero.webp` is 1920×810. Blur hardware models, device names,
network names and private plugin names. Never capture WiFi, Bluetooth, Weather,
AI Usage, Clipboard History, accounts, folder pickers, notifications or private
open windows. Keep accounts, tokens and project content out of every shot.
Describe the visible interface in alt text. Everything else uses Eitr's drawn
Norse illustrations and the wallpaper catalog.

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
Both wolf sprites preload and decode during idle time. The moving overlay uses
a 1× canvas with layered trail strokes and a cached celestial halo.
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
codename's myth line, in `src/i18n/en.json`. Consecutive releases with the
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

The approved Yggdrasil illustration holds nine realm
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

`site-pages.ts` owns public page paths; `src/i18n/*.json` owns localized titles and descriptions. Layout emits
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
The web reader uses the desktop’s reviewed pt_BR, es, de and fr catalogs (pt_BR maps to `/pt-br/`). Missing or stale chapter translations fall back to English with a localized note; freshness is checked against canonical source bytes and `source-hashes.json`.
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

## ISO download counter

The separate dependency-free Worker in `workers/download-counter/` counts ISO
GET requests without Range or with a single range starting at byte zero. It
records only UTC day, filename and count in D1; resumed/split ranges, HEAD and
package repositories are excluded. Counts measure starts, not completed transfers
or unique visitors. Database writes run in the background and failures do not
block downloads. `/stats.json` exposes the total and first day, cacheable for
five minutes. The homepage shows a positive total after load and stays silent
when statistics are unavailable.

The D1 database `eitr-stats` exists and its ID is in
`workers/download-counter/wrangler.toml` (an ID alone grants no access). Only
when recreating it, run `npx wrangler d1 create eitr-stats` and put the new ID
there. Apply the schema and deploy from `website/`:

```sh
npx wrangler d1 execute eitr-stats --remote --config workers/download-counter/wrangler.toml --file workers/download-counter/schema.sql
npx wrangler deploy --config workers/download-counter/wrangler.toml
```

The routes cover `download.eitr.info/eitr-*` (only successful `.iso` downloads
are counted) and `/stats.json` in the `eitr.info` zone. R2 remains the origin through `fetch(request)`; requests and
responses retain their range, cache and header behavior. Package paths under
`repo/` and `repo-testing/` bypass the Worker. Deploy this Worker separately from
the static-site Worker `eitr`. No provisioning or deployment runs in tests:

```sh
node --test workers/download-counter/tests/*.test.js
npm run test:downloads
```

The download-count browser suite uses the production build with every request
fulfilled or rejected by a mock, including the stats success, zero, invalid and
error cases.

## Website languages

English is the source and fallback at `/`. The same page components generate
Portuguese (Brazil) under `/pt-br/`, Spanish under `/es/`, German under `/de/`
and French under `/fr/`. Every prefix offers the home page and `about/`,
`features/`, `development/`, `installation/`, `privacy/`, `screenshots/`,
`guide/` and `intro/`. Intro keeps `noindex` and stays outside the sitemap.

`src/i18n/en.json`, `pt-br.json`, `es.json`, `de.json` and `fr.json` own page
and shared-interface copy, including metadata, gallery descriptions, myths and
roadmap milestones. Keys are grouped by page or shared component. Keep keys,
placeholders such as `{version}` and `{count}`, product names, commands and
paths intact when editing a translation. `translator()` falls back per string
to English; a key missing from English fails the build. Desktop menu names
follow the corresponding `i18n/catalogs/<locale>/` labels. Release data still
owns version numbers and codenames. New roadmap milestones need matching keys
in the website catalogs; asset sync never invents translations.

`src/pages/[locale]/[...page].astro` generates localized routes from the existing
page components. `src/i18n/index.ts` owns locale selection and local link
mapping. Rendered HTML includes the translated copy, `lang`, canonical URL and
all available `hreflang` alternates, including English as `x-default`. The
sitemap includes every indexable localized page. `llms.txt` stays English.

The header's native language menu works with keyboard navigation and without
JavaScript. JavaScript preserves the current query and fragment when switching,
remembers explicit selections in the browser's `eitr-language` localStorage
entry and closes the menu on Escape or outside click. Storage failures are
ignored. URLs always determine the language; neither browser language nor a
saved choice redirects a visit. No analytics or cookies are added.

Every localized `guide/` and `guide/<chapter>/` route shares the English rendering path. Heading IDs follow English headings by position and level so deep links remain stable across languages. A different heading hierarchy falls back to the English chapter until reviewed. Chapter titles, search, navigation and metadata use the selected locale; internal links and language switches preserve the chapter. Translations remain in the canonical desktop sources.

After editing copy or routes, run `npm run build` and `npm run test:i18n`.
The latter checks all catalogs, placeholders, generated routes, metadata,
internal links, fragment targets and sitemap entries without a browser.
`npm run test:discovery` also checks localized static HTML, the language switch,
blocked storage and 360 px layouts with and without JavaScript. Run the browser
suite against a production preview as described above.

## Security headers

`public/_headers` is copied to the assets root by Astro. Cloudflare Workers
static assets apply its `/*` rule to every path (see [Cloudflare's headers
reference](https://developers.cloudflare.com/workers/static-assets/headers/)).
The CSP starts in report-only mode; review browser console violations before
enforcing it. No report collector is configured. `X-Frame-Options: DENY` already
blocks framing. HSTS covers only this host for one year: no preload or
includeSubDomains, because HTTPS-only operation of every subdomain was not verified.

The production build uses local module scripts, fonts, images and audio, plus
`https://download.eitr.info/stats.json`. `connect-src` also allows local audio and
SVG fetches. `img-src data:` permits the inline SVG grain texture. Inline script
permission covers the appearance bootstrap, Astro-inlined modules and localized
JSON-LD/data blocks; hashes for all per-page localized structured data would
exceed Cloudflare's 2,000-character header-line limit. Inline style permission
covers generated style blocks, HTML style attributes and runtime animation styles.
Neither scripts nor styles allow external origins or eval. Revisit these inline
exceptions before enforcing a stricter policy.

After `npm run build`, `npm run test:headers` checks the built header file and
asset policy against all generated pages. It is also part of `npm test`.
Deployment and live response headers require a separate post-deploy check.
