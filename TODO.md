# Plan

Open work in priority order. Each item lists what decides the next step.
Remove an item when it ships; `distro/RELEASES.md` tracks releases.

1. Assistants working together
2. Remote access: Moonlight, Sunshine and Tailscale
3. Smaller items: OBS and the main display, menu translations, AI Usage
4. Waiting on the owner: personal overlay split, testing channel
5. Later: AI multi-account, plugins, smaller artwork packages, screenshots
6. Before 1.0.0: skipped-release upgrade, encrypted install, other hardware

# 1. Assistants working together

Any installed, signed-in assistant can hand a task to another one, for people
or companies paying for several subscriptions.

Design:

- One Eitr MCP server ("assistants") offers `ask_claude`, `ask_codex`,
  `ask_gemini`, `ask_copilot` and `ask_grok`, only for assistants that are
  installed and signed in. Each tool runs that assistant's non-interactive mode
  with a timeout and returns its answer.
- One switch, AI > "Let assistants work together", off by default. Turning it
  on shows a confirmation naming the connected assistants and warning that each
  hand-off uses that assistant's subscription and counts toward its limits.
  Turning it off removes everything it added.
- The calling assistant asks the user before each hand-off (its normal tool
  approval); nothing is pre-approved and no auto-approve mode is used.
- Helpers only read: review, explain, suggest. Edits stay with the assistant
  the user is talking to.
- One hop: a helper cannot call another helper (a depth counter in the
  environment).
- A notification shows "Claude asked Codex" while a helper works.
- Registering the server adds one entry to each assistant's own settings and
  leaves every other setting untouched, written atomically like the theme sync.

Steps:

1. Verify each tool's read-only non-interactive mode and MCP settings on the
   installed version (`--help` and its docs):
   - Codex: `codex exec --sandbox read-only`; MCP in `~/.codex/config.toml`.
   - Claude Code: `claude -p` in plan mode or with read-only tools; MCP in
     `~/.claude.json`.
   - Gemini CLI: `gemini -p` with `--approval-mode plan`; MCP in
     `~/.gemini/settings.json` (`mcpServers`). Confirm plan mode blocks writes
     in headless runs.
   - Copilot CLI: `copilot -p` needs tools pre-approved, so allow only read
     tools and `--deny-tool` writes and shell; MCP in
     `~/.copilot/mcp-config.json`.
   - Grok Build: `grok -p` is documented; read-only and MCP support are not
     officially documented yet. Leave Grok out until they are.
   A tool that cannot run read-only is not offered as a helper.
2. Build the server and the switch for Claude and Codex; unit tests with mocked
   CLIs, settings round-trip tests, the depth limit and timeouts.
3. Test end to end with the owner's Claude and Codex (each hand-off uses a
   little of their limits), then add Gemini and Copilot as each one checks out.
4. Handbook chapter (all languages), menu translations, Learn entry.

# 2. Remote access: Moonlight, Sunshine and Tailscale

First milestone: control the owner's signed-in, awake Eitr desktop (apps and
games) from a MacBook. Install everything on first use, like GeForce NOW; the
ISO does not grow. All three are open source from their usual sources.

Stage 1, Moonlight (client):

- Gaming > Moonlight next to Steam and GeForce NOW: first click installs it,
  later clicks open it. Also listed as "Connect to another PC" under
  System > Connectivity > Remote Access.

Stage 2, Sunshine on the home network (host):

- System > Connectivity > Remote Access > Share this PC: set up, start or stop
  sharing, open settings, pair a device, optionally start at login (a user
  service). Hosting stays off until enabled; existing installations and
  settings are kept.
- The first enable warns that sharing hands over full control of the desktop
  and makes the user set Sunshine's password. Its web settings listen only on
  this PC.
- Firewall: Eitr's firewall is on from the first boot, so sharing opens TCP
  47984, 47989, 47990 and 48010 and UDP 47998-48000 only for the home network
  and the Tailscale interface; stopping sharing closes them. Never suggest
  router port forwarding.
