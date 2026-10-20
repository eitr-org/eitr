# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Assistants working together: Gemini, Copilot and Grok as helpers
2. Remote access: Moonlight, Sunshine and Tailscale
3. Organization profiles: choose the software at installation
4. Smaller items: OBS and the main display, menu translations, AI Usage
5. Waiting on the owner: personal overlay split, testing channel
6. Later: AI multi-account, plugins, smaller artwork packages, screenshots
7. Before 1.0.0: skipped-release upgrade, encrypted install, other hardware

# 1. Assistants working together: more helpers

Claude and Codex hand questions to each other through AI > "Let assistants
work together" (`distro/ASSISTANTS.md`). Next, each only once its headless
mode is proven read-only, with a real hand-off test like the one in
`distro/ASSISTANTS.md`:

- **Gemini CLI:** confirm `gemini -p --approval-mode plan` cannot write in a
  headless run (try creating a file in a scratch folder), then add `ask_gemini`
  and register through `gemini mcp add`.
- **Copilot CLI:** install it, allow only read tools and `--deny-tool` writes
  and shell in `copilot -p`, prove a write is refused, then add `ask_copilot`
  (MCP in `~/.copilot/mcp-config.json`).
- **Grok Build:** wait until xAI documents a read-only headless mode and MCP
  support.

# 2. Remote access: Moonlight, Sunshine and Tailscale

First milestone: control the owner's signed-in, awake Eitr desktop (apps and
games) from a MacBook. Install everything on first use, like GeForce NOW; the
ISO does not grow. All three are open source from their usual sources.

Stage 1, Moonlight (client):

- Gaming > Moonlight next to Steam and GeForce NOW: first click installs it,
  later clicks open it. Also listed as "Connect to another PC" under
  System > Connectivity > Remote Access.

Stage 2, Sunshine on the home network (host):

- System > Connectivity > Remote Access > Share this PC: set up, start or stop
  sharing, open settings, pair a device, optionally start at login (a user
  service). Hosting stays off until enabled; existing installations and
  settings are kept.
- The first enable warns that sharing hands over full control of the desktop
  and makes the user set Sunshine's password. Its web settings listen only on
  this PC.
- Firewall: Eitr's firewall is on from the first boot, so sharing opens TCP
  47984, 47989, 47990 and 48010 and UDP 47998-48000 only for the home network
  and the Tailscale interface; stopping sharing closes them. Never suggest
  router port forwarding.
- Virtual keyboard, mouse and controller input (uinput) and any capture
  permission Sunshine needs on Wayland with NVIDIA are system changes: one
  confirmed setup step through the root helper, with an undo.
- Test with the owner on the local network first: Hyprland capture, keyboard,
  mouse, audio, controller, both monitors, and behaviour while locked.

Stage 3, Tailscale (away from home):

- Remote Access > Access away from home: install, enable the system service
  (confirmed, like the network backend switch), set the user as operator so
  later actions need no sudo, sign in through the browser, show status and this
  PC's address, connect or disconnect.
- Show whether the connection is direct or relayed (from Tailscale's own
  status) to explain poor performance.
- Handbook guide: Sunshine on Eitr, Moonlight on the Mac, then Tailscale on
  both. Translate menus and messages; test installs, service controls,
  signed-out states and failures.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 3. Organization profiles

A company (or anyone setting up several machines) chooses the software at
installation without rebuilding the ISO: the official, signed ISO stays
untouched and machines keep receiving Eitr's normal updates. Built on the
existing answers drive (`EITR-ANSWERS`, `distro/README.md` > Unattended install).

Design:

- An `eitr-profile.json` beside (or instead of) `eitr-answers.json`. With only
  the profile, the normal wizard runs and then shows the profile's changes;
  with both files the install is fully unattended.
- `remove`: Eitr apps to leave out, for example Steam or RetroArch. Only apps
  on an explicit, reviewed list of removable apps are accepted. Everything the
  desktop needs is protected: `distro/packages.txt`, `distro/aur-packages.txt`
  and `distro/local-packages.txt` (Hyprland, Quickshell, Walker, Elephant and
  the rest), `eitr-desktop`, `eitr-artwork` and anything they depend on.
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
- Before anything changes, the installer lists everything it will add, remove,
  set and run, with the answers drive's countdown when unattended.
- The applied profile is recorded on the machine so System Update never
  reinstalls a removed app.
- `eitr profile check DRIVE` validates a stick before it is used.

Steps:

1. Review `distro/apps.txt` and `distro/aur-apps.txt` entry by entry and mark
   the removable apps (gaming, media and other optional apps); write the
   protected-package test first.
2. Profile parser and validation, shared by the installer and
   `eitr profile check`; unit tests for refusals (protected packages, bad
   checksums, unknown recipes).
3. Installer integration: skip removed apps in the offline payload install,
   then additions, defaults and the setup script; record the profile.
4. VM tests: an offline install with removals and stick packages, an online
   install with Flathub additions, a refused profile, and System Update not
   bringing a removed app back.
5. Handbook and `distro/README.md` section with a complete example profile.

Out of scope: managing machines after installation (fleet management).

# 4. Smaller items

- **OBS and the main display.** The screen-share permission keeps the first
  monitor picked, so OBS does not follow the bar's main display. Ship a shared
  `xdph.conf` default with `allow_token_by_default = true` (an existing user
  file is kept) so the share prompt remembers its choice after the first time,
  and say in the Handbook that OBS asks once which screen to record. Do not
  replace the share picker: it serves every app, not only OBS. Verify with both
  monitors.
- **Menu translations, final read.** The last 1.0 item in `distro/RELEASES.md`:
  an editorial pass over menu wording in all four languages (whole sentences,
  consistent terms, same register as the Handbook), then the owner uses
  Portuguese daily and reports anything odd. Native speakers among early users
  review Spanish, German and French.
- **AI Usage for Copilot and Gemini.** Not added: Copilot's official endpoint
  reports only requests used (no allowance, personal plans only, separate
  token) and Gemini has no official quota source. Check again when either
  publishes real limits.

# 5. Waiting on the owner

- **Personal overlay split** (`PUBLISHING.md`). Once the owner creates the
  private repository: move `HOME_FILES/.zshrc` and `owner/cooler-display` there
  with their install notes, update `distro/layout-manifest.json` and the
  manifests that list them, keep the distro's own `.zshrc` default, check the
  box in `PUBLISHING.md`.
- **Testing channel.** Built and verified. When the owner says so, publish with
  `release-desktop.py --channel testing`, try it on the owner's PC, then
  `--promote` to stable.

# 6. Later

- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Pairs with item 1 for teams with several seats.
- **Eitr plugins.** A plugin is a Git repository with a manifest declaring its
  Walker rows, scripts and optional user service. Install > Plugins takes a
  URL, shows who wrote it and a trust warning before any code runs, updates
  with System Update and removes cleanly. `cooler-display` becomes the first
  plugin, in the owner's repository.
- **Smaller artwork packages.** Only if artwork changes become frequent: split
  `eitr-artwork` per theme so one theme's change republishes a few MB.
- **Screenshots.** Retake the 8 theme previews made before the btop colour
  change; add website shots of the lockscreen, the dictation waveform and the
  Packages picker (owner-only captures, taken when the owner says).

# 7. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Encrypted install.** Install with LUKS in a VM by hand (the passphrase is
  typed at boot), then verify, update, both factory resets and the boot guard.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
