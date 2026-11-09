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

- **Walker > Settings follows the Settings app's groups (asked 2026-11-09).** Use the
  app's six groups and names in Walker so a setting lives in the same place in both:
  Devices (today's Connectivity, Devices & Input and Language), Desktop (today's Style;
  its quick choice lists such as theme, wallpaper and cursor stay as submenus), Apps &
  Keys (keybinds, default apps), Accounts & Security (drop the Users and Update Password
  rows the Settings Security page no longer has), System. Control Center and Dotfiles
  stay at the bottom. Keep every row's action, parents for Shift+Backspace, search and
  Learn entries; follow `walker/MENU-DEFINITIONS.md`.
- **Keybinds and window rules editors.** Settings > Keybinds only lists shortcuts today:
  rebind one by pressing the new keys, with clash warnings, reset to default and the
  change kept in the person's own config. Window rules: pick an app and choose
  "always float", workspace, size or opacity from a form instead of editing Lua.
- **VPN plugins, Taildrop and Tailscale out of the default install (agreed 2026-11-09,
  to do together with the owner).**
  - Three official plugins in `eitr-org/eitr-plugins`: Tailscale (today's bar icon, panel
    and actions, plus Taildrop: send files to the person's other Tailscale machines from
    a menu, incoming files arriving as a notification; operator setup moves from the core
    root helper to the plugin's own reviewed step), WireGuard (import a config,
    connect/disconnect, status) and NetworkManager VPN (OpenVPN/OpenConnect profiles;
    explains the NetworkManager backend when on iwd).
  - Plugin format gains an optional `packages` field: official Arch/Eitr repositories
    only. The install review lists them; after approval they install with the
    administrator password, ideally inside the Themes & Plugins session, otherwise a
    terminal that returns to it. Packages already installed are detected and not
    reinstalled. Removing the plugin offers to remove only the packages it installed
    that nothing else needs.
  - Plugins never install silently. A one-time update step installs the official
    Tailscale plugin (pinned, reviewed) on desktops that already have Tailscale, with a
    notification; Tailscale is never uninstalled automatically. New installs no longer
    include it.
  - Remove the Tailscale rows from Walker; keep Install > VPN.
  - Order: plugin `packages` field (VM-tested), the three plugins, then remove Tailscale
    from the core and ship the update step after the plugin passes a VM test.
- **Lockscreens tab in the catalog (decided 2026-11-04).** A Lockscreens tab in
  Themes & Plugins, working like themes and plugins. Eitr and Theme Wallpaper are
  permanent (no trash icon). The other designs shipped today move to an official
  `eitr-org/eitr-lockscreens` repository, stay installed by default on fresh and
  existing desktops (as the extra themes did), and can be uninstalled and
  reinstalled from the tab. New designs come only from that repository at a pinned,
  reviewed version; there is no community or third-party source, since a design runs
  on the screen that reads the password. The design in use shows no trash icon.
  Uninstalling uses the catalog's usual confirmation sheet; when some of your own
  lockscreens (Walker > Style) are built on that design, the sheet says so, and they
  are hidden rather than deleted, coming back if the design is reinstalled.
  Open question (paused 2026-11-04): designs also draw the SDDM login screen, which
  runs as its own user and reads only system files (`/usr/share/sddm/themes/
  desktop-lockscreen-*`, staged by `install-login.py`). Per-user installs like themes
  could not reach it, so designs would likely become signed packages in Eitr's
  repository, installed and removed with one password prompt, for every account.
- **Settings Overview leftovers.** Network throughput needs a shared data topic; each
  theme's Overview illustration is still to be drawn (the wallpaper until then).
- **Git & Cloud for many companies** (Walker; Settings no longer has the page): group
  each company's cloud profiles and contexts with its Git identity and folder rules.
- **Dynamic island, next.** Live activities in the clock island beyond the capture
  indicator (volume/brightness replacing swayosd only in Dynamic, notification
  previews, media title), a hover card for the clock (large time and week strip), and
  the wallpaper/theme carousel growing out of the clock island. Islands arrows (‹ ›)
  like Dynamic if the owner wants them.
