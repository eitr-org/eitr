# Repository Conventions

This repository backs up Eitr, a customized Arch Linux desktop. Preserve the
existing design and workflows rather than replacing them with upstream defaults.

## Engineering Practices

- New wallpapers and website illustrations follow `branding/ART-DIRECTION.md`:
  clearly drawn Norse fantasy, bold ink contours, flat limited colors, black
  negative space and varied compositions. Crowns and knotwork are optional,
  never a template for every image. Avoid realistic rendering and
  scenic backdrops unless the owner explicitly requests them.

- Keep the EITR Handbook current whenever changing documented shortcuts, menus,
  panels, preferences, installers, security/recovery procedures or limitations.
  Update the relevant Markdown chapters and privacy-safe screenshots, then run
  `python3 quickshell/desktop-bar/scripts/handbook-build.py` and its `--check`.
  The catalog bundles canonical distro guides rather than duplicating them;
  keyboard/mouse tables are generated from Learn's shortcut/gesture sources. Secure Boot docs
  belong only in the Handbook, without a separate Learn or Security menu entry.
  The reader is an offline, read-only overlay: never
  execute commands from document links or include secrets/private screen content.
  It closes only from its close button, Escape or its shortcut, never from a click
  beside it. Its Getting Started chapter is the first-login welcome; its setup
  buttons are reader controls that open existing panels, not document links.

- Keep the docs in step, proportionately: a change updates what directly
  describes it (the nearby comments, its menu text or messages, the Handbook or
  README section about it, and the `TODO.md` or `distro/RELEASES.md` item it
  finishes) in the same commit. Only when something is renamed, moved or removed,
  also search the repository once for its old name and fix those mentions. Full
  documentation sweeps are occasional check-ups, not part of every change.

- Keep code comments and repository guidance focused on current behavior and
  relevant design constraints. Remove stale comments, change narratives, and
  historical notes that no longer apply; Git history records ordinary changes.
  Preserve history only when it is essential to understanding a current safety,
  compatibility, or design decision. Put that context in a dedicated document
  and, when needed, link to it from a brief current-behavior comment instead of
  keeping the historical explanation inline.

- Keep folders and filenames organized and descriptive. Promote selected artwork
  out of concept folders and replace draft identifiers such as `05b-rune-liquid`
  with stable Eitr asset names. Store branding sources, vector masters, and sized
  exports in clearly separated directories; update every consumer when renaming.
  Keep export scripts with their assets so formats and sizes can be regenerated.

- Keep changes small and cohesive. Read neighboring code before adding a new
  component or helper; reuse existing patterns and shared style APIs.
- Avoid duplicated behavior and duplicated theme constants. Put reusable
  logic in one owner module and update its callers, but do not create an
  abstraction merely to eliminate a few clear lines.
- Prefer descriptive names, simple control flow, explicit errors, and data
  formats with real parsers. Avoid hidden side effects and hardcoded user paths.
- Keep generated files and their generators synchronized. Validate both the
  immediate result and what a later theme change or reboot will regenerate.
- Add focused tests for new behavior and regressions; run syntax/lint checks
  for every edited script. Do not claim untested hardware behavior as verified.
- Keep external packages and installers in `distro/` manifests rather than
  scattering installation commands across unrelated desktop scripts. Package
  lists should distinguish official, AUR, and hardware-specific dependencies.
- Reviewed local packages belong in `distro/local-packages.txt` and `distro/pkg/`.
  Keep online installation, offline payload building and guided-install transactions
  in sync. Pin third-party binaries and checksums; never replace cmux TUI with the
  unrelated AUR serial-debugging package or run its per-user installer at first login.
- Fresh-install code must not assume a particular username, monitor, GPU,
  locale, account, or disk layout. Never bundle secrets or migrate live caches.
- Do not overwrite existing user configs or start/restart services during a
  repository audit. Installer actions belong on a new target system only.

## Working With Live Configs

- Commit identity: the owner's checkout keeps `core.hooksPath=.githooks`. The
  hooks read the required identity, the allowed push remote and forbidden
  identities from local Git config (`eitr.guard.*`), never from this repository.
  Check BOTH author and committer identities before committing, never bypass the
  guard, and never change global Git identity or global CLI logins. The owner's
  own identity and account rules live in their local agent instructions.
  Never add `Co-Authored-By` trailers, AI/agent attribution, or another author
  (including Claude, Codex, Anthropic, or OpenAI). Keep the commit-message
  attribution guard enabled.

