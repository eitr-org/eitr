# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Smaller items
3. Later
4. 0.8 release candidate and 1.0.0

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

# 2. Smaller items

- **Light themes.** The owner has ideas for more light themes; create them later.
- **Performance: measure on real weak hardware.** Polling now follows events and
  closed panels stay quiet: idle launches in a 4-core VM fell from ~800 to ~40 a
  minute (CPU 25% to 1% of one core). Still to check on an old laptop, with
  multiple monitors and with OBS started straight into the tray.
- **Shared data service for the bar (refactor, after the improvements).** One
  long-running helper instead of ~33 short-lived scripts: one reader per piece of
  data, one set of tests, consistent timeouts and refresh-on-open, easier to trace.
  Migrate one panel at a time.
- **Maintainability refactors, after the data service.** In this order:
  1. Split `shell.qml` (about 2,500 lines): data owners first, then one bar section
     at a time, keeping the centred clock, panel anchors and click-through gaps.
  2. Control Center's style settings: give the cursor/font helpers structured
     (JSON) answers instead of parsing plain text from three separate runs.
  3. One definition per menu row, shared by browsing and search (including Learn's
     shortcut list and the search index).
  4. Notification image memory: cap decoded image bytes without shortening history.
  5. Menus with live contents (accounts, plugins) get the same type-to-search-below
     behaviour as fixed menus, through one shared adapter.
  6. Retire the older VS Code / LazyVim project providers once nothing uses them.
  Only if profiling shows a need: sharing plugin data between copies of the same
  widget, and one shared window list for the dock, Focus and OBS.
- **Web Apps show their own icon in the dock.** A web app opened from Install >
  Web Apps (for example YouTube Music) shows a generic grid icon in the dock
  instead of its app icon; match the web app's window class to its desktop entry
  and icon.
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
- **Public discovery: announce the release right after the video.** With the owner's
  approval, post the release on Linux community sites and forums and on Reddit (for
  example r/linux, r/archlinux's rules permitting, r/hyprland and r/unixporn), each
  written for that community and following its self-promotion rules. Invite
  independent testers/reviewers and check distro-directory submission requirements
  (for example DistroWatch). Share reproducible evidence rather
  than promotional claims. Describe Eitr the same way everywhere (repository
  description, README and website), and never present features common to other
  Arch or Hyprland setups as exclusive to Eitr.

# 3. Later

- **Voice reminders, next steps.** Read-only Google/Outlook/iCal subscriptions
  through a secret iCal address are done (Tools > Calendar Sources). Two-way sync
  (creating or editing provider events) needs account sign-in (OAuth, with
  Google's app verification) and remains later.
- **The Eitr logo drawn with runes.** Previews of the emblem filled with Elder
  Futhark runes are ready and kept outside the repository; the owner likes the
  36-row versions and will decide later where (if anywhere) to use them.

# 4. 0.8 release candidate and 1.0.0

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
