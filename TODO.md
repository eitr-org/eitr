# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Catalog: official themes and plugins
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

# 2. Catalog: official themes and plugins

A movable, resizable catalog window that lists every theme and plugin: what is
installed and what the official repositories offer. Tested on the testing
channel first; the website changes only once it reaches stable.

- **Built in (13):** the nine realms, Eitr, Eitr Light, Afterglow and Ragnarok.
- **Moved to `eitr-org/eitr-themes` (12):** Catppuccin, Catppuccin Latte,
  Daylight, Gruvbox, Jade, Kanagawa, Moss, Nord, One Dark Pro, Rosé Pine,
  Stillwater and Wisteria. Eitr Light stays the only built-in light theme until
  new light themes are made.
- **Installed** lists everything on the machine as Built in, Official
  (`eitr-org/eitr-themes` or `eitr-org/eitr-plugins`, decided by repository
  address only) or Third-party, each with use/open, update check and remove.
  The **Official** tab combines built-ins and official repositories; **Community**
  reads the community index. Themes and Plugins are the two sidebar rows.
- **Download only what is chosen.** Each repository carries a small index (id,
  name, description, size, small preview). The catalog fetches the index and
  visible previews only while open; installing several selected items shows one
  review with the total size and fetches only their folders. Updates are checked
  in System Update, never on a timer.
- **No terminal inside the catalog.** Pasting a third-party Git address, the
  review, the AI check, progress and errors all happen in the window. Walker and
  the Control Center keep their terminal flows; both front ends call the same
  install code, so the safety checks cannot drift. Network reads and installs go
  through a bar data domain.
- **Themes are data.** A versioned theme format (like the plugins'
  `schemaVersion`); themes containing executables are refused.
- **Existing users.** Someone using a moved theme gets it installed from the
  official repository by the update, so their desktop does not change.
- **Backend:** the versioned data-only theme format, sparse Git index and JSON
  install/update/remove backend are implemented; see `distro/THEMES.md`. The
  app/editor files are generated locally from trusted official integrations or
  palette defaults; downloaded packages contain data only.
- **Lockscreens (owner deciding).** Lockscreen designs are QML that runs in the
  screen reading the password, so only official designs from an
  `eitr-org/eitr-lockscreens` repository would be offered; third-party designs are
  refused and the owner's own lockscreens stay settings on an installed design.
  Which designs stay built in is still open.
- **Catalog window (built, owner reviewing).** A movable, resizable window the
  shortcut toggles; the Handbook shares its window component. Sidebar: Themes,
  Plugins; browser-style tabs (the selected one joins the page): Official, Community,
  Installed. Theme cards show palette swatches; clicking an installed theme applies
  it, and Sun/Moon filter light or dark themes (all by default, like the theme
  carousel). Multi-select theme installs, updates checked on open, and removal.
  Removing a built-in theme hides it (Show hidden restores; Eitr and the current
  theme cannot be hidden).
- **Community index `eitr-org/eitr-community`.** Pointers only, one JSON file per
  entry under `themes/` and `plugins/` (plugins pin an exact commit),
  `removed.json`, a generated `index.json`, and CI running
  `tools/community-index.py --check --verify` (format: `distro/COMMUNITY.md`).
  Community themes follow their author's repository; community plugin updates are
  new pull requests the owner reviews. Lockscreens stay official-only.
- **Order:** the owner's review of the catalog window, then the
  native install review, then move the 12 themes (they stay here until the
  installer works).

# 3. Smaller items

- **Light themes.** The owner has ideas for more light themes; create them later.
- **Performance: measure on real weak hardware.** Polling now follows events and
  closed panels stay quiet: idle launches in a 4-core VM fell from ~800 to ~40 a
  minute (CPU 25% to 1% of one core). Still to check on an old laptop, with
  multiple monitors and with OBS started straight into the tray.
- **Walker slow to open after a reboot.** Reported 2026-10-30. Elephant and the search
  index answer in milliseconds after login, so the delay is elsewhere (Walker's
  window, or what else starts then). The owner will record the next reboot.
- **Dock: magnify on hover.** Hovering a dock icon enlarges it and its neighbours
  on a smooth falloff (the hovered icon largest, the next ones a little), like
  macOS, growing away from the screen edge on all four dock edges without moving
  the dock's base or shifting other bar items. Off with Reduce motion; keep icon
  hit areas, tooltips and running indicators aligned. Owner's reference: a macOS
  dock screenshot (2026-11-03).
- **Choice lists: remaining copies.** Bar layouts and update channels still repeat
  their option lists across files; move them into `tools/choice-lists.json` when
  next touched.
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
- **Releases and public evidence.** After the owner records the video, add a website Releases page and prepare
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

- **Performance baselines on weak hardware.** Use `tools/perf-baseline.py`
  ([guide](distro/PERFORMANCE.md)) for comparable before/after measurements on
  real weak hardware; collect instrumented frame runs separately.
- **Bar crashes when panels or screens go away quickly.** Live checks (2026-11-02,
  VM): cycling every Control Center page, a plugin install/removal and three
  monitor hotplugs all left data subscriptions at their baseline. But Quickshell
  segfaults inside Qt in about half the runs of: open the Settings sections, switch
  to Style, open its sections, then `panels close` (`QQuickWindowPrivate::dirtyItem`
  from `setVisible`); and once while a hotplugged monitor was removed
  (`QQuickItemPrivate::derefWindow`). Focus on/off in the VM crashed it the same way
  (`QMetaObject::cast`). The owner's PC has three such crashes since 2026-10-19.
  Find the QML item involved (debug-symbol Quickshell), then fix it here or report
  it upstream. Hotplug also logs binding loops in DisplayService `snapshot` and
  DisplaySettingsEditor `width`.
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
- **`eitr check`: plain-language findings.** `eitr check` (Settings > System >
  Maintenance > Check This PC) already runs read-only checks and copies a redacted
  report. Next: add GPU driver, displays and audio, open it from the Control Center,
  and lead each problem with one plain sentence on what it means and what to try.
- **`eitr matrix`: falling runes in the terminal.** A fun command that rains Elder
  Futhark runes down the terminal in the current theme's colors, like the Matrix,
  until a key is pressed. A working prototype exists outside the repository
  (used for the 0.7 preview video); give it a home under `distro/bin/eitr`, a test
  for resize and clean exit, and a Learn/Handbook mention.
- **Dynamic island.** The clock pill grows into a live surface for what is
  happening now, then shrinks back: media with controls, volume/brightness
  changes, an incoming notification, a running screen recording (with a stop
  button and the chosen area), timers and reminders. One event at a time with a
  clear priority; it never adds bar icons and keeps the clock screen-centred.
  Start from the Islands layout's clock pill; decide whether it is its own layout
  or an option of Islands, Centered and Full. Owner's reference: a Hyprland
  "dynamic island" video with area screen recording (2026-11-03).
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
