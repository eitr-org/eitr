# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Smaller items
3. Later
4. Before 1.0.0

# 1. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built and inactive until set up.
Fresh installs include them; existing machines install missing apps on demand
(`distro/REMOTE-ACCESS.md`). With the owner and a MacBook, in this order:

1. Home network, tested 2026-10-21 on the owner's PC (one monitor) with Moonlight
   on a MacBook: setup, start sharing, pairing by IP, video with no noticeable
   delay, keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start
   at login and Stop Sharing all work; two monitors and Restore Sharing Setup
   followed on 2026-10-22. Controllers are not needed.
2. Away from home works (2026-10-21): Tailscale setup, sign-in and connect on the
   owner's PC, and the Mac reached the PC through it.
3. Fix what the tests find; only then call remote access ready in the Handbook
   and on the website.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 2. Smaller items

- **Plugins: fixes from the owner's first test (2026-10-27).** Schema v2 plugins
  (tiles, panels, widgets, bar items, audio spectrum, streams, Plugins page,
  opt-in styling) are on testing; `distro/PLUGINS.md` has the details.
  - Menu focus, stable edit surfaces and compact list/detail navigation are implemented; verify right-click dismissal and smooth dragging on Hyprland
    before calling these fixes shipped.
  - Still open: runtime QML errors are not attributed to a plugin; in-process QML
    is not a sandbox; verify above-window click-through, fullscreen hiding and
    monitor hotplug live.

- **Theme previews.** Previews are Neovim + About screenshots (2026-10-27); `branding/sources/wallpapers/batch-05/export.py` still rewrites realm previews from wallpapers, so drop its preview step before rerunning it.
- **Realm theme colours.** The owner's palettes (from their realm CSV) are applied to
  the nine realms; Ragnarök keeps Blood & Iron. Waiting on the owner: whether any
  should be darker. Afterwards retake the Neovim + About previews of the realm themes
  (they still show the old colours).
- **Panel smoothness review.** Every bar panel, Control Center page and popup must open
  and close fluidly. Some still start opening, freeze, then finish (data loading or
  rebuilding during the animation, as Control Center and Display did before
  `JsonState.js` prefetching). Measure each panel's open on the live desktop, find
  mid-animation work (process launches, model rebuilds, image loads, layout jumps),
  prefetch it or apply it within the same reveal, and keep a checklist of panels verified. The repository audit,
  warm guarded snapshots, capped pre-reveal readiness, shared-deadline size retargeting
  and per-panel offscreen measurements are in desktop-bar/README.md;
  every entry still needs the live check. Then a full review
  and testing round of all panels with the owner.
- **Reduce motion option.** A Style > Desktop Bar setting to turn off panel open/close
  effects (unfold, fold, Overview entrances), applied everywhere through
  `DesktopStyle`/`DockPanel`, saved in `bar-settings.json`, Walker and QML settings.
  Implemented with five-language Handbook/catalog updates; live review remains.
- **Official plugins repository.** `eitr-org/eitr-plugins` is public with the
  Visualizer (2026-10-28); Add Plugin lists a repository's plugins from its
  `eitr-plugins.json` index. Next: add more plugins there and mention the repository
  on the website and in the Handbook. Ideas: a system monitor widget (CPU/GPU/RAM
  graphs), a weather widget, a calendar/agenda widget, a now-playing card with album
  art, a Pomodoro timer, a clipboard history tile, a GitHub notifications/PR tile, a
  Docker containers tile, a Home Assistant switchboard, a crypto/stock ticker, a
  world clock, a sticky notes widget, a network speed graph, a CI status tile (GitHub
  Actions), a Tailscale peers tile.
- **Themes from a Git repository.** Let users add a theme by repository URL, like
  plugins: validate `colors.toml` and the theme files against `test_theme_schema.py`'s
  contract, review before installing, pin to a commit, offer updates through System
  Update, and list user themes next to the bundled ones. Bundled themes stay as they are.
- **Auto-hide bar.** Implemented for every edge and layout;
  live Hyprland pointer-edge and exclusive-zone checks are pending before release.
- **Boot, shutdown and disk-password screens.** Shared Bifröst logo colours and
  runestone-gold runes are implemented with offscreen
  previews; boot, shutdown and encrypted unlock still need VM review before release.
- **Website translations.** Offer the site in the desktop's languages
  (Portuguese (Brazil), Spanish, German, French) with a language switch, reusing
  the reviewed Handbook translations where chapters overlap. Decide the URL scheme
  (`/pt-br/...`), `hreflang` and sitemap entries first; keep English the default
  and keep untranslated pages falling back to English.
- **Website evidence and screenshots.** Keep the public pages in step with verified
  desktop behavior. A feature gets a screenshot when it has a screen people look
  for (a panel, menu or wizard) shown on the website or in the Handbook;
  background behavior gets none. Missing: the HDR switch in a monitor's display settings.
  Describe remote access as verified only after the real-device tests above pass.
- **Search indexing and measurement.** eitr.info is verified in Google Search
  Console and Bing Webmaster Tools with the sitemap submitted (2026-10-22). Check
  that both read it, then track impressions, queries and clicks there without
  adding site analytics. Periodically spot-check whether search/AI answers
  identify Eitr accurately; inclusion and recommendations are not guaranteed.
- **Releases and public evidence.** After the owner records the video, add a website Releases page and prepare
  consistent GitHub Release notes with version, date, changes, checksums,
  tested configurations and known limitations. Publish installation walkthroughs
  and a video, a hardware test matrix, and suitable GitHub feedback templates.
  Keep beta and untested-hardware limits explicit.
- **Public discovery.** After the owner's video and with their approval, prepare release announcements for
  appropriate Linux communities, invite independent testers/reviewers and check
  distro-directory submission requirements. Share reproducible evidence rather
  than promotional claims. Update the public repository description/README with
  consistent Eitr Linux positioning. Consider a dated, source-checked Omarchy
  comparison page separately; do not imply shared features are exclusive.

# 3. Later

- **Voice reminders, next steps.** Read-only Google/Outlook/iCal subscriptions
  through a secret iCal address are done (Tools > Calendars). Two-way sync
  (creating or editing provider events) needs account sign-in (OAuth, with
  Google's app verification) and remains later.
- **The Eitr logo drawn with runes.** For About (and maybe the welcome banner):
  fill the emblem's shape with Elder Futhark runes in the theme accent, like
  Arch's logo drawn with characters, leaving the inner E cut-out empty.
- **Antigravity as a helper.** Recheck when its command-line tool gains per-run
  permissions or a read-only headless mode; until then it stays a standalone
  assistant. Nothing to do before that.

# 4. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Assistant sessions use full access by default; System > Security > Assistant Access restores permission prompts. Not planned: the rest of the "Not planned now"
list in `distro/RELEASES.md`.
