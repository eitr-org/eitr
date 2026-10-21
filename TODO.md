# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Voice reminders
2. More cloud providers
3. Display review
4. Remote access: test with the owner
5. Organization profiles
6. Eitr plugins
7. Smaller items
8. Google's assistants: remaining verification
9. Waiting on the owner
10. Later
11. Before 1.0.0

# 1. Voice reminders

Agreed with the owner on 2026-10-21; build when the owner says go.

- **Trigger.** Hold SUPER+SHIFT+D, speak, release (offline whisper, like SUPER+D),
  or type into a Walker row "Tell the assistant…".
- **Assistant.** The default assistant runs headless and returns only a small,
  validated instruction (create, delete, list, ask); Eitr executes it. The
  assistant never runs commands, so any supported assistant works the same.
- **Reminders.** Eitr's own reminders (`reminders.py`) gain real dates
  ("tomorrow 15:00", "Friday", "October 30"). Appointments alert 1 hour before
  (or as said, "30 minutes before") and again at the event time; plain reminders
  fire at their time. Reminders due while the computer was off or asleep show at
  the next login, as today.
- **Questions.** Ambiguity ("which reminder?") or missing details open a
  terminal with the full text of numbered choices; answer by typing or SUPER+D.
- **Feedback.** One notification says what was done ("Reminder set: Dentist,
  tomorrow 15:00 · alert 14:00") or why nothing changed.
- **Calendar.** The bar's calendar marks days with reminders and lists a day's
  reminders when clicked, updated as soon as one is added or removed.
- **Privacy.** Only the transcript goes to the assistant's provider; audio stays
  local. The Handbook says so.
- Handbook, translations and tests as usual.

# 2. More cloud providers

The seven requested providers have Cloud menu entries and isolated account
workspaces. DigitalOcean and Hetzner use Arch extra packages; Oracle and IBM use
reviewer-verified official HTTPS installers; Vercel and Netlify use NVM/npm.
Native sign-in, context/profile listing, account switching and IBM account/region
targeting are wired. Context/profile/scope selections persist visibly and use
per-command flags where supported, without changing global defaults to navigate.

Cloud navigation now uses Elephant account, service and resource menus with real
Parent links for Shift+Backspace and private persisted selections.

Remaining: owner-authorized live installation/sign-in checks, remote identity and
project verification. Account deletion and common read-only resource views are
implemented for these seven providers with isolated mock tests. Offline mock tests do
not establish live vendor behavior. See `distro/DISPLAY-REVIEW.md`.
Do not add more providers as part of this work.

# 3. Display review

The source display review is accepted. Inventory and retained design decisions are in `distro/DISPLAY-REVIEW.md`. Passive cloud
resource reports use the existing pager; actionable choices stay in Walker and
log/event searches keep fzf. Future work: native status parity for security,
snapshots, battery and remote access, cloud status presentation, and About's
optional native redesign. Preserve typed confirmations and readable failures.

# 4. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built and inactive until set up.
Fresh installs include them; existing machines install missing apps on demand (`distro/REMOTE-ACCESS.md`). Nothing about real hardware is
verified yet. With the owner and a MacBook, in this order:

1. Home network: Share this PC setup (permissions, Sunshine password), start
   sharing, pair Moonlight on the Mac. Check video on both monitors, keyboard,
   mouse, audio, a controller, behaviour while locked, start at login, and that
   Stop Sharing and Restore Sharing Setup undo everything.
2. Away from home: Tailscale setup and sign-in on both machines, then connect
   through it and check direct versus relayed.
3. Fix what the tests find; only then call remote access ready in the Handbook
   and on the website.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 5. Organization profiles

A company (or anyone setting up several machines) chooses the software at
installation without rebuilding the ISO: the official, signed ISO stays
untouched and machines keep receiving Eitr's normal updates. Built on the
existing answers drive (`EITR-ANSWERS`, `distro/README.md` > Unattended install).

Design:

- An `eitr-profile.json` beside (or instead of) `eitr-answers.json`. With only
  the profile, the normal wizard runs and then shows the profile's changes;
  with both files the install is fully unattended.
- `remove`: Eitr apps to leave out, for example Steam, RetroArch or the remote
  access apps (`moonlight-qt`, `eitr-sunshine`, `tailscale`). Only apps on an
  explicit, reviewed list of removable apps are accepted. Everything the
  desktop needs is protected: `distro/packages.txt`, `distro/aur-packages.txt`,
  the desktop's own entries in `distro/local-packages.txt` (Hyprland,
  Quickshell, Walker, Elephant and the rest; `eitr-sunshine` there is
  removable), `eitr-desktop`, `eitr-artwork` and anything they depend on.
  `distro/apps.txt` also holds pieces the desktop relies on (themes, menu
  data), so it is not removable as a whole; each removable entry is reviewed.
  A profile naming a protected package is refused as a whole with a clear
  message, before any disk is changed. pacman confirms that no removal breaks
  a dependency.
- `add`: Eitr install recipes by name (`distro/software.json`), Arch packages,
  Flathub apps (Zoom is `us.zoom.Zoom`), and package files on the stick, each
  with its SHA-256 in the profile. No AUR builds during installation. Additions
  that need the internet say so; package files on the stick install offline.
- `defaults`: theme, wallpaper (an image on the stick), browser, update
  channel, and an extra package repository with its signing key.
- `setup`: an optional script from the stick, run once at the end of the
  installation and shown in the summary.