- **Wallpaper preview and monitor/workspace assignments.** Preview still images
  temporarily without changing saved choices or the committed palette; cancel or
  closing the picker restores the saved wallpaper. Add assignments with the precedence
  workspace, monitor, global choice, then shipped default. Define restore behavior for
  login, monitor disconnect/reconnect and removed workspaces; rapid workspace switches
  should settle on the latest choice without restarting unrelated outputs.
- **Voice reminders, two-way sync.** Read-only Google/Outlook/iCal subscriptions are
  done (Tools > Calendar Sources). Creating or editing provider events needs account
  sign-in (OAuth, with Google's app verification).
- **World clock, as a plugin.** Other cities and people's local time beside the clock;
  not built in.
- **`eitr-store`.** A separate repository and app for themes, plugins and other
  add-ons: catalog index, submissions and listings; replaces the built-in catalog
  window later.
- **Choose Hyprland or niri (owner's idea, 2026-11-09).** Let a person pick the
  compositor at install time and in Settings, with niri as a supported second session.
  Needs first: a list of everything that talks to Hyprland (Lua config, `hyprctl` and
  its IPC in the bar, Overview, workspaces, window rules, hypridle/hyprlock,
  screenshots, Focus groups) and an adapter so the bar and helpers ask one Eitr
  interface instead. Decide what niri does not offer, then VM-test both sessions
  before any release.

# 2. To test with the owner

- **Remote access.** Moonlight, Sunshine and Tailscale are built and inactive until set
  up (`distro/REMOTE-ACCESS.md`). Home network (2026-10-21/22, one and two monitors)
  and away from home through Tailscale (2026-10-21) work with a MacBook. Next: fix what
  those tests find, then call remote access ready in the Handbook and on the website.
  Afterwards, each separately: headless use, access before login, wake on LAN.
- **Scrolling layout, Settings search and the About logo (shipped to testing 2026-11-09).**
  Scrolling with real windows and its shortcuts; searching for a setting with the
  keyboard, including controls that need hardware or an account; the rune logo in a real
  System > About terminal.
- **Themes & Plugins Update all.** Shipped untested: it appears only when an installed
  theme or plugin has an update. Try it the next time one does.
- **The Eitr logo drawn with runes elsewhere.** The owner likes the 36-row versions;
  beyond the About choice above, they decide later where else (if anywhere) to use it.

# 3. Waiting on others

- **hyprpaper crash without a GPU.** hyprpaper segfaults in VMs without 3D
  acceleration (hyprwm/hyprtoolkit#144); the bar draws the still wallpaper on any
  screen hyprpaper does not answer for. Drop the note once a fixed hyprtoolkit ships.
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
  `QQuickRepeater::setModel`), not reproduced since; and the binding loops a hotplug
  logs in DisplayService `snapshot` and DisplaySettingsEditor `width`.
- **Split the large files marked "To improve".** The files listed with their reasons in
  `tools/file-size-baseline.json`: `eitr-system.py` by area behind the same CLI, the
  Themes & Plugins content (cards, sheets, Git address flow), software installs, Git
  Accounts (model vs apply/CLI), calendars and reminders (parsing vs scheduling), OBS
  control, own-style import, and the Display panel (display list, night light, power).
  One at a time, when it is next worked on; no behaviour change.
- **Move expensive work off the UI thread selectively.** Profile interactions first,
  then move demonstrated image-processing, audio-analysis or other costly work into
  bounded asynchronous workers. Keep results tied to the current request so stale
  work cannot overwrite newer state. Consider a native helper only when measured
  benefits justify its build and maintenance cost; retain the existing broker and
  shared ownership model.

# 6. 0.8 release candidate and 1.0.0

0.8 (Muninn) is the exact ISO intended for 1.0; 1.0 (Bifröst) publishes the
promises below. The roadmap table in `distro/RELEASES.md` has the wording.

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 0.8 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Repeated clean installs and destructive recovery tests** of the 0.8 ISO in
  isolated VMs, until install, maintenance and recovery are reproducible.
- **Hardware we do not have**: laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work; the results become 1.0's supported hardware matrix.
- **1.0 documents**: supported hardware matrix, tested upgrade paths, rollback
  limitations, security-update process, compatibility policy.

Assistant sessions use full access by default; Settings > AI Assistant > Assistant
Access restores permission prompts. Not planned: the "Not planned now" list in
`distro/RELEASES.md`.
