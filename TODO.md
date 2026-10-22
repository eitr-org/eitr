# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Remote access: test with the owner
2. Organization profiles
3. Smaller items
4. Google's assistants: Antigravity
5. Later
6. Before 1.0.0

# 1. Remote access: test with the owner

Moonlight, Sunshine and Tailscale are built and inactive until set up.
Fresh installs include them; existing machines install missing apps on demand
(`distro/REMOTE-ACCESS.md`). With the owner and a MacBook, in this order:

1. Home network, tested 2026-10-21 on the owner's PC (one monitor) with Moonlight
   on a MacBook: setup, start sharing, pairing by IP, video with no noticeable
   delay, keyboard, mouse, audio, the lockscreen (unlocked from the Mac), start
   at login and Stop Sharing all work. Still to check: two monitors, Restore
   Sharing Setup. Controllers are not needed.
2. Away from home works (2026-10-21): Tailscale setup, sign-in and connect on the
   owner's PC, and the Mac reached the PC through it.
3. Fix what the tests find; only then call remote access ready in the Handbook
   and on the website.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 2. Organization profiles — VM verification pending

Parser, reviewed allowlist, installer/CLI integration, policies, update exclusions,
VM harness and translated documentation are implemented in the working tree.
Do not call this shipped until the maintainer runs the VM checks in
`distro/PROFILE-VM-TESTING.md`:

1. Offline install with removals and checksum-verified stick package files.
2. Online install with Flathub additions.
3. Refused profile leaves the target disk unchanged.
4. System Update does not bring excluded apps back.
5. Remote Access policy hides menus and bar entries and refuses direct tools.
6. Applying a profile to an installed machine, including typed cancellation,
   successful application, defaults, root-owned policy files and setup run-once.
7. Profile-only wizard Review and all online additions/default repository paths.

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
- **Website evidence and screenshots.** Keep the new public information pages in
  step with verified desktop behavior. Add lockscreen, dictation waveform and
  Packages picker shots, taken when the owner says. Describe remote access as
  verified only after the real-device tests above pass.
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

# 4. Google's assistants: Antigravity

Gemini CLI is verified as an assistants-together helper with a free API key:
a direct read-only question and an MCP `ask_gemini` call both answered.

Antigravity (`agy`) stays out as a helper: headless runs auto-deny even reading.
The only unlocks are `--dangerously-skip-permissions` or global permission rules
in `~/.gemini/antigravity-cli/settings.json`. Re-check when it gains per-run
permissions or a read-only headless mode. Do not weaken global permissions.

# 5. Later

- **Voice reminders, next steps.** Syncing with Google or Outlook Calendar (needs account sign-in).
- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Useful for teams with several seats.
- **Local assistant for voice reminders.** An optional offline model through
  Ollama (a 3B model such as Qwen 2.5 or Llama 3.2, 2-3 GB once) offered next to
  the other assistants, with its answer constrained to the reminder JSON format and
  checked by the same validator. Nothing leaves the PC; weaker on unusual phrasing.

# 6. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
