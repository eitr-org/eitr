# Releases

Organization profile Flatpaks now install for the desktop user at the first boot
with a network connection, avoiding extra-data sandbox failures in the installer
chroot. Failed installations remain queued for the next boot.

EITR releases use semantic versions with a Norse codename per minor release.
`distro/release.json` is the single source: the package version, About, the
problem report and the ISO name and boot menu all read it.

| Version | Codename | Stage | Milestone |
|---|---|---|---|
| 0.3.0 | Ymir | alpha | Desktop code shipped by the package; offline installer, signed package repository, factory reset, dual boot |
| 0.4.0 | Audhumla | alpha | Updates through System Update, tested from the previous release |
| 0.5.0 | Yggdrasil | beta | Automated VM install, upgrade and reset tests |
| 0.6.0 | Mimir | beta | First public preview: a download for early users |
| 0.6.1 | Mimir | beta | The public preview's everyday features: dictation, package search, Tools menu, display settings, ultrawide wallpapers |
| 0.6.2 | Mimir | beta | Updates served from download.eitr.info; Clipboard History newest first |
| 0.6.3 | Mimir | beta | Real-desktop screenshots on the site, smaller downloads (JPEG wallpapers), check marks in Install lists |
| 0.6.4 | Mimir | beta | Translations (Portuguese, Spanish, German, French), multi-monitor arrangement, Control Center, AI assistants, crash help, OBS defaults |
| 0.7.0 | Huginn | beta | Fixes from early users' real-hardware installs; release-candidate hardening |
| 1.0.0 | Bifröst | stable | Supported upgrades between releases |