- On the owner's machine, the active configuration is under `$HOME/.config`.
  Read the live files and repository versions before editing: either may contain
  newer user changes. Never restore the backup over live configs indiscriminately.
- For requested desktop changes, update the relevant live files, verify them,
  then sync the matching files into this repository. On other machines, do not
  assume this layout is installed or modify the desktop without authorization.
- Shipped desktop code runs from `/usr/share/eitr`, installed by `eitr-desktop`
  (see `distro/CONFIG-LAYOUT.md`); `~/.config` holds preferences, generated output,
  tiny loaders and deliberate overrides under `eitr/overrides`. Classify every new
  file in `distro/layout-manifest.json`. A home that has not run
  `eitr-config adopt-layout` still runs its old copied code; check
  `$XDG_STATE_HOME/eitr/layout.json` before assuming either layout. On an adopted
  machine, mirror code changes by updating the package, not by copying into
  `~/.config`; pass `--repo CHECKOUT` to `eitr-shell` or `eitr-run` to try a checkout.
- Repository directories generally mirror the shipped tree. `HOME_FILES` contains
  files belonging elsewhere under `$HOME`; preserve relative symlinks and permissions.
  `owner/` holds tools for the owner's own hardware (such as `owner/cooler-display`);
  it is backed up here but never packaged or installed on other machines.
- Keep unrelated user changes. Do not commit credentials, tokens, clipboard data,
  generated QR codes, logs, caches, or Python bytecode.
- The owner's standing preference is to sync, commit, and push completed changes.
  Review the diff and status first; report failures rather than claiming success.
  Never force-push or reset unrelated work.
- Treat new messages as steering ongoing work. Handle added requests and then
  resume outstanding tasks; stop or abandon a task only when the owner explicitly
  asks to stop or replaces it with an incompatible request.

## Desktop Architecture

- Hyprland configuration uses Lua in `hypr/hyprland.lua`; follow its existing APIs.
- The active bar and native popups are in `quickshell/desktop-bar`.
  Use local scripts from that directory, not legacy Waybar or Wofi helpers.
- Walker is the launcher; Elephant supplies its menus. Update all relevant
  shortcut and Learn/Shortcuts entry points when changing a workflow.
- Start Elephant through its single systemd user service, not a second raw
  autostart process. Keep `KillMode=process`: custom menu commands inherit the
  backend's cgroup, and restarting it must not kill launched apps or terminals.
  Detached sessions alone do not isolate systemd cgroups; native provider launch
  prefixes do not cover custom menu actions.
- SUPER+Space and Main > Apps must share the custom `menus:apps` provider,
  including Enter/Open, Delete/Uninstall with confirmation, and back navigation.
  The owner retired the separate native Apps/pin workflow. Global search launches
  apps without uninstall actions; keep uninstall scoped to the Apps menu.
  Existing desktops must not require distro snapshot setup just to update;
  fresh distro installs snapshot only the System Update workflow. Advanced
  Pacman/AUR updates intentionally do not create automatic snapshots.
- Keep Walker menus organized: group related setup/actions into named submenus.
  List submenus first, like folders, then the rows that open something, each
  group sorted alphabetically (case-insensitive). Main retains its custom order,
  and Apps retains its existing behavior.
  instead of crowding their parent. Set each submenu's parent to its actual
  location so Shift+Backspace returns correctly. A menu with submenus is a Lua
  menu on `elephant/scoped-menu.lua` with its rows in `elephant/menu-rows/<name>.json`,
  so typing in it searches everything below it. Menus share one row layout
  (copy item_menus-main.xml to item_menus-<name>.xml for a new menu): the
  description sits below the title, and rows in the "submenu" state show a
  right-aligned ">" marker. Submenu rows keep `subtext = ">"` in their data,
  which scoped-menu.lua and the search index turn into that state; they carry
  no description. Every other row has a short description of what it opens or
  does. In menus that pick one option (theme, wallpaper, lockscreen, fonts,
  corners, update channel, bar settings) the current choice, and installed apps
  in Install lists, use the check icon with the "current" state; write the icon
  as `"\u{F00C}"` in TOML, JSON and Python so editors cannot drop the glyph, but
  as `"\239\128\140"` in Lua: Elephant's Lua 5.1 has no `\u{}` escape and would
  send the text `u{F00C}`, which Walker draws as a missing icon. Use
  `elephant/choice-entries.lua` for small fixed choices.
- Walker system actions should open the same native panels as bar clicks. Use
  the existing `panels` IPC interface, including `call -- panels show <kind>`.
