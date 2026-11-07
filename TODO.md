# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Catalog: what is left
3. Smaller items
4. Later
5. 0.8 release candidate and 1.0.0

# 1. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built and inactive until set up.
Fresh installs include them; existing machines install missing apps on demand
(`distro/REMOTE-ACCESS.md`). With the owner and a MacBook, in this order:

1. Home network, tested 2026-10-21 on the owner's PC (one monitor) with Moonlight
   on a MacBook: setup, start sharing, pairing by IP, video with no noticeable
   delay, keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start
   at login and Stop Sharing all work; two monitors and Restore Sharing Setup
   followed on 2026-10-22. Controllers are not needed.
2. Away from home works (2026-10-21): Tailscale setup, sign-in and connect on the
   owner's PC, and the Mac reached the PC through it.
3. Fix what the tests find; only then call remote access ready in the Handbook
   and on the website.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 2. Catalog: what is left

The Themes & Plugins catalog, the 12 extra themes in `eitr-org/eitr-themes`, the
native install review and the community index `eitr-org/eitr-community` shipped to
stable on 2026-11-04 (`distro/THEMES.md`, `distro/COMMUNITY.md`).

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
- **Plugin media.** Real screenshots and short clips for Visualizer and Lofi Radio
  (`media`/`preview` in `eitr-org/eitr-plugins`), captured only with the owner's go.

# 3. Smaller items

- **Desktop ideas (agreed 2026-11-05).** Each is Eitr's own design and code.
  Done: notification actions, display rotation, event sounds, screenshot pin and beautify.
  Next:
  - Taildrop: send files to the user's other Tailscale machines from a menu; incoming
    files arrive as a notification.
  - Window rules and keybinds editors: "always float this app" and rebinding shortcuts
    from Settings, without editing Lua by hand.
  - First-run welcome that previews the bar layouts and lets the user pick one.
  - **Shared Settings controls and monitor map:** Shared palette-driven controls now serve Settings, display choices, workspace previews, theme filters, recording scenes and laptop power profiles. Displays and the Display panel share a positioned monitor map with trial outlines and click selection; fixtures cover dark/light, single, unequal and rotated screens.
  - **Settings presentation:** Connections, Displays and Appearance tabs; tab-aware search/IPC with network alias; reusable visual choice cards and a saved theme/website Settings palette. Offscreen dark/light and website comparisons cover the window and preview controls.
  - **Settings app (all page groups implemented).** One window with a grouped sidebar and a
    search that finds individual settings: Overview (System); Devices (Displays,
    Sound, Connections, Input); Desktop (Appearance, Desktop Bar, Windows,
    Lockscreen, Notifications, Focus); Apps & Keys (Keybinds, Default apps);
    Themes and Plugins retain their separate catalog window; Accounts & Security; System (Updates &
    Channel, Check This PC, About). The
    Overview shows the profile picture and name, live CPU/GPU/RAM/network from the bar's
    existing data, version and channel, resolution, uptime, the theme palette and a large
    illustration per theme (to be drawn; the wallpaper until then). Settings chooses theme
    colours or the website palette and stays opaque. Each setting has one plain
    line and a "Learn more" link into the Handbook, which stays a separate window.
    SUPER + , opens Settings; the Control Center moves to SUPER + I and keeps quick
    toggles, sliders, media, plugins and tools, with an "All settings" button.
    Walker's Settings rows will open the matching page. The frame, Overview, embedded
    separate Themes and Plugins pages and shortcut split are implemented.
    Desktop and Devices reuse the existing inline controls. Keybinds, Default apps, Users,
    Git & Cloud, Security, Updates, Check This PC and About are implemented with shared
    readers and existing confirmed actions. The Control Center is slimmed: its Style
    and Settings pages are gone, and its All settings button opens Settings. The
    Handbook and Themes & Plugins share the Settings frame, sidebar, page header and
    cards. Dropdowns support type-ahead and screen-bounded floating lists; Dynamic
    panels reserve navigation space, and shared sidebars support Square corners.
    Next: refine individual-setting search. Network throughput needs a shared
    data topic; theme artwork currently uses the wallpaper.
  - **Window gaps preference implemented.** None, Small, Default (6 px inner,
    12 px outer) and Large share the local corner preference and survive theme
    changes and reloads. Settings and Walker use one catalog.
    Live hardware acceptance across bar layouts remains pending.

