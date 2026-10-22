# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Organization profiles
3. Smaller items
4. Later
5. Before 1.0.0

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

# 2. Organization profiles: remaining checks

Built and VM-tested on 2026-10-22 (`distro/LINUX-VM-TESTING.md`): offline install
with removals, a checksummed stick package and policies; online install with a
Flathub app (installed at first boot); a refused profile leaving the disk
untouched; `eitr profile apply` on an installed machine; System Update keeping
the profile. Still to check, in a VM or with the owner:

1. An update that really upgrades packages does not bring an excluded app back.
2. Remote Access, assistants and update-channel controls hidden on screen (bar
   in both orientations, menus, search) with the policies on.
3. `eitr profile apply`: a mistyped confirmation changes nothing; defaults
   (theme, wallpaper, browser, extra signed repository) after the next login;
   a setup script runs once.
4. The profile-only wizard Review and the unattended countdown, in each language.

# 3. Smaller items

- **The first real plugin: switch over with the owner.** The private
  `eitr-personal` repository is now a plugin (`personal-tools`: the cooler display's
  service and a Cooler Display Status row), fetched and validated over SSH. With
  the owner: add the udev rule once, install it from Install > Plugins, retire the
  `install.sh` copy (its README lists the commands) and check the display.
- **ISO download counter.** Cloudflare's R2 analytics only keep a few weeks and
  cannot tell our own checks from real downloads. Put a small Worker in front of
  the ISO link that counts new downloads (not resumed ranges) in D1 without
  storing IPs, and show the total on the website.
- **Website translations.** Offer the site in the desktop's languages
  (Portuguese (Brazil), Spanish, German, French) with a language switch, reusing
  the reviewed Handbook translations where chapters overlap. Decide the URL scheme
  (`/pt-br/...`), `hreflang` and sitemap entries first; keep English the default
  and keep untranslated pages falling back to English.
- **Website evidence and screenshots.** Keep the public pages in step with verified
  desktop behavior. A feature gets a screenshot when it has a screen people look
  for (a panel, menu or wizard) shown on the website or in the Handbook;
  background behavior gets none. Missing: the lockscreen and the Packages picker.
  Describe remote access as verified only after the real-device tests above pass.
- **Search indexing and measurement.** The owner verifies eitr.info in Google
  Search Console and Bing Webmaster Tools, submits the sitemap and inspects
  public-page indexing. Track impressions, queries and clicks there without
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
  than promotional claims. Update the public repository description/README with
  consistent Eitr Linux positioning. Consider a dated, source-checked Omarchy
  comparison page separately; do not imply shared features are exclusive.

# 4. Later

- **Your own theme, lockscreen and wallpaper.** Let a person create and use their
  own, kept only on their machine (never uploaded or shared by Eitr): a theme
  from a picked wallpaper or chosen colors (bar, terminal, launcher, apps and
  icons follow, like the shipped themes), their own images as wallpapers in the
  Walker picker and carousel, and a lockscreen based on an existing design with
  their own picture, colors and text. Stored under the user's config, listed
  beside the shipped ones and removable; updates never overwrite them. Decide the
  creation flow (Walker wizard with a live preview) with the owner first.
- **Voice reminders, next steps.** Syncing with Google or Outlook Calendar (needs account sign-in).
- **Antigravity as a helper.** Recheck when its command-line tool gains per-run
  permissions or a read-only headless mode; until then it stays a standalone
  assistant. Nothing to do before that.
- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Useful for teams with several seats.

# 5. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