- System groups Connectivity, Devices & Input, Information and Maintenance;
  Security and Dotfiles remain directly under System. Calendar and Workspace
  Overview remain searchable through the hidden system-shortcuts provider and
  accessible from the bar, without adding rows to System.
- Existing cloud CLI configurations belong to the owner and may hold work
  accounts. Never run commands against, edit, reformat or write to a profile,
  account or config file (`~/.aws/config`, `~/.aws/credentials`, gcloud or Azure
  config, SSO caches) that the current task did not create, including
  `aws configure set`. Use the project's own credentials (such as Cloudflare R2)
  only through the profile the owner named for them, with the profile and
  endpoint explicit on every command; never print keys, and ask before anything
  that could reach another account.
- Cloud tools select an explicit provider context before resource queries.
  Git Accounts use a confirmed managed Git include, default identity and
  narrow-to-specific folder rules; repository settings win. Keep SSH keys,
  provider CLI profiles and backups private and outside the repository. Never
  change existing remotes, global CLI logins or credential helpers during setup.
  Keep Google configuration/account/project and Azure tenant/subscription visible,
  preserve selections across terminal returns, and never switch global CLI defaults
  just to navigate menus. Friendly environment labels are machine-local, not inferred.
- Walker installation/update/setup terminals use `task-terminal.py` to show
  the EITR banner in the current theme accent. Successful tasks close automatically;
  failed tasks keep their output visible until dismissed. Do not add this banner
  to ordinary interactive terminals or About. Keep informational viewers open
  long enough to read their output.
  Status/guide terminals also show that banner but stay open for reading. Cloud
  tasks print it after their initial clear via `--banner-only`, keeping their
  provider-specific return behavior. Ordinary terminals and About remain unbranded.
  Cursor settings live in machine-local `eitr/cursor.json`: retain the family,
  size and explicit color override across theme switches. Auto follows the
  theme's light.mode marker; generated cursor-env.conf must not be committed.
- Use `walker/bin/walker` for Walker launches. It carries an application-scoped
  GTK workaround required for compositor blur; do not bypass it casually.
- WiFi defaults to iwd and supports an explicit reboot-only NetworkManager choice
  through the root-owned Eitr network helper. Keep live connections untouched when
  saving a backend, preserve both sets of profiles, and require CA/server validation
  for enterprise WiFi. Audio uses PipeWire, Bluetooth uses the native Quickshell service,
  and Quickshell's NotificationServer handles notifications. Do not substitute
  backends without agreement. Notification cards and the center follow the same
  shared panel styles and the bar's current color/transparency setting.
- The custom lockscreen and SDDM login themes have separate responsibilities.
  Keep the `hyprlock` PAM dependency and existing idle/suspend timings intact.

## Visual And Interaction Patterns

- Read `quickshell/desktop-bar/PanelStyle.js` and its README before styling panels.
  Use the shared font, text roles, padding, and corner radii. Utility headings are
  16 px, body/control text 13 px, and captions 11-12 px. Calendar dates, weather
  temperatures, and glyphs have intentional size exceptions.
- Panel surfaces follow the bar's selected theme color or transparency with
  blur. Maintain both light and dark theme support; do not reintroduce the
  no-color appearance option.
- Keyboard layout lists share `KeyboardLayoutRow` in the keyboard popup and
  Control Center: follow WiFi's foreground-tinted selected/hover rows, with
  action icons inset inside the row and vertically centered.
- Selectable device/layout rows and Control Center tiles follow WiFi's shared
  `PanelStyle.selectionAlpha` and `selectionBorderWidth` pattern: selected rows
  have a foreground-tinted fill without an outline; inactive rows have a subtle
  foreground border and hover fill. Keep action buttons inside their row,
  vertically centered, without changing the behavior of unrelated action buttons.
  Use the shared WiFi row metrics: 44 px height, 6 px row gap, 10 px leading
  inset, 36 px text inset, 2 px title/detail gap, and 32×30 px action buttons
  with 8 px inset/spacing. Keep two-line labels vertically centered.
- Use subtle foreground-colored dividers and existing `PanelButton`,
  `PanelSwitch`, `BarTooltip`, and `ThemedPopup` components where appropriate.
  Keep hover tooltips short and theme-aware; do not introduce bar hover fills.