- `policies`: features the organization turns off, written to a root-owned
  `/etc/eitr/policies.json` that users cannot change. Each policy hides the
  feature's menus and makes Eitr's own tools refuse it: `remote_access`
  (Remote Access menus, and the sharing and Tailscale setup in `eitr-system`),
  `assistants_together` (the "Let assistants work together" switch),
  `update_channel` (pin stable), and the removable app groups such as gaming.
  Eitr can only enforce this in its own tools: an employee with root could
  still set things up by hand, so the Handbook says that real lockdown also
  means not granting root.
- Before anything changes, the installer lists everything it will add, remove,
  set and run, with the answers drive's countdown when unattended.
- The applied profile is recorded on the machine so System Update never
  reinstalls a removed app.
- `eitr profile check DRIVE` validates a stick before it is used, and
  `eitr profile apply DRIVE` brings an already installed machine in line:
  removes the listed apps, writes the policies and records the profile, after
  the same summary and confirmation.

Steps:

1. Review `distro/apps.txt` and `distro/aur-apps.txt` entry by entry and mark
   the removable apps (gaming, media and other optional apps); write the
   protected-package test first.
2. Profile parser and validation, shared by the installer and
   `eitr profile check`; unit tests for refusals (protected packages, bad
   checksums, unknown recipes).
3. Installer integration: skip removed apps in the offline payload install,
   then additions, defaults, policies and the setup script; record the profile.
   Policy checks in the menus and in `eitr-system`, with tests that a refused
   feature stays refused from both.
4. VM tests: an offline install with removals and stick packages, an online
   install with Flathub additions, a refused profile, System Update not
   bringing a removed app back, a policy hiding Remote Access, and
   `eitr profile apply` on an installed machine.
5. Handbook and `distro/README.md` section with a complete example profile.

Out of scope: managing machines after installation (fleet management).

# 6. Eitr plugins

A plugin is a Git repository with a manifest declaring its Walker rows,
scripts and optional user service. Install > Plugins takes a URL, shows who
wrote it and a trust warning before any code runs, updates with System Update
and removes cleanly. The owner's cooler display tool (in the owner's private
repository) becomes the first plugin.

# 7. Smaller items

- **ISO download counter.** Cloudflare's R2 analytics only keep a few weeks and
  cannot tell our own checks from real downloads. Put a small Worker in front of
  the ISO link that counts new downloads (not resumed ranges) in D1 without
  storing IPs, and show the total on the website.
- **Website translations.** Offer the site in the desktop's languages
  (Portuguese (Brazil), Spanish, German, French) with a language switch, reusing
  the reviewed Handbook translations where chapters overlap. Decide the URL scheme
  (`/pt-br/...`), `hreflang` and sitemap entries first; keep English the default
  and keep untranslated pages falling back to English.
- **Website evidence and screenshots.** Keep the new public information pages in
  step with verified desktop behavior. Retake the 8 theme previews made before
  the btop colour change and add lockscreen, dictation waveform and Packages
  picker shots (owner-only captures, taken when the owner says). Describe remote
  access as verified only after the real-device tests above pass.
- **Crawler access.** Inspect Cloudflare's bot/WAF settings and logs with the
  owner: automated fetches returned 403 while a normal browser loaded the site.
  Verify access for Googlebot, Bingbot, OAI-SearchBot, Claude-SearchBot and
  Claude-User, including robots.txt and the sitemap. Do not weaken unrelated
  security rules or change model-training permissions as part of search setup.
- **Search indexing and measurement.** The owner verifies eitr.info in Google
  Search Console and Bing Webmaster Tools, submits the sitemap and inspects
  public-page indexing. Track impressions, queries and clicks there without
  adding site analytics. Periodically spot-check whether search/AI answers
  identify Eitr accurately; inclusion and recommendations are not guaranteed.
- **Releases and public evidence.** Add a website Releases page and prepare
  consistent GitHub Release notes with version, date, changes, checksums,
  tested configurations and known limitations. Publish installation walkthroughs
  and a video, a hardware test matrix, and suitable GitHub feedback templates.
  Keep beta and untested-hardware limits explicit.
- **Public discovery.** With owner approval, prepare release announcements for
  appropriate Linux communities, invite independent testers/reviewers and check
  distro-directory submission requirements. Share reproducible evidence rather
  than promotional claims. Update the public repository description/README with
  consistent Eitr Linux positioning. Consider a dated, source-checked Omarchy
  comparison page separately; do not imply shared features are exclusive.

# 8. Google's assistants: remaining verification

Gemini CLI ships as an assistants-together helper from documentation. A real
read-only and MCP test remains open for someone with a paid API key or company
account; no personal Google sign-in test is applicable.

Antigravity (`agy`) stays out as a helper: headless runs auto-deny even reading.
The only unlocks are `--dangerously-skip-permissions` or global permission rules
in `~/.gemini/antigravity-cli/settings.json`. Re-check when it gains per-run
permissions or a read-only headless mode. Do not weaken global permissions.

# 9. Waiting on the owner

- **Testing channel.** Built and verified. When the owner says so, publish with
  `release-desktop.py --channel testing`, try it on the owner's PC, then
  `--promote` to stable.

# 10. Later

- **Voice reminders, next steps.** Repeating reminders ("every Monday") and
  syncing with Google or Outlook Calendar (needs account sign-in).
- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Pairs with item 2 (cloud providers) for teams with several seats.

# 11. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Factory resets and the boot guard on an encrypted disk.** The owner's PC
  proves an encrypted install and daily use. What has never run on LUKS is
  destructive: both factory resets and the boot guard's rollback. Test them in
  a VM installed with encryption by hand (the passphrase is typed at boot),
  never on the owner's PC.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