Milestones we can verify ourselves (virtual machines and the owner's desktop)
come first. Anything that needs hardware we do not have, such as laptops, other
GPUs or a real Windows/BitLocker disk, waits for the public preview and lands in
0.7.0 or later; 1.0.0 does not have to come soon.

Later codenames are planned, not promised: a release may move to the next row
when its milestone changes. Patch releases (0.3.1) keep their minor's codename.

## Local assistant (unreleased)

Development > Default Assistant always offers an offline, experimental assistant:
Ollama (`ollama`) and `qwen3:4b` (Apache-2.0), downloaded once after one confirmation and run
by the on-demand user service `eitr-ollama.service` on `127.0.0.1` only. Voice
reminders use it with JSON-constrained answers and the same validator; it is never
an assistants-together helper. Remove Local Assistant deletes the service, models
and a package setup installed. Not yet tried on real hardware.

## Repeating reminders (unreleased)

Local daily, weekday, weekly, monthly and yearly reminders retain alert offsets,
end by date or count, and skip elapsed occurrences after one missed notification.
Calendar dots include future occurrences; cancellation can skip one or end a series.
Google/Outlook synchronization still requires account sign-in and remains planned.

## Organization profiles (unreleased)

Reviewed optional-app exclusions, strict checksum-checked stick profiles, installer
review/countdown, `eitr profile check/apply`, root-owned policies and persistent
update exclusions. The Handbook covers the format and root limitation in every
supported language. Offline and online installs, a refused profile, applying to an
installed machine and System Update passed in a VM (`LINUX-VM-TESTING.md`); the
remaining checks are listed in `PROFILE-VM-TESTING.md` and TODO.md.

## Icons fall back to Breeze

Apps use a small per-user icon theme, `eitr-current`, that inherits the theme's
icons and then Breeze and hicolor. Yaru lacks icons such as play, grid view and
back that KDE-style apps ask for, so their buttons showed empty squares.

## Versions

The package version is `<version>.<UTC commit date>.<time>.g<commit>`, for
example `0.3.0.20261014.041148.gb7c94d8`, so every build of a release sorts
after the previous one and the same commit has the same version in any clone.
The PKGBUILD's `epoch=1` keeps these above the earlier date-only versions.

To start a release, change `version`, `stage` and `codename` in
`distro/release.json` in one commit, rebuild the package and the ISO, upload it
(Downloads below), then tag the commit that updates
`website/src/data/download.json` as `v<version>`. Until that commit, the site
still offers the previous ISO; CI accepts that on ordinary commits but not on a
release tag.

## Feature plan

Update now offers only System Update and Update Channel. The redundant Advanced
submenu is removed; `eitr update pacman`, `eitr update aur` and `eitr update full`
remain available in a terminal without automatic snapshots.

AWS account discovery excludes credentials-only profiles and config profiles with
custom endpoints, including S3-compatible storage. Remote diagnostic terminals
remain open until Esc, and failed local status commands show unavailable status.

The website presents keyboard-first desktop, development and system workflows
together. Development has a dedicated hub, and the English offline Handbook is
also available as static, linkable web chapters. Included tools, optional installs
and current hardware/remote-service validation remain separate claims.

Audio and microphone controls share one panel. Tailscale and Streaming panels
show local status beside existing remote-access workflows. Shared controls use
compact sizing, hover-only icon backgrounds, centered loading glyphs and pointer
tooltips. Tailscale account actions request administrator authorization.

Cursor is an optional Developer Apps install. Installed entries in the named
Install lists support Delete with confirmation and preserve settings; managed
language bundles show a full terminal warning. The Pacman/Yay package pickers
remain install-only.

Update terminals show the active package check and snapshot stage; an up-to-date
result stays visible for three seconds. Package installations announce their
safety check before the administrator password, and Flatpak preparation is visible.
Noninteractive waiting steps show a spinning rune and flow with Bifröst rainbow text (theme accent without
truecolour support) and translated Norse phrases, then settle
with a check mark; redirected output and terminal opt-outs keep plain progress lines.

The desktop includes cava under Tools > Music Visualizer and on right-click of
the media equalizer. Its four bars follow live system audio through a private cava
process while visible and playing, with a gentle animation fallback. Theme switches
regenerate its colour gradient while keeping
settings outside the colour section. Existing desktops install cava on first use.

Plugins: Main > Install > Plugins adds a Git repository whose `eitr-plugin.json`
declares Walker rows (shown under Tools > Plugins) and optionally a user service.
Installation shows the author, commit and a trust warning before anything runs;
plugins stay per-user, pinned to the approved commit, and System Update shows each
plugin's changes and asks before updating it. `eitr plugin` does the same from a
terminal; `distro/plugins/example/` is a starting point.

Safer plugins: adding one now takes two confirmations that default to No, a plain
safety page before anything is downloaded and the review after it, which lists
warnings such as a background service or binary files. Every plugin row says whose
code it is and that Eitr has not reviewed it. Updates open with a summary (commits,
changed files with line counts, RISK flags for service and manifest changes,
executables, binaries and new authors); `d` shows the full diff, and a rewritten
history is refused. A blocklist shipped in the signed `eitr-desktop` package stops
known-bad plugins (rows hidden, service disabled, one notification with Remove),
organization profiles can turn plugins off or allow listed repositories, symlinks
are refused anywhere in a plugin, and plugin services get `NoNewPrivileges=yes`.
Report a harmful plugin with the Report a plugin issue form.

pacman shows colour and the Pac-Man progress bar (`Color` and `ILoveCandy`):
new installs write both, and existing desktops get them once with the next
update; removing them by hand afterwards is kept.

Voice reminders: hold SUPER+SHIFT+D and speak, or use Tools > Reminders > Tell the
assistant…. The default assistant only returns a validated instruction (create,
cancel, list or a numbered question in a terminal); Eitr carries it out, and audio
stays local. Reminders take dates ("tomorrow 15:00", "Friday"), appointments alert
an hour before and at the time, and the bar's calendar marks and lists them.

Background menu indexing skips cloud resource pickers, so opening or searching
Walker does not query those services or flood notifications with their failures.
Notification history coalesces bulk removals before rebuilding its cards.

The translated Secure Boot, factory reset and network backend guides retain
all source commands, paths and numbered steps. Interface terminology checks
keep catalogued Handbook controls aligned with their panel or Walker labels.

Capture, desktop bar and Control Center translations now cover recording paths,
all-display bars and the actual Language picker. Handbook checks retain chapter
sections, commands, product names and the newly documented feature details.
The Apps chapter is translated in full, including gaming, dictation and package
review; Steam, GeForce NOW and RetroArch retain their original names.

The translated Devices and Development Handbook chapters now include the full
monitor arrangement, installer keyboard, Monitoring and cloud account workflows.

Translation review: account setup, recovery notices, installer progress and
capture failures now have reviewed pt_BR, es, de and fr helper messages. The
remaining user-facing snapshot, power, network and update messages are also
translated; shared technical terms and developer diagnostics remain English.

Handbook translations track their English source revision; checks flag source
changes even when the localized catalogs have been regenerated.

Ultrawide artwork uses panoramic expansions or proper crops instead of stretched
edge padding. Moss’s
kneeling warrior and Graphite’s reaching hands have corrected hand anatomy; its left hand uses an
owner-approved open pose with five clearly separated digits.
Catppuccin Latte keeps the owner’s revised wallpaper order. The Dark/Light
carousel now shows resting Hati/Sköll with a glowing full moon/sun on black.

Translations: cloud account setup subtitles and menu search use the session
language; Spanish Install and French Development labels are corrected.

The theme collection now contains 15 themes; Moonveil and Obsidian have been
removed at the owner’s request. Its generation prompts remain archived in the artwork batches.
Batch 04 replaces the approved Stillwater, Catppuccin Latte, Rose Pine and
Wisteria wallpapers with fresh written-brief illustrations. Wallpapers have 4K
and ultrawide exports. Afterglow and Moss now also have fresh written-brief
Norse artwork in their owner-requested painterly styles. Girl Coffee also has a fresh
written-brief illustration, a 4K background and an updated lockscreen preview.

Agreed on 2026-10-16 and built in 0.6.x: the firewall, Arch news before updates, the boot guard, the `eitr`
command, user hooks, snapshot diffs and home-folder restores, unattended
installs, Game Mode, display settings, reminders, the calculator, laptop fixes
(experimental until early users confirm them), update channels and offline
dictation. Each ships with tests and Handbook updates. Hardware fixes are written
from what each fix solves, not copied; code taken directly from another project
keeps its copyright notice in a NOTICE file.

The **translations** of menus and the Handbook are reviewed and accepted by the
owner for pt_BR, es, de and fr, including commands, links, key names and
consistent forms of address; early users' reports refine the wording.

The **AI agents** feature is implemented: first-use installation for Claude Code,
Codex, Gemini CLI, Grok Build and GitHub Copilot CLI; a machine-local default
assistant and shortcut; supported light/dark theme settings; and opt-in AI help
from crash notifications. Assistants retain their normal permission prompts.

Translation infrastructure, QML, menus and Handbook catalogs are implemented for
Brazilian Portuguese, Spanish, German and French, with English as source and
fallback. Reviewed helper and installer prompts use one gettext domain.
Unreviewed helper drafts use English; `i18n/pending-helpers.json` lists those
entries explicitly. Complete helper translation review remains open; passing
catalog checks verifies coverage and placeholders, not linguistic approval.

Not planned now: dynamic wallpaper colors, community themes, a separate settings
app, desktop raven tips, browser recoloring, a second compositor, auto-approve agent modes.

## Open work

The current state and the next concrete steps, so anyone (or any AI assistant)
can pick up from the repository alone. Remove items as they ship.

- **Released.** 0.3.0 to 0.6.4, each ISO built in the owner's builder VM (outside
  this repository) and passed the automated VM tests below; the packages are
  published in `[eitr]`. `v0.6.4` and later are tagged.
