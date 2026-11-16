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

- **VPN plugins, Taildrop and Tailscale out of the default install (agreed 2026-11-09,
  to do together with the owner).**
  - Three official plugins in `eitr-org/eitr-plugins`: Tailscale (today's bar icon, panel
    and actions, plus Taildrop: send files to the person's other Tailscale machines from
    a menu, incoming files arriving as a notification; operator setup moves from the core
    root helper to the plugin's own reviewed step), WireGuard (import a config,
    connect/disconnect, status) and NetworkManager VPN (OpenVPN/OpenConnect profiles;
    explains the NetworkManager backend when on iwd).
  - Plugin format has an optional `packages` field (on testing since 2026-11-10; a real
    install and removal with the administrator password still needs a VM test): official
    Arch/Eitr repositories only. The install review lists them; after approval they install with the
    administrator password, ideally inside the Eitr Store session, otherwise a
    terminal that returns to it. Packages already installed are detected and not
    reinstalled. Removing the plugin offers to remove only the packages it installed
    that nothing else needs.
  - Plugins never install silently. A one-time update step installs the official
    Tailscale plugin (pinned, reviewed) on desktops that already have Tailscale, with a
    notification; Tailscale is never uninstalled automatically. New installs no longer
    include it.
  - Install > VPN and Walker's Tailscale menus are gone; `walker/scripts/actions/install/vpn.py`,
    `eitr_vpn` and `remote-access.py away setup|undo` (with its root helper) stay for the plugins.
  - Order: plugin `packages` field (VM-tested), the three plugins, then remove Tailscale
    from the core and ship the update step after the plugin passes a VM test.
  - Status (2026-11-10): Tailscale is official (`eitr-org/eitr-plugins`) with its bar icon,
    panel and Taildrop, the core icon and panel are gone, and a login step installs the
    pinned plugin on desktops with Tailscale (2026-11-11: Walker's Tailscale menus and the
    core panel's Tailscale branch removed; the plugin's panel covers them).
  - Status (2026-11-14): WireGuard and NetworkManager VPN have bar icons and panels on the
    `vpn-bar-panels` branch of `eitr-org/eitr-plugins` (WireGuard installed in the VM through
    the normal review, its panel shown; real tunnels untested). Next: the owner reviews the
    branch, a VM test with a real WireGuard peer and an OpenVPN profile, then merge to main.
    Removing a tunnel asks for the password through `pkexec rm`; an `eitr-system` action
    would show a clearer prompt.
- **Remote access, next.** Sharing works at home, away through Tailscale and from a Mac
  (2026-11-11). Owner's choices (2026-11-12): Sunshine on the login screen behind its own
  switch beside Start at Login (a system Sunshine with KMS capture while SDDM shows, handing
  over to the session's Sunshine after sign-in), and headless use (a virtual display sized
  to the Moonlight client); wake on LAN is left to people who want it. On hold; the agreed
  design, including several users on one PC, is in `eitr-testing/codex-wip/remote-access-next/PLAN.md`.
- **Dynamic island, next.** Short notification, volume/brightness, song, Bluetooth and
  keyboard moments are implemented. Next: a hover card for the clock (large time and week
  strip), and the wallpaper/theme carousel growing out of the clock island. Islands arrows
  (‹ ›) like Dynamic if the owner wants them.
- **Bar icon organizer (idea 2026-11-16).** A Settings > Desktop Bar page that finds every bar
  icon, plugin icons included, and lets people drag them into the order and side they want
  (left group, right group, beside the clock), with a reset to the default order. Every
  layout (Full, Tabs, Islands, Dynamic, Drop) follows the saved order.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Reminders > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **Reminders: alarms (idea 2026-11-15).** A wake-up alarm: the reminder stays on screen with a
  song and an animated effect until stopped, with Stop and Snooze. The owner will record the
  effect they want; build after that.
- **Eitr Store, next.** `eitr-org/eitr-store` is public with the schema 2 index (empty: the
  community index had no entries yet) and its validation workflow. Screensavers and other
  future kinds are a registry entry plus a backend (`distro/STORE.md`).
- **Backup and Restore (planned 2026-11-15).** Move a desktop to a fresh Eitr install: one
  encrypted file (age passphrase) holding the chosen Eitr and app settings, personal folders
  (asked one by one with their sizes), the lists of installed official, AUR, Flatpak and
  plugin apps (reinstalled on restore), and optionally Git, cloud and WiFi accounts.
  Browser profiles are left out (people sign in again). A one-time move first; scheduled
  backups later. Plan: `eitr-testing/codex-wip/backup-restore/PLAN.md`.
- **Local AI in the AI Usage panel (idea 2026-11-15).** The local assistant (Ollama, `eitr-ollama.service`)
  has no panel entry today. Add a local section beside the cloud assistants: service running
  or stopped (start/stop), the loaded model and its memory, installed models with size,
  download (with progress) and delete, the default model, and an Open Chat button (SUPER + A).
  A new DesktopData domain reading Ollama's local API on `127.0.0.1:11434`, only while the
  panel is open; nothing shown when it is not set up.
- **Plugin ideas (from Omarchy and Ryoku's popular plugins, 2026-11-15).** Official plugins in
  `eitr-org/eitr-plugins`, not core features:
  - Phone and Apple devices: send files, notifications and clipboard to and from a phone
    (KDE Connect, which also works with iPhones through its iOS app) and AirDrop-style
    sharing with Macs and iPhones.
  - Radio globe: browse live radio stations on a spinning globe and play them, beside the
    existing Lofi Radio.

# 2. To test with the owner

- **Wallpaper per display: the parts not tried yet.** The switch, preview, carousel and
  theme resets passed the owner's test (2026-11-10); still untried: plugging a display
  in and out, and each display's wallpaper coming back at login.

# 3. Waiting on others

- **hyprpaper crash without a GPU.** hyprpaper segfaults in VMs without 3D
  acceleration (hyprwm/hyprtoolkit#144); the bar draws the still wallpaper on any
  screen hyprpaper does not answer for. A contributor turned the owner's diagnosis into
  hyprwm/hyprtoolkit#149 (2026-11-09); a bot closed it under the vouching policy, so it
  waits for a maintainer. Drop the note once a fixed hyprtoolkit ships.
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