- Keep rounded corners, centered icons, consistent gaps, and stable dimensions.
  Corner choices (Square, Rounded, Extra Rounded) use the shared DesktopStyle
  preference for Eitr surfaces, Walker and compositor window decorations; theme
  regeneration and reloads must preserve it. Keep circular status dots and slider
  thumbs circular. Notifications get a subtle inward-only glow (no hard outline
  or exterior shadow): the theme accent for normal urgency, the theme's color1
  for critical, none for subdued low-priority cards, in history and popups.
  Changing values must not shift bar items. Match icon sizes visually, not just
  by font size, since glyph shapes differ.
- The date/time stays exactly screen-centered regardless of neighboring items.
  The Main display switch in a monitor's Display panel settings selects the bar's
  primary screen and saves it in the machine-local `hypr/primary-display` file. If the chosen display is
  disconnected, fall back to an available one. Until a choice is saved, use the
  first connected output in the machine-local `hypr/preferred-outputs`, else the
  largest active display. Do not commit primary-display or preferred-outputs.
- Shared `hypr/hyprland.lua` stays generic: automatic monitor layout and no
  connector names, input device names, or other machine-specific settings.
  Those belong in the Git-ignored `~/.config/hypr/local.lua`, loaded last and
  error-guarded; the owner's layout is kept in `hypr/local.lua.example` and
  `hypr/preferred-outputs.example`. Update the examples, not the shared file,
  when the owner's hardware changes.
- Hardware and AI Usage icons sit after the workspaces and open on the left;
  calendar/weather open centered; other controls open on the right. Panels
  share the bar's Wayland surface and attach directly to its actual edge with
  inward-curved corners and continuous blur. Unfold them inward on opening and
  fold them back on dismissal. Keep content padded inside the curved surface.
  Hardware uses one icon, with CPU/GPU/RAM and only the root-drive Storage data
  inside the popup. Growing content must stay within the usable screen.
- Empty-bar double-left-click toggles transparency, double-right-click toggles
  full/centered hover layouts, and left drag changes the screen edge. These settings
  persist in `bar-settings.json` and also appear under Style > Desktop Bar.
  Centered mode shows only the clock until hovered or pinned. Expansion preserves
  icon order and the clock's exact screen center on all four edges; pin sits
  between media and clock. Keep it expanded during panel use/dragging. Its panels
  use detached rounded surfaces beside the bar, centered along its axis, with
  the live Hyprland inter-window gap and existing 320 ms reveal. Full-bar panels
  keep their connected surfaces. Gaps must pass clicks through.
- Panels close on outside click or Escape, not merely when the pointer leaves.
  Use the shared DockPanel and PanelSurface components for bar controls.
  Full-bar panel backgrounds stay attached to the bar with fluid concave joins.
  Twice Hyprland's outer gaps inset the content on all four sides, not the attached
  surface. Do not align glyph centers at the expense of button backgrounds or
  add duplicate per-panel padding above the shared content frame.
- Keep the right-side icon group hidden by default, with its manual toggle and
  no auto-close timer. Preserve the existing arrow direction and icon order.
- Keep calendar height fixed with six week rows. Weather city choices are
  session-only; the city close button restores the default geolocation.
- Media is hidden when no eligible player exists; meetings are excluded. Keep
  its compact controls and song-name tooltip on the animated equalizer.
- WiFi separates Connected, Known Networks, and Other Networks. Saved offline
  networks remain listed. Do not show fake signal percentages for offline rows.
- Workspace style examples must match the actual bar markers. Start with five
  numbered workspaces; expand sequentially through the current or highest occupied
  workspace, capped at ten. Remove extra empty markers after leaving them.
  Preserve dual-monitor assignments. The Overview icon precedes
  the workspace markers and shows only occupied numbered workspaces, using
  in-memory previews with no saved screenshots. Keep equal left-group spacing
  and centered icon/marker alignment on all bar edges. Right-side controls use
  the same icon-slot dimensions and spacing as the left group.
  Overview always uses a theme-tinted blurred background, independent of bar
  appearance. Stagger preview entrances in workspace order, finishing within
  one second; all Overview dismissal paths must be instant, with no closing effect.
- Wallpaper/theme changes should not emit success notifications. Preserve both
  Walker selection and the desktop carousel workflows.
- Theme-generator changes must accompany edits to generated styles so the next
  theme switch does not undo the fix. Use portable names and `$HOME` paths, not
  personal names or upstream branding for new components.

## Safety And Verification

