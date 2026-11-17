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
  (2026-11-11). Share the Login Screen is built (2026-11-17, `distro/system/eitr_remote_login.py`,
  `distro/REMOTE-ACCESS.md`): a system Sunshine while nobody is signed in, with the sharing
  account's identity and paired devices. VM-tested 2026-11-17: boot, sign-in (stops 2 ms after
  logind's new session), sign-out, hand-over to and from the user's own Sharing at login, a
  second account, switch off and Restore Sharing Setup. Next: a real Moonlight connection to
  the login screen on the owner's NVIDIA PC. Headless use (a virtual display sized to the Moonlight client) stays planned in
  `eitr-testing/codex-wip/remote-access-next/PLAN.md`; wake on LAN is left to people who want it.
- **Dynamic island, next.** Short notification, volume/brightness, song, Bluetooth and
  keyboard moments are implemented. Next: a hover card for the clock (large time and week
  strip), and the wallpaper/theme carousel growing out of the clock island. Islands arrows
  (‹ ›) like Dynamic if the owner wants them.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Reminders > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **Clock app (phase 1 done 2026-11-17; alarms next).** One Eitr app (`clock/ClockWindow.qml`)
  opened from Apps (SUPER + Space), Walker (Main > Tools > Clock), the timer ring beside the clock
  (every layout and Drop's pill) and Control Center > Tools; no new bar icon. A chronograph dial
  (`clock/ChronoDial.qml`) with Timers, Stopwatch and Focus is done (World clock stays a plugin); their state survives bar restarts (`$XDG_STATE_HOME/eitr/clock.json`).
  - **Next, phase 2 (Alarms):** time, name, repeat days and a sound; one switch each. Ringing,
    the alarm takes the screen with the song and an animated effect until **Stop** or
    **Snooze** (the owner will record the effect they want; build that part after).
    Reminders' existing schedule and notifications stay the source of truth, so an alarm is a
    reminder that rings.
- **Desktop widget ideas (2026-11-17).** New official plugin widgets in `eitr-org/eitr-plugins`,
  placed and moved like the Visualizer (`distro/PLUGINS.md`, Desktop widgets):
  - **Notes:** a sticky note on the desktop to type into, kept between logins.
  - **Hardware:** CPU, GPU, RAM, storage and network at a glance, from the bar's own hardware
    data (no second reader).
  - **More Visualizer styles:** today Wave and Bars; add a circle (bars around a ring) and
    other shapes.
- **Eitr Store, next.** `eitr-org/eitr-store` is public with the schema 2 index (empty: the
  community index had no entries yet) and its validation workflow. Screensavers and other
  future kinds are a registry entry plus a backend (`distro/STORE.md`).
- **Backup and Restore (Phases 1–3 built 2026-11-17).** Encrypted `tar.zst.age` archives
  via `eitr backup` / `eitr-backup`, `Settings > System > Backup and Restore`, Walker
  (`System > Backup and Restore`), Welcome setup card, interactive wizard on `eitr_wizard.py`,
  per-folder sizing, official/AUR/Flatpak/plugin/Store reinstall with review and restore undo
  journals. Remaining: Git/cloud/Wi-Fi secret migration (Phase 4) and live VM verification
  (Phase 5). Plan: `eitr-testing/codex-wip/backup-restore/PLAN.md`.
- **Ollama plugin (built 2026-11-16).** Held in the private `eitr-plugins-night-test`
  repository (local branch in `eitr-testing/codex-wip/plugins-night/ollama`) until the owner
  says it is ready; Radio Globe and Phone Link went to `eitr-org/eitr-plugins` on 2026-11-16.
  The Ollama panel cannot change the local model yet: the core fixes `qwen3:4b`.
- **AI Usage as a built-in plugin (idea 2026-11-16).** Like Weather (`distro/plugins/bundled`):
  installed by default, removable for people who do not use AI.

# 2. To test with the owner

- **Wallpaper per display: the parts not tried yet.** The switch, preview, carousel and
  theme resets passed the owner's test (2026-11-10); still untried: plugging a display
  in and out, and each display's wallpaper coming back at login.

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
