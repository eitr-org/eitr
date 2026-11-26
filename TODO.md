# Plan

Open work, grouped by what it waits on; each group is in priority order and each
item says what decides the next step. Remove an item when it ships;
`distro/RELEASES.md` tracks releases.

1. New features
2. To test with the owner
3. Waiting on others
4. Website and outreach
5. Maintenance
6. 0.8 release candidate and 1.0.0

# 1. New features

- **Remote access, next.** Sharing works at home, away through Tailscale and from a Mac
  (2026-11-11). Share the Login Screen is built (2026-11-17, `distro/system/eitr_remote_login.py`,
  `distro/REMOTE-ACCESS.md`): a system Sunshine while nobody is signed in, with the sharing
  account's identity and paired devices. VM-tested 2026-11-17: boot, sign-in (stops 2 ms after
  logind's new session), sign-out, hand-over to and from the user's own Sharing at login, a
  second account, switch off and Restore Sharing Setup. On the owner's NVIDIA PC (2026-11-18)
  Moonlight on a Mac streamed the login screen (X11 capture of SDDM's display) and was handed to
  the user's own Sharing at sign-in. Headless use and wake on LAN are not planned.
- **Side docks (proposed 2026-11-23).** Left and right screen edges beside the bottom app dock:
  right = Controls (volume, microphone, brightness), left = Recent (screenshots, recordings,
  clipboard, timer), with a short dwell, middle of outer edges only, never over fullscreen.
  Waiting for the owner's go on the contents.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Reminders > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **Clock alarm effect.** Replace the theme-colored pulse in `clock/AlarmEffect.qml`
  once the owner records the intended effect. Keep the Reduce motion behavior.
- **Eitr Store, next.** `eitr-org/eitr-store` is public with the schema 2 index and its
  validation workflow; fan content is allowed (`distro/STORE.md`, Community content). Listed:
  the owner's fan themes (`erickbatistaprado/eitr-theme-*`, from 2026-11-23). A
  new index field or license form must reach stable before the index uses it: older
  desktops refuse the whole index over one entry they do not understand. Screensavers and other
  future kinds are a registry entry plus a backend (`distro/STORE.md`).
- **Windows apps (requested 2026-11-24).** Run single Windows programs, such as Microsoft
  Office (Excel, Word), as ordinary windows on the desktop, opening Linux files in place.
  Wine cannot run current Office, so this needs a Windows VM behind the scenes with each app
  streamed as its own window over RDP (WinApps, WinBoat). Decide: which project to build on or
  wrap, sharing the VM with the Windows desktop item below, an Install entry through
  `eitr_wizard`, licence/activation guidance, resource use while idle. VM-test before shipping.
- **Windows desktop (requested 2026-11-24).** Run a full Windows in a window. Omarchy uses
  dockur/windows (QEMU/KVM inside Docker, shown over FreeRDP, `~/Windows` shared, ports bound
  to localhost). Compare before choosing: dockur, libvirt/virt-manager, Quickemu, plain QEMU with
  SPICE; weigh setup steps, GPU acceleration (virtio-gpu, passthrough), suspend/resume, disk
  use, snapshots and what the Windows apps item can reuse. Needs KVM (refuse clearly when
  virtualization is off in firmware), about 64 GB of disk, an Install entry through
  `eitr_wizard` and a VM test.
- **Ollama plugin, next.** Optional in `eitr-org/eitr-plugins` since 2026-11-23 (not installed
  by default). Its panel cannot change the local model yet: the core fixes `qwen3:4b`.

- **Faster installation.** The guided install
  takes 138.5 s in the 4-vCPU release VM (0.7.6): 52 s base system, 78 s desktop (817 packages),
  8 s for the rest. Packages are already offline, so the time is package extraction and pacman
  hooks. Plan, measured in the same VM after each step:
  1. *Cheap wins: done (2026-11-25).* archinstall 4.5 runs in two transactions instead of eight,
     the initramfs is built once at the end instead of seven times, and the package pool is read
     ahead during the questions. Same VM, back to back: 127.1 s to 113.7 s (base 45.7 to 39.4 s,
     desktop 73.5 to 65.8 s); packages, services, `/etc`, boot files and initramfs contents
     identical to 0.7.6's installer. Step 1 used standard transactions for other archinstall versions.
  2. *A prebuilt system image: working (2026-11-25), not yet on an ISO release.* The ISO build
     installs the fixed package set once into a generalized SquashFS root (`/eitr/system.sfs`,
     2.9 GB) and keeps only the hardware, input-method and profile closures in the pool (990 MB;
     ISO 6.4 GB). The installer lets archinstall 4.5 lay out the disk, extracts the root, makes a
     new machine ID and pacman keyring, adds the hardware packages and builds the initramfs once.
     VM: 75.6 s unencrypted, 79.7 s encrypted, 64 s with a profile; same packages, services,
     boot files and initramfs as 0.7.6. Passed: verify (both), Japanese + Mozc, a profile with
     removals, both factory resets, System Update. Not tested: Alongside (the VM harness has no
     Windows disk). The new pacman keyring is built in `/run` from the image's keyring files
     while the image is extracted (2026-11-26): 68 s unencrypted, 77-88 s encrypted (the first
     small writes after extraction wait for the disk to catch up, which varies by run).
     Next, waiting for the owner: extraction takes 36-45 s because Btrfs pays per file (275k
     files; unpacking to memory takes 3 s), so a raw Btrfs image written block by block (the
     original idea) could reach about 30 s.

# 2. To test with the owner

Shipped features that still need hardware or a setup the VMs cannot give.

- **2026-11-23 batch, on stable (g684985e).** Alarms, AI Usage pace, WireGuard's vpn-remove
  prompt, the Store's Updates page and Hardware as a built-in plugin were VM-tested and tried by
  the owner. Not yet confirmed on real hardware: an alarm ringing with sound, Visualizer's
  Ring/Mirror/Dots with music, AI pace against real accounts.
- **Wallpaper per display: the last part not tried yet.** The switch, preview, carousel and
  theme resets passed the owner's test (2026-11-10), and unplugging and replugging a display
  (HDMI) brought its own wallpaper back (2026-11-17). Still untried: each display's wallpaper
  coming back at login.
- **Clean My Eitr on a real laptop (VM-tested 2026-11-18).** In the VM the overlay, the
  empty `clean` submap (SUPER shortcuts did nothing), the inhibitor, a short Esc tap staying
  locked, a 3-second Esc hold leaving and `eitr clean stop` all worked; Ctrl+Alt+F still
  switches consoles (no Hyprland option blocks it; documented in the Handbook). Still to try:
  touchpad gestures and laptop Fn keys handled by firmware.
- **Battery warning levels on a real laptop.** Shipped in 0.7.5 (2–50%, critical below low);
  only tried without a battery so far.
- **OpenVPN traffic through a real server.** An OpenVPN profile connected to a test server
  (TLS and address) but no data crossed that server's tunnel; try a real OpenVPN server
  before calling OpenVPN traffic verified.

# 3. Waiting on others

- **hyprpaper crash without a GPU.** hyprpaper segfaults in VMs without 3D
  acceleration (hyprwm/hyprtoolkit#144); the bar draws the still wallpaper on any
  screen hyprpaper does not answer for. The fix from the owner's diagnosis merged as
  hyprwm/hyprtoolkit#155 (`fa61bbc`, 2026-11-13) but is not released yet (latest v0.6.0,
  Arch `0.6.0-3`). When a release containing it reaches Arch, confirm hyprpaper runs in a
  VM without 3D and drop this note.
- **Search indexing.** eitr.info is verified in Google Search Console and Bing
  Webmaster Tools. Bing reads the sitemap (2026-10-29); Google's sitemap entry was
  stuck on "Couldn't fetch" and the owner resubmitted it (2026-10-29): check it reads
  Success, then track impressions, queries and clicks there without site analytics.
- **DistroWatch.** The submission was emailed (2026-11-02); expect a long waiting list.

# 4. Website and outreach

- **Website evidence and screenshots.** Keep the public pages in step with verified
  desktop behavior. A feature gets a screenshot when it has a screen people look for
  (a panel, menu or wizard) shown on the website or in the Handbook; background
  behavior gets none. Describe remote access as verified only after its tests pass.
- **Plugin media.** Real screenshots and short clips for Visualizer and Lofi Radio
  (`media`/`preview` in `eitr-org/eitr-plugins`), captured only with the owner's go.
- **Releases and public evidence.** After the owner records the video, add a website
  Releases page (generated from the same release notes as the GitHub Release, kept per
  area as they land) and prepare consistent GitHub Release notes with version, date,
  changes, checksums, tested configurations and known limitations. Publish
  installation walkthroughs and a video, a hardware test matrix, and suitable GitHub
  feedback templates. Keep beta and untested-hardware limits explicit.
- **Public discovery: announce the release right after the video.** The preview video
  is on YouTube and the website; r/unixporn needs more account karma before posting,
  so build it with genuinely helpful comments first. With the owner's approval, post
  the release on Linux community sites and forums and on Reddit (for example r/linux,
  r/archlinux's rules permitting, r/hyprland and r/unixporn), each written for that
  community and following its self-promotion rules. Invite independent
  testers/reviewers. Share reproducible evidence rather than promotional claims.
  Describe Eitr the same way everywhere (repository description, README and website),
  and never present features common to other Arch or Hyprland setups as exclusive to
  Eitr. Periodically spot-check whether search/AI answers identify Eitr accurately.

# 5. Maintenance

- **Small visual issues seen in VM tests (2026-11-23).** The lock screen's "Locked session ·
  Switch user" text overlaps its footer line; a built-in plugin that is not installed fills its
  Store card with the icon; the plugin details sheet lets the mouse wheel scroll the grid behind it.
- **Bar disappearing.** It ended twice without a trace (2026-11-10 and 11). The bar now
  leaves a record when it ends unexpectedly (`~/.local/state/eitr/shell-exits/`): read the
  newest one if it happens again.

# 6. 0.8 release candidate and 1.0.0

0.8 (Muninn) is the exact ISO intended for 1.0; 1.0 (Bifröst) publishes the
promises below. The roadmap table in `distro/RELEASES.md` has the wording.

- **After 1.0: choose Hyprland or niri (decided 2026-11-13).** Parked until 1.0 ships. The
  survey of Hyprland dependencies and the adapter plan are in
  `eitr-testing/ideas/niri/` (INVENTORY.md, PLAN.md). Until then, new settings keep
  compositor-neutral data (as the keybind editor does).
- **After 1.0: analyse a Quickshell launcher in place of Walker (noted 2026-11-14).**
  Possible gains: no process start per open, the panels' look and motion, menus that grow
  into the bar panels in place, live rows, one i18n system, no Walker XML/GTK blur
  workaround. Risks: rewriting every menu and provider (apps, clipboard, calculator, files,
  emoji), CJK input-method support in Quickshell text fields, search speed in QML, a crash
  taking the bar down. First step: a prototype Main menu in Quickshell on Elephant's data,
  measured against Walker (open, typing) and tested with CJK input.
- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 0.8 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Repeated clean installs and destructive recovery tests** of the 0.8 ISO in
  isolated VMs, until install, maintenance and recovery are reproducible.
- **1.0 documents**: supported hardware matrix, tested upgrade paths, rollback
  limitations, security-update process, compatibility policy.

Assistant sessions use full access by default; Settings > AI Assistant > Assistant
Access restores permission prompts. Not planned: the "Not planned now" list in
`distro/RELEASES.md`.
