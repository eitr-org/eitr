# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Organization profiles
3. Smaller items
4. Google's assistants: Antigravity
5. Later
6. Before 1.0.0

# 1. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built and inactive until set up.
Fresh installs include them; existing machines install missing apps on demand
(`distro/REMOTE-ACCESS.md`). With the owner and a MacBook, in this order:

1. Home network, tested 2026-10-21 on the owner's PC (one monitor) with Moonlight
   on a MacBook: setup, start sharing, pairing by IP, video with no noticeable
   delay, keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start
   at login and Stop Sharing all work. Still to check: two monitors, Restore
   Sharing Setup. Controllers are not needed.
2. Away from home works (2026-10-21): Tailscale setup, sign-in and connect on the
   owner's PC, and the Mac reached the PC through it.
3. Fix what the tests find; only then call remote access ready in the Handbook
   and on the website.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 2. Organization profiles

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

# 3. Smaller items

- **The first real plugin: switch over with the owner.** The private
  `eitr-personal` repository is now a plugin (`personal-tools`: the cooler display's
  service and a Cooler Display Status row), fetched and validated over SSH. With
  the owner: add the udev rule once, install it from Install > Plugins, retire the
  `install.sh` copy (its README lists the commands) and check the display.
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
  step with verified desktop behavior. Add lockscreen, dictation waveform and
  Packages picker shots, taken when the owner says. Describe remote access as
  verified only after the real-device tests above pass.
- **Search indexing and measurement.** The owner verifies eitr.info in Google
  Search Console and Bing Webmaster Tools, submits the sitemap and inspects
  public-page indexing. Track impressions, queries and clicks there without
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

# 4. Google's assistants: Antigravity

Gemini CLI is verified as an assistants-together helper with a free API key:
a direct read-only question and an MCP `ask_gemini` call both answered.

Antigravity (`agy`) stays out as a helper: headless runs auto-deny even reading.
The only unlocks are `--dangerously-skip-permissions` or global permission rules
in `~/.gemini/antigravity-cli/settings.json`. Re-check when it gains per-run
permissions or a read-only headless mode. Do not weaken global permissions.

# 5. Later

- **Voice reminders, next steps.** Repeating reminders ("every Monday") and
  syncing with Google or Outlook Calendar (needs account sign-in).
- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Useful for teams with several seats.
- **Local assistant for voice reminders.** An optional offline model through
  Ollama (a 3B model such as Qwen 2.5 or Llama 3.2, 2-3 GB once) offered next to
  the other assistants, with its answer constrained to the reminder JSON format and
  checked by the same validator. Nothing leaves the PC; weaker on unusual phrasing.

# 6. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