- **Light themes.** The owner has ideas for more light themes; create them later.
- **hyprpaper crash without a GPU: follow upstream.** hyprpaper segfaults in VMs
  without 3D acceleration (hyprwm/hyprtoolkit#144); the bar now draws the still
  wallpaper on any screen hyprpaper does not answer for. Drop the note once a fixed
  hyprtoolkit ships.
- **Website evidence and screenshots.** Keep the public pages in step with verified
  desktop behavior. A feature gets a screenshot when it has a screen people look
  for (a panel, menu or wizard) shown on the website or in the Handbook;
  background behavior gets none.
  Describe remote access as verified only after the real-device tests above pass.
- **Search indexing and measurement.** eitr.info is verified in Google Search
  Console and Bing Webmaster Tools. Bing reads the sitemap (2026-10-29); Google
  indexes the home page but its sitemap entry was stuck on "Couldn't fetch", so the
  owner resubmitted it (2026-10-29): check it reads Success. Then track impressions,
  queries and clicks there without
  adding site analytics. Periodically spot-check whether search/AI answers
  identify Eitr accurately; inclusion and recommendations are not guaranteed.
- **Releases and public evidence.** After the owner records the video, add a website Releases page (generated
  from the same release notes as the GitHub Release, kept per area as they land) and prepare
  consistent GitHub Release notes with version, date, changes, checksums,
  tested configurations and known limitations. Publish installation walkthroughs
  and a video, a hardware test matrix, and suitable GitHub feedback templates.
  Keep beta and untested-hardware limits explicit.
- **Public discovery: announce the release right after the video.** Status
  (2026-11-02): the preview video is on YouTube and the website; the DistroWatch
  submission was emailed (expect a long waiting list); r/unixporn needs more account
  karma before posting, so build it with genuinely helpful comments first. With the owner's
  approval, post the release on Linux community sites and forums and on Reddit (for
  example r/linux, r/archlinux's rules permitting, r/hyprland and r/unixporn), each
  written for that community and following its self-promotion rules. Invite
  independent testers/reviewers and check distro-directory submission requirements
  (for example DistroWatch). Share reproducible evidence rather
  than promotional claims. Describe Eitr the same way everywhere (repository
  description, README and website), and never present features common to other
  Arch or Hyprland setups as exclusive to Eitr.

# 4. Later

- **World clock, as a plugin.** Other cities and people's local time beside the clock;
  not built in.
- **Bar crash leftovers.** The VM crashes (hidden bar plus a panel closing, the bar's
  screen unplugged) are fixed: the bar window stays mapped and closed panels leave it.
  Still open: the owner's two crashes of 2026-10-29 at bar start, a PipeWire event
  rebuilding a Repeater (`QQuickItem::polish` from `QQuickRepeater::setModel`), not
  reproduced since; and the binding loops a hotplug logs in DisplayService `snapshot`
  and DisplaySettingsEditor `width`.
- **Move expensive work off the UI thread selectively.** Profile interactions
  first, then move demonstrated image-processing, audio-analysis or other costly
  work into bounded asynchronous workers. Keep results tied to the current
  request so stale work cannot overwrite newer state. Consider a native helper
  only when measured benefits justify its build and maintenance cost; retain the
  existing broker and shared ownership model.
- **Wallpaper preview and monitor/workspace assignments.** Preview still images
  temporarily without changing saved choices or the committed palette; cancel
  or closing the picker restores the saved wallpaper. Add assignments with the
  precedence workspace, monitor, global choice, then shipped default. Define
  restore behavior for login, monitor disconnect/reconnect and removed
  workspaces; rapid workspace switches should settle on the latest choice
  without restarting unrelated outputs. Preserve existing theme workflows.
- **Voice reminders, next steps.** Read-only Google/Outlook/iCal subscriptions
  through a secret iCal address are done (Tools > Calendar Sources). Two-way sync
  (creating or editing provider events) needs account sign-in (OAuth, with
  Google's app verification) and remains later.
- **Dynamic island, next.** Shipped to stable: the Dynamic layout (three centred
  islands that expand on hover, grow into their panels with ‹ › to step through an
  island's panels, and slide aside for each other) and Islands cards growing from
  their pills and pushing neighbours. Next: live activities in the clock island beyond
  the capture indicator (volume/brightness replacing swayosd only in Dynamic,
  notification previews, media title), a hover card for the clock (large time and week
  strip), and the wallpaper/theme carousel growing out of the clock island. Islands
  arrows (‹ ›) like Dynamic if the owner wants them.
- **The Eitr logo drawn with runes.** Previews of the emblem filled with Elder
  Futhark runes are ready and kept outside the repository; the owner likes the
  36-row versions and will decide later where (if anywhere) to use them.

# 5. 0.8 release candidate and 1.0.0

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

Assistant sessions use full access by default; Settings > Security > Assistant Access restores permission prompts. Not planned: the rest of the "Not planned now"
list in `distro/RELEASES.md`.

- [ ] Handbook revision with live illustrations: review every chapter, and show the thing being explained, rendered in QML with the current theme (the bar in each layout with its parts labelled, panels, the Control Center, Settings pages, menus), like Settings' picture previews, instead of text alone or static screenshots.
- [ ] A welcoming first page: the first-login Getting Started chapter is too plain for new users (a first-time reader said they would close it right away). Redesign it as an inviting welcome with the theme's art, a short animated tour of the desktop (bar, launcher, Settings, themes), large friendly setup cards and subtle motion, keeping it read-only, offline and quick to dismiss.
- [ ] Settings > Users: an administrator page for other accounts (create, remove, change type or password), separate from the User page for your own account. Reuse Walker's reviewed Create User flow and the root helper behind typed confirmation.
- [ ] Settings > Git & Cloud for many companies: group each company's cloud profiles and contexts with its Git identity and folder rules.
- [ ] Create a separate `eitr-store` repository and app for themes, plugins and other add-ons: catalog index, submissions and listings; replace the built-in catalog window later.
- [ ] Move Tailscale out of the default install into a suggested plugin; retain the current install and remote-access workflows until that migration is implemented.
