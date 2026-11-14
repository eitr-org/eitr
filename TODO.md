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
- **Companies: Git identity and cloud accounts per folder (planned 2026-11-14).** Git Accounts
  becomes Companies: each company has folders, a commit identity (one main Git account can serve
  several companies with different emails) and an AWS profile and Google Cloud configuration
  that a terminal uses inside its folders. A default company's cloud accounts apply outside
  them only when the person turns that on. Azure and the other providers come later. Plan in
  `eitr-testing/codex-wip/companies/PLAN.md`; next: Codex brief, then a VM test.
- **Dynamic island, next.** Live activities in the clock island beyond the capture
  indicator (volume/brightness replacing swayosd only in Dynamic, notification
  previews, media title), a hover card for the clock (large time and week strip), and
  the wallpaper/theme carousel growing out of the clock island. Islands arrows (‹ ›)
  like Dynamic if the owner wants them.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Reminders > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **World clock, as a plugin.** Other cities and people's local time beside the clock;
  not built in.
- **`eitr-store`.** A separate repository and app for themes, plugins and other
  add-ons: catalog index, submissions and listings; replaces the built-in catalog
  window later.

# 2. To test with the owner

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

- **Hotplug binding loop.** A VM unplug logged a binding loop in DisplaySettingsEditor
  `width` (2026-11-04); check it in a VM hotplug test and fix it if it comes back.
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
