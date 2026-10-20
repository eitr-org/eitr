# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Google's assistant: Antigravity CLI instead of Gemini CLI
2. Remote access: test with the owner
3. Organization profiles: software and policies at installation
4. Eitr plugins
5. Smaller items: the website update
6. Waiting on the owner: testing channel
7. Later: AI multi-account
8. Before 1.0.0: skipped-release upgrade, encrypted resets, other hardware

# 1. Google's assistant: Antigravity CLI

Google no longer serves Gemini CLI for personal accounts (only paid API keys
and company accounts); individuals moved to Antigravity CLI (`agy`).

- Relabel Gemini CLI in Install > AI CLIs as "for Gemini API keys or Google
  Cloud accounts", so nobody installs it expecting the Google sign-in to work.
- Add Antigravity CLI to Install > AI CLIs and the first-use launchers, from
  Google's official source (it is not open source; never bundled).
- Then, as with the other helpers in `distro/ASSISTANTS.md`, prove a
  read-only headless mode and MCP registration before offering `ask_agy`.

# 2. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built, installed by default and inactive
until set up (`distro/REMOTE-ACCESS.md`). Nothing about real hardware is
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

# 3. Organization profiles

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

# 4. Eitr plugins

A plugin is a Git repository with a manifest declaring its Walker rows,
scripts and optional user service. Install > Plugins takes a URL, shows who
wrote it and a trust warning before any code runs, updates with System Update
and removes cleanly. The owner's cooler display tool (in the owner's private
repository) becomes the first plugin.

# 5. Smaller items

- **Website update** (with the owner's own changes). Add assistants working
  together (a second opinion from another subscription, each hand-off
  approved, helpers read-only) and, once tested, remote access. Retake the 8
  theme previews made before the btop colour change and add shots of the
  lockscreen, the dictation waveform and the Packages picker (owner-only
  captures, taken when the owner says).

# 6. Waiting on the owner

- **Testing channel.** Built and verified. When the owner says so, publish with
  `release-desktop.py --channel testing`, try it on the owner's PC, then
  `--promote` to stable.

# 7. Later

- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Pairs with item 1 for teams with several seats.

# 8. Before 1.0.0

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