- **History.** On 2026-10-19 the 707 commits up to 0.6.3 were squashed into one, to
  make the repository smaller: the history held 1.14 GB, mostly retired wallpaper
  art and the PNG wallpapers replaced by JPEGs. Tags `v0.3.0`–`v0.6.2` went with it;
  the owner keeps the old history offline. Later that day third-party
  wallpapers, kept only as references, were removed from every commit too.
  On 2026-10-20 the 69 commits since then were squashed into one again before
  0.6.4, and the `v0.6.3` tag went with them. Ordinary commits continue from here.
- **Downloads.** The ISO is public at `https://download.eitr.info/eitr-<version>.iso`
  with its `.sha256` beside it (Cloudflare R2 bucket `eitr-downloads`, free tier
  up to 10 GB, no bandwidth charges). The website's button reads
  `website/src/data/download.json`. The bucket holds **one ISO at a time**, so it
  never pays for extra storage. For each release:
  1. Delete the previous ISO and its `.sha256` from the bucket
     (`aws s3 rm ... --profile eitr-r2` with R2's endpoint; list first, check
     the names, and delete nothing else).
  2. Upload the new ISO and checksum with an S3 multipart upload (the dashboard
     and Wrangler stop near 300 MB).
  3. Download it back through the public address and compare the checksum.
  4. Update `download.json`; `distro/tests/test_website_download.py` fails until
     it names the current release.

  Between steps 1 and 3 the website's button has no file to serve, so do the
  steps back to back; a short 404 is accepted rather than paying for storage.
  Only if the ISO shrinks to about 4 GB (two of them fit the free 10 GB) may the
  owner choose to upload before deleting instead.