- Virtual keyboard, mouse and controller input (uinput) and any capture
  permission Sunshine needs on Wayland with NVIDIA are system changes: one
  confirmed setup step through the root helper, with an undo.
- Test with the owner on the local network first: Hyprland capture, keyboard,
  mouse, audio, controller, both monitors, and behaviour while locked.

Stage 3, Tailscale (away from home):

- Remote Access > Access away from home: install, enable the system service
  (confirmed, like the network backend switch), set the user as operator so
  later actions need no sudo, sign in through the browser, show status and this
  PC's address, connect or disconnect.
- Show whether the connection is direct or relayed (from Tailscale's own
  status) to explain poor performance.
- Handbook guide: Sunshine on Eitr, Moonlight on the Mac, then Tailscale on
  both. Translate menus and messages; test installs, service controls,
  signed-out states and failures.

Afterwards, each tested separately: headless use, access before login, wake on
LAN.

# 3. Smaller items

- **OBS and the main display.** The screen-share permission keeps the first
  monitor picked, so OBS does not follow the bar's main display. Ship a shared
  `xdph.conf` default with `allow_token_by_default = true` (an existing user
  file is kept) so the share prompt remembers its choice after the first time,
  and say in the Handbook that OBS asks once which screen to record. Do not
  replace the share picker: it serves every app, not only OBS. Verify with both
  monitors.
- **Menu translations, final read.** The last 1.0 item in `distro/RELEASES.md`:
  an editorial pass over menu wording in all four languages (whole sentences,
  consistent terms, same register as the Handbook), then the owner uses
  Portuguese daily and reports anything odd. Native speakers among early users
  review Spanish, German and French.
- **AI Usage for Copilot and Gemini.** Not added: Copilot's official endpoint
  reports only requests used (no allowance, personal plans only, separate
  token) and Gemini has no official quota source. Check again when either
  publishes real limits.

# 4. Waiting on the owner

- **Personal overlay split** (`PUBLISHING.md`). Once the owner creates the
  private repository: move `HOME_FILES/.zshrc` and `owner/cooler-display` there
  with their install notes, update `distro/layout-manifest.json` and the
  manifests that list them, keep the distro's own `.zshrc` default, check the
  box in `PUBLISHING.md`.
- **Testing channel.** Built and verified. When the owner says so, publish with
  `release-desktop.py --channel testing`, try it on the owner's PC, then
  `--promote` to stable.

# 5. Later

- **AI multi-account.** Several accounts per assistant, manual switching only.
  Each account gets its own config folder selected through the tool's own
  variable (`CLAUDE_CONFIG_DIR`, `CODEX_HOME`); sign-in for an extra account
  uses a private browser window; never log out of an account to add another.
  AI Usage shows each account. Pairs with item 1 for teams with several seats.
- **Eitr plugins.** A plugin is a Git repository with a manifest declaring its
  Walker rows, scripts and optional user service. Install > Plugins takes a
  URL, shows who wrote it and a trust warning before any code runs, updates
  with System Update and removes cleanly. `cooler-display` becomes the first
  plugin, in the owner's repository.
- **Smaller artwork packages.** Only if artwork changes become frequent: split
  `eitr-artwork` per theme so one theme's change republishes a few MB.
- **Screenshots.** Retake the 8 theme previews made before the btop colour
  change; add website shots of the lockscreen, the dictation waveform and the
  Packages picker (owner-only captures, taken when the owner says).

# 6. Before 1.0.0

- **Upgrade that skips releases.** 1.0 promises supported upgrades, so test
  installing 0.6.4 and updating straight to the 1.0 candidate. The 0.6.4 ISO is
  kept locally for this test only, then deleted.
- **Encrypted install.** Install with LUKS in a VM by hand (the passphrase is
  typed at boot), then verify, update, both factory resets and the boot guard.
- **Hardware we do not have** (0.7.0): laptops, AMD and Intel graphics, a real
  Windows/BitLocker dual boot. Fixes come from early users' reports and do not
  hold back other work.

Not planned: auto-approve agent modes and the rest of the "Not planned now"
list in `distro/RELEASES.md`.
