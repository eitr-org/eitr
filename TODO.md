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

- **Plugins.** The owner confirmed the schema v2 plugins work (2026-10-28).
  Still open: runtime QML errors are not attributed to a plugin, and in-process
  QML is not a sandbox.

- **Dock: pinned apps.** The edge dock (opposite the bar) shows open apps; next,
  pinned apps that stay in it when closed, as the owner planned.
- **Light themes.** The owner has ideas for more light themes; create them later.
- **Website Handbook in every language.** The site is translated (`/pt-br/`, `/es/`,
  `/de/`, `/fr/`), but its Handbook chapters still show English; the desktop's
  Handbook already has reviewed translations to publish there.
- **Website evidence and screenshots.** Keep the public pages in step with verified
  desktop behavior. A feature gets a screenshot when it has a screen people look
  for (a panel, menu or wizard) shown on the website or in the Handbook;
  background behavior gets none.
  Describe remote access as verified only after the real-device tests above pass.
- **Search indexing and measurement.** eitr.info is verified in Google Search
  Console and Bing Webmaster Tools with the sitemap submitted (2026-10-22). Check
  that both read it, then track impressions, queries and clicks there without
  adding site analytics. Periodically spot-check whether search/AI answers
  identify Eitr accurately; inclusion and recommendations are not guaranteed.
- **Releases and public evidence.** After the owner records the video, add a website Releases page and prepare
  consistent GitHub Release notes with version, date, changes, checksums,
  tested configurations and known limitations. Publish installation walkthroughs
  and a video, a hardware test matrix, and suitable GitHub feedback templates.
  Keep beta and untested-hardware limits explicit.
- **Public discovery.** After the owner's video and with their approval, prepare release announcements for
  appropriate Linux communities, invite independent testers/reviewers and check
  distro-directory submission requirements. Share reproducible evidence rather
  than promotional claims. Describe Eitr the same way everywhere (repository
  description, README and website), and never present features common to other
  Arch or Hyprland setups as exclusive to Eitr.

# 3. Later

- **Voice reminders, next steps.** Read-only Google/Outlook/iCal subscriptions
  through a secret iCal address are done (Tools > Calendars). Two-way sync
  (creating or editing provider events) needs account sign-in (OAuth, with
  Google's app verification) and remains later.
- **The Eitr logo drawn with runes.** For About (and maybe the welcome banner):
  fill the emblem's shape with Elder Futhark runes in the theme accent, like
  Arch's logo drawn with characters, leaving the inner E cut-out empty.
- **Antigravity as a helper.** Recheck when its command-line tool gains per-run
  permissions or a read-only headless mode; until then it stays a standalone
  assistant. Nothing to do before that.

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

Assistant sessions use full access by default; System > Security > Assistant Access restores permission prompts. Not planned: the rest of the "Not planned now"
list in `distro/RELEASES.md`.