- **Real hardware.** The owner's desktop (Intel, NVIDIA, dual monitor) runs
  Eitr installed from the 0.3.0 ISO and stays current through `[eitr]` with
  System Update; Git Accounts and Cloud accounts were set up through their menus
  there. It is the real-hardware install for each release.
- **Publishing a release.** `distro/repo/release-desktop.py` rebuilds and
  publishes `eitr-desktop` (and `eitr-artwork` when the artwork changed) from the
  pushed HEAD to Cloudflare R2 (`distro/REPOSITORY.md`).
- **Hardware we do not have (0.7.0).** Windows/BitLocker dual boot is verified
  only in a VM with a fake Windows disk; laptop-only features (battery limit,
  power profiles) and other GPUs need early users' machines.
- **GPL sources.** Each payload build writes the source archives of the AUR and
  local packages it built (`--sources`, `distro/README.md`). The owner keeps
  every release's set offline, outside Cloudflare, for at least three years:
  `NOTICE.md` promises them on request.
- **Release tests.** For every release, after bumping `distro/release.json` and
  publishing: install the previous release's ISO and System Update it to the
  new package, then install the new ISO and run verify, both factory resets and the boot guard
  (`distro/vm-tests/eitr-vm-test`, `distro/LINUX-VM-TESTING.md`). LUKS installs
  need a person to type the passphrase at boot, so they stay a manual test.
- **Smaller packages, if artwork changes become frequent.** Wallpapers ship as
  JPEG, testing takes `eitr-artwork` from stable, and login images are stored
  once (0.6.3). The next step, only if needed: split `eitr-artwork` per theme so
  changing one theme republishes a few MB instead of the whole set.
- **Sponsorship.** GitHub Sponsors is live (`github.com/sponsors/erickbatistaprado`):
  the repository's Sponsor button reads `.github/FUNDING.yml`, and the website
  has a Support section and footer link.
- **Website and email (eitr.info).** The owner owns `eitr.info`. Its DNS, the
  website (a Cloudflare Worker serving the built site, `website/README.md`),
  `reports@eitr.info` for problem reports and `contact@eitr.info` for everything
  else (Cloudflare Email Routing, forwarding to the owner's inbox; the catch-all
  is off) run on Cloudflare's
  free plan; nothing costs money beyond the domain.
- **Publishing checklist.** `PUBLISHING.md` lists what remains: splitting the
  personal overlay from the distro.
