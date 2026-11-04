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

- **Lockscreens (owner deciding).** Lockscreen designs are QML that runs in the
  screen reading the password, so only official designs from an
  `eitr-org/eitr-lockscreens` repository would be offered; third-party designs are
  refused and the owner's own lockscreens stay settings on an installed design.
  Which designs stay built in is still open.
- **Plugin media.** Real screenshots and short clips for Visualizer and Lofi Radio
  (`media`/`preview` in `eitr-org/eitr-plugins`), captured only with the owner's go.

# 3. Smaller items

- **Light themes.** The owner has ideas for more light themes; create them later.
- **Walker at login: start Elephant earlier.** After the fix, Walker is usable about
  7.4 s after login (was ~12.5 s; measured 2026-11-04). Elephant still starts ~3 s
  after the bar process, behind the wallpaper check and the bar launch; starting it
  first in `hypr/scripts/session-start.sh` should bring Walker to ~4 s.
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
