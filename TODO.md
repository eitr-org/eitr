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

- **Visual plugins (next).** Event hooks and schemaVersion 1 shipped
  (`distro/PLUGINS.md`). Next: plugin QML for panels, Control Center tiles and
  widgets on the shared panel style, placed in the Control Center by default
  (bar slots only when the user places one). They run inside the bar, so load
  failures must be caught, crashing plugins disabled, and the review must show
  the QML before approval.
- **Create User.** A System action to add another account (standard or
  administrator) on an installed machine, with a review step; the new account
  gets Eitr's desktop setup at its first login, like the installer's first user.
- **Install > VPN.** Tailscale (keeps its panel), WireGuard and NetworkManager
  VPN profiles: install the tools and import a profile, in one menu.
- **Dim before the idle lock.** About 20 seconds before hypridle locks, dim the
  screen as a warning and restore the exact brightness on activity (backlight on
  laptops, DDC steps on external monitors).
- **Self-check ("Check this PC").** Agreed with the owner (2026-10-26): System >
  Maintenance > Check this PC, read-only, one line per check (ok, warning, problem)
  and one suggested fix each; copyable and attachable to Report a Problem. Checks:
  restart needed (running kernel older than installed, for every GPU; NVIDIA
  module vs utils only on NVIDIA; Mesa or linux-firmware updated since login or
  boot on AMD/Intel, using `distro/hardware/detect.sh`); disk space (root, snapshot
  usage, ESP nearly full); updates (pending, last System Update, channel, stale
  pacman lock, package-list signatures); recovery (snapshots, last pre/post pair,
  boot guard, factory reset point); failed services, bar/Walker/Elephant running,
  idle lock; memory pressure, swap, OOM kills this boot, core dumps this week;
  DNS, clock sync, firewall; Hyprland config errors, bar load errors, PipeWire and
  an output device; Secure Boot, encryption, exposed SSH (informational); blocked
  plugins and hook failures. Only the keyring and ESP file system checks may ask
  for a password, in the terminal.
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
