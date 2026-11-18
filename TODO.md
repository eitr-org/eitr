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

- **VPN plugins, what is left.** Tailscale, WireGuard and NetworkManager VPN are official
  plugins on `eitr-org/eitr-plugins` main (WireGuard and NetworkManager VPN merged 2026-11-18
  after a VM test: install with their packages, import, connect with a real WireGuard peer on
  iwd and on NetworkManager, copy, disconnect, remove, update and plugin removal).
  - An OpenVPN profile connected to a test server (TLS and address) but no data crossed that
    server's tunnel; try a real OpenVPN server before calling OpenVPN traffic verified.
  - Plugin package cleanup now includes pulled-in dependencies (2026-11-18): VM-test removing
    NetworkManager VPN again and check `pacman -Qdt` is empty afterwards.
  - Removing a wg-quick tunnel asks for the password through `pkexec rm`; an `eitr-system`
    action would show a clearer prompt.
- **Remote access, next.** Sharing works at home, away through Tailscale and from a Mac
  (2026-11-11). Share the Login Screen is built (2026-11-17, `distro/system/eitr_remote_login.py`,
  `distro/REMOTE-ACCESS.md`): a system Sunshine while nobody is signed in, with the sharing
  account's identity and paired devices. VM-tested 2026-11-17: boot, sign-in (stops 2 ms after
  logind's new session), sign-out, hand-over to and from the user's own Sharing at login, a
  second account, switch off and Restore Sharing Setup. On the owner's NVIDIA PC (2026-11-18)
  Moonlight on a Mac streamed the login screen (X11 capture of SDDM's display) and was handed to
  the user's own Sharing at sign-in. Headless use (a virtual display sized to the Moonlight client) stays planned in
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
- **Desktop widget ideas (2026-11-17).** Remaining official plugin widget item in `eitr-org/eitr-plugins`
  (`distro/PLUGINS.md`, Desktop widgets; **Notes** and **Hardware** are implemented):
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
- **Clean My Eitr, on a real laptop (VM-tested 2026-11-18).** In the VM the overlay, the
  empty `clean` submap (SUPER shortcuts did nothing), the inhibitor, a short Esc tap staying
  locked, a 3-second Esc hold leaving and `eitr clean stop` all worked; Ctrl+Alt+F still
  switches consoles (no Hyprland option blocks it; documented in the Handbook). Still to try on
  real hardware: touchpad gestures and laptop Fn keys handled by firmware.
- **Ideas from Omarchy 4.5, Ryoku 1.1 and Caelestia (picked by the owner 2026-11-18).**
  Ryoku and Caelestia are GPL-3 and Omarchy MIT: adapted code keeps their notices.
  - **Keyboard layout on the lock and login screens** (Ryoku): show the active layout and
    switch it by click or Ctrl+Alt+Space, so a lock taken on a second layout still accepts
    the password. Neither the lockscreen nor SDDM's `login/Main.qml` shows it today.
  - **Lockscreen password field** (Caelestia): a show-password eye and Ctrl+U /
    Ctrl+Backspace to clear, in every lock design.
  - **Copy-code and open-link buttons on notifications** (Omarchy `shell/plugins/notifications/Detect.js`):
    only when the text names a number as a code, so order numbers and ports are not offered;
    tested on its own, added to `NotificationCard.qml`'s actions.
  - **AI usage pace** (Ryoku): a trend arrow, ahead of or behind an even pace, and when a
    limit would fill, from the reset time and window length AI Usage already reads.
  - **Sound output change moment** (Caelestia): "Now using: Headphones" as a clock moment
    when the default output changes, not a new pop-up.
  - **Typing Japanese, Korean and Chinese** (Omarchy `docs/input-methods.md`): fcitx5 with a
    theme-coloured candidate window and a shortcut to switch, packages in `distro/`
    manifests, offered with those languages.
  - Smaller:
    - **Crash notifications** (Omarchy `omarchy-crash-watch`): a notice when an app
      crashes, with a way to mute that app; Check This PC already reads the coredumps.
    - **Battery warning levels** (Caelestia): the 10% and 5% warnings become settings.
    - **Window info page** (Caelestia `modules/windowinfo/`): the active window's app, title,
      process, size, floating and pinned state, with move/float/pin/close; a Control Center
      or Walker page, no bar icon.
    - **Disk and network speed tests** (Omarchy): a Control Center page.
    - **Window previews in the edge dock** (Ryoku): reuse Overview's in-memory previews,
      with an off switch (a Hyprland capture bug can drop the capture connection).

# 2. To test with the owner

- **Wallpaper per display: the last part not tried yet.** The switch, preview, carousel and
  theme resets passed the owner's test (2026-11-10), and unplugging and replugging a display
  (HDMI) brought its own wallpaper back (2026-11-17). Still untried: each display's wallpaper
  coming back at login.

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