- Factory reset means restoring the complete first-login system, settings and
  user data. Require two separate destructive-action warnings and a typed
  confirmation; never perform it on the running root/home filesystems. Keep
  the read-only baseline outside ordinary Snapper lists and cleanup, and verify
  coordinated system/home/boot recovery in an isolated VM before enabling it.
  Do not claim snapshots are undeletable by root or that installation works
  offline until the complete package payload has passed disconnected testing.

- Never test by disconnecting WiFi/Bluetooth, changing audio devices or levels,
  starting/stopping recordings or streams, locking, suspending, or logging out.
  Use read-only queries and mocks; ask before exercising disruptive actions.
- Never restart SDDM during a session. The owner permits Elephant restarts without
  asking; verify its `KillMode=process` protection before restarting it. Ask before
  restarting other services that could disrupt work, unless permission was given
  for the current task. Prefer Quickshell auto-reload and config-only Hyprland reload.
- Boot, disk, LUKS/TPM, Secure Boot and PAM changes stay explicit `eitr-system`
  actions behind typed confirmation, with backups or a documented undo. The
  installer may only offer them (`distro/bootloader/setup.sh --offer`); never
  automate sbctl key enrollment, initramfs `HOOKS` edits or `limine-update`.
  systemd-boot snapshot booting is unsupported. Laptop-only features (power
  profiles, battery limit) must stay hidden or refused without a system battery.
- Do not uninstall packages, delete configs, or weaken credential permissions
  without explicit authorization. Keep WiFi QR secrets out of files and argv.
- Inspect screenshots for clipping, alignment, and theme consistency without
  publishing private screen content. Close any test menus afterward.
- `bash tools/check.sh` runs every repository check (CI runs the same script;
  `--list` shows stages to run individually). Run focused checks appropriate
  to the change, for example:

```sh
/usr/lib/qt6/bin/qmllint --silent quickshell/desktop-bar/ChangedComponent.qml
python3 -m unittest discover -s quickshell/desktop-bar/tests
python3 -m unittest discover -s walker/tests
node quickshell/desktop-bar/tests/test_media_model.js
luac -p hypr/hyprland.lua
bash -n path/to/changed-script.sh
hyprctl configerrors
git diff --check
```

`hyprctl` checks require the live session. Use the Qt 6 linter, not the older
`qmllint` on PATH. Do not claim unperformed tests or end with a push still running.

## Recurring Review Findings

Check these before committing; reviews keep catching them.

- A new QML file under `quickshell/desktop-bar` must be listed in its `qmldir`,
  or the running bar cannot find it even though `qmllint` passes.
- Lists repeated across files change together: workspace styles (QML menus,
  Elephant, both scripts, tests) and lockscreen designs (settings `NAMES`,
  gallery, README count, Handbook, tests). Keep style lists alphabetical.
- After editing `handbook/content/*.md`, rebuild `catalog.json` with
  `handbook-build.py`; `--check` fails otherwise.
- A new folder inside a theme needs `test_theme_schema.py`, the `eitr-artwork`
  glob and the `eitr-desktop` removal line. Renaming or deleting wallpapers also
  updates `artwork.md`, `references/*.json`, `distro/artwork.json` patterns,
  `branding/ART-DIRECTION.md` and `website/scripts/sync-art.mjs`.
- Run tests through `bash tools/check.sh`. The desktop session exports
  `XDG_CONFIG_HOME`/`XDG_CACHE_HOME`, which win over a patched `Path.home()`, so a
  direct run can write fixtures into the owner's real home (a saved wallpaper
  pointing at a deleted temporary image is a black desktop at the next login).
  Test modules that patch `Path.home()` import `setUpModule` and
  `tearDownModule` from `walker/tests/home_isolation.py`.
- Verify visuals without capturing private windows: render QML offscreen
  (`QT_QPA_PLATFORM=offscreen` and `grabToImage`) or take a screenshot only
  while the overlay under test covers the whole screen. Delete test captures.
- Start long-running test shells as transient `systemd-run --user` units and
  stop them afterwards; processes backgrounded from a tool shell die with it.
- The public ISO bucket (Cloudflare R2 `eitr-downloads`) keeps exactly one ISO.
  When publishing a new ISO, delete the previous one first, then upload, then
  verify; never leave two ISOs stored (`distro/RELEASES.md`, Downloads).
  The whole bucket (ISO plus the `repo/` and `repo-testing/` package folders)
  must stay under R2's free 10 GB. Check its total before and after every ISO
  upload and every package publish, and stop to ask if a step would pass it.
- Another agent may be editing this checkout. Read `git status` and stage
  explicit paths; never stage website build output.
