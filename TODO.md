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

- **Keybinds and window rules editors.** Settings > Keybinds only lists shortcuts today:
  rebind one by pressing the new keys, with clash warnings, reset to default and the
  change kept in the person's own config. Window rules: pick an app and choose
  "always float", workspace, size or opacity from a form instead of editing Lua.
  Approved 2026-11-11; Codex is building it (2026-11-13)
  (`eitr-testing/codex-wip/keybinds-window-rules/BRIEF.md`).
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
    administrator password, ideally inside the Add-ons session, otherwise a
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
    core panel's Tailscale branch removed; the plugin's panel covers them). WireGuard and NetworkManager VPN
    stay on the owner's private test repository (local `vpn-plugins` branch) until they
    get bar icons and panels too.
- **Remote access, next.** Sharing works at home, away through Tailscale and from a Mac
  (2026-11-11). Owner's choices (2026-11-12): Sunshine on the login screen behind its own
  switch beside Start at Login (a system Sunshine with KMS capture while SDDM shows, handing
  over to the session's Sunshine after sign-in), and headless use (a virtual display sized
  to the Moonlight client); wake on LAN is left to people who want it. On hold; the agreed
  design, including several users on one PC, is in `eitr-testing/codex-wip/remote-access-next/PLAN.md`.
- **Git & Cloud for many companies** (Walker; Settings no longer has the page): group
  each company's cloud profiles and contexts with its Git identity and folder rules.
- **Dynamic island, next.** Live activities in the clock island beyond the capture
  indicator (volume/brightness replacing swayosd only in Dynamic, notification
  previews, media title), a hover card for the clock (large time and week strip), and
  the wallpaper/theme carousel growing out of the clock island. Islands arrows (‹ ›)
  like Dynamic if the owner wants them.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Reminders > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **Song recognition, as a plugin (owner's idea, 2026-11-10).** "What's playing?" for audio
  on the desktop (a video, a stream, a game): capture a few seconds from PipeWire's monitor
  of the default output (`pw-record --target` the sink monitor), fingerprint it and show
  the title, artist and links in a notification or panel. Shazam has no official public
  API; options are AcoustID/Chromaprint (open, free, but mostly matches full recordings),
  AudD or ACRCloud (paid APIs with free tiers and keys), or an unofficial Shazam client
  (`songrec` in the AUR, works today but can break). Decide the service with the owner;
  audio leaves the computer only when the person asks.
- **World clock, as a plugin.** Other cities and people's local time beside the clock;
  not built in.
- **`eitr-store`.** A separate repository and app for themes, plugins and other
  add-ons: catalog index, submissions and listings; replaces the built-in catalog
  window later.

# 2. To test with the owner

- **Add-ons and the Lockscreens tab (on testing 2026-11-13).** VM-tested: upgrade fallback
  to Eitr, one-time install of the eight designs, login design restored, remove and reinstall
  with the password popup, refusals. On the owner's desktop: the first System Update removes the
  optional designs; the next System Update installs them back (the migration). Then promote.

- **Island style and Side style (on testing 2026-11-13).** Attached Islands, Dynamic and Drop,
  straight sides for Tabs and Centered (Settings > Desktop Bar > Layout); try every layout
  and edge, panels opening from attached pills, auto-hide, then promote.
- **Login on the main display (on testing 2026-11-13).** The login design runs only on the
  largest display and the others stay black; at the next login, check that typing goes
  straight to the password field, then promote.
- **Logout on NVIDIA.** The login screen crashed in the NVIDIA driver when SDDM started
  it again after a logout (black screen). It now uses Qt's basic render loop
  (`eitr-greeter.conf`, on stable 2026-11-11); log out once after updating to confirm.
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

- **Bar crash leftovers.** The owner's two crashes of 2026-10-29 at bar start, a
  PipeWire event rebuilding a Repeater (`QQuickItem::polish` from
  `QQuickRepeater::setModel`), not reproduced since; and the binding loop a hotplug
  logged in DisplaySettingsEditor `width` (VM unplug, 2026-11-04; no cycle in today's
  code, so check it in the next hotplug test before changing anything). DisplayService
  `snapshot`'s loop is fixed.
- **Bar disappears without a trace (2026-11-10, again 2026-11-11).** The bar process
  ended with no error in its log and no core dump (the second time while a full
  `tools/check.sh` ran and the owner used the Audio panel); find what ends it.
- **Hyprland crash on SUPER+T (2026-11-12).** Hyprland 0.57.2 aborted while SUPER+T
  (float + pin) floated a Chrome Google Meet window on the owner's NVIDIA desktop with two
  displays: an inlined check in the dwindle layout's `movedTarget` (re-tiling the window)
  failed. Not reproduced in the test VM (one display, Firefox and kitty, fast and repeated
  presses, fullscreen, pseudo and resized windows). If it happens again, note the window's
  display, fullscreen or picture-in-picture state, then report it upstream with the crash
  report from `~/.cache/hyprland/`.
- **Move expensive work off the UI thread selectively.** Profile interactions first,
  then move demonstrated image-processing, audio-analysis or other costly work into
  bounded asynchronous workers. Keep results tied to the current request so stale
  work cannot overwrite newer state. Consider a native helper only when measured
  benefits justify its build and maintenance cost; retain the existing broker and
  shared ownership model.

# 6. 0.8 release candidate and 1.0.0

0.8 (Muninn) is the exact ISO intended for 1.0; 1.0 (Bifröst) publishes the
promises below. The roadmap table in `distro/RELEASES.md` has the wording.

- **After 1.0: choose Hyprland or niri (decided 2026-11-13).** Parked until 1.0 ships. The
  survey of Hyprland dependencies and the adapter plan are in
  `eitr-testing/ideas/niri/` (INVENTORY.md, PLAN.md). Until then, new settings keep
  compositor-neutral data (as the keybind editor does).
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
