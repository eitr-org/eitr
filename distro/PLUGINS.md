# Plugin author guide

## Schema version 1

Declare `"schemaVersion": 1` in the root `eitr-plugin.json`. A missing field is
accepted as version 1 for existing plugins, with a review reminder. Version 2 adds the optional visual declarations below; a higher integer requires a newer Eitr. Booleans are not versions.

Version 1 fields and hook names will not change meaning or be removed within
1.x. Additions are optional fields. A breaking change requires schemaVersion 2;
Eitr will support both versions for at least one release.

The manifest is a JSON object of at most 64 KiB, without duplicate or unknown
keys. Required fields:

- `id`: up to 64 lowercase letters/digits, separated by single hyphens; stable
  across updates and unique among installed plugins.
- `name`, `author`, `version`: nonblank display strings, at most 256 characters.
  `version` is the author's display version; approval pins a Git commit.
- `description`: nonblank summary, at most 72 characters.
- `rows`: 1–20 actions (0–20 for a schema version 2 plugin that declares `ui` components). Each requires `title` and `description` (at most 72
  characters) and `run`. Optional `icon` is a nonblank string up to 64 characters;
  optional `arguments` is an array of at most 64 fixed strings, each at most 4096
  characters. Empty arguments are allowed; control characters are refused.

Optional fields are `schemaVersion`, `service` and `hooks`. Display text rejects
control characters. `run` names an executable file inside the repository, never
an absolute path or a path containing `..`. Symlinks anywhere in a plugin are
refused. Submodules are not initialized.

## Execution

Rows launch as the current user, detached, with the plugin directory as their
working directory and the desktop process's environment. The executable and
arguments form argv: no shell expansion, interpolation or command string is
performed. Use an executable script with a shebang. Plugins have the user's
full permissions; they are not sandboxed or reviewed by Eitr. Installation and
updates require review before any plugin command runs.

An optional `service` object accepts `run` and optional `arguments` with the same
validation. Eitr manages one systemd user service, enabled at login and started
on approval, with `NoNewPrivileges=yes`, `Restart=on-failure` and `RestartSec=5`.
Its working directory and environment are the user manager's defaults, rather
than the plugin directory. Use paths relative to your script's location there.
Removal disables and stops the service but cannot undo changes a plugin made.

## Event hooks

`hooks` maps event names to objects with `run` and optional `arguments`, using
the row command validation:

```json
"hooks": {
  "theme-changed": {"run": "notify.sh", "arguments": ["Theme changed"]}
}
```

- `theme-changed`: after the theme switch finishes; `EITR_THEME` is the theme id.
- `wallpaper-changed`: after wallpaper application; `EITR_WALLPAPER` is its
  absolute path.
- `after-update`: after System Update installed updates successfully. A check
  that finds nothing to update, and the terminal-only `eitr update pacman`,
  `aur` and `full` commands, do not emit it.
- `login`: once per desktop session after the bar starts.

Hooks run as the user, with argv, plugin working directory and inherited desktop
environment, plus `EITR_EVENT` and the relevant context above. Unrelated Eitr
event context is removed. Triggering actions launch the dispatcher without
waiting. Each hook has a 30-second timeout; its process group is killed on timeout.
Output, failures and timeouts go to `$XDG_STATE_HOME/eitr/plugin-hooks.log`
(default `~/.local/state/eitr/plugin-hooks.log`). A failure does not stop other
plugins or fail the triggering action. Hooks from separate events may overlap;
authors must handle this. Do not rely on ordering between plugins.

The runner is `eitr plugin hooks EVENT`. Blocklisted plugins, plugins disabled
by organization policy and repositories outside a policy allowlist never run
hooks. Hook declarations appear in install review; added or changed declarations
raise update RISK flags. Hooks are not run during installation or update review.

See `distro/plugins/example/` for a manifest, notification row and theme hook.
The example is documentation and is never installed automatically.

## Visual components (schema version 2)

Version 2 retains all version 1 fields and adds optional `ui` and `capabilities`. Version 1
manifests keep their validation and behavior; they cannot declare `ui`.
`ui` accepts `tiles`, `panels`, `widgets` and `barItems`, each an array of at most eight objects.
Every object requires `id`, `title` (72 characters maximum), and `qml` (a
relative `.qml` path inside the plugin). IDs follow the plugin ID grammar and
must be unique across all four kinds. Optional `icon` is up to eight characters.
Optional `dataCommand` uses the same `{run, arguments}` validation as rows.
Optional `refreshInterval` is milliseconds: zero (on demand), or 1000–3600000;
a nonzero interval requires a data command. Unknown fields are refused.
At most 32 QML files are allowed per visual plugin, each UTF-8, without NUL,
and no larger than 64 KiB. Symlinks are refused anywhere in the repository.

```json
"ui": {
  "tiles": [{"id": "hello", "title": "Hello", "qml": "HelloTile.qml", "panel": "hello-panel"}],
  "panels": [{"id": "hello-panel", "title": "Hello status", "qml": "HelloPanel.qml"}]
}
```

Tiles appear at the end of **Control Center > General**, under **Plugins**, only
when tiles are declared. The host draws each 36 px row: declared icon centred
in the 10 px leading slot, title at 36 px, and optional caption with a 2 px gap.
With `look: "eitr"` (the default), plugin tile QML supplies `api.detail` and optional trailing content (root
`implicitWidth`, capped at 96 px); the host supplies the title and row. With `look: "custom"`, QML fills the whole fixed 36 px high, full-width slot and draws everything. The host only handles click/Return/Space, keyboard focus and the focus ring.
Declare `panel` on a tile or bar item to name one of this plugin's panels. The host handles
click, Return and Space. Panels replace the tiles; by default the host shows a back chevron and title.
Back or Escape returns to tiles; another Escape closes Control Center.
Panel height follows the root `implicitHeight`, scrolling above 360 px.
Placements are prefetched in the background, retained while closed, and refreshed
on installation, update, removal and re-enabling, without open-page polling.

Every root component must be a QtQuick Item and declare
`required property var api`. The injected object exposes:

- `foreground`, `background`, `accent`: optional live theme colors.
- `palette`: full theme palette, including `color0`–`color15` and named roles from colors.toml. `themeChanged()` signals changes to the palette or style helpers.
- `fontFamily`, `bodySize`, `captionSize`, `headingSize`, `radius`: shared style.
- `title`, `icon`: this component's manifest labels.
- `runDataCommand()`: runs only this component's declared argv, with its plugin
  directory as cwd. Repeated calls while busy are ignored. Runs on component
  load and at `refreshInterval` while the General page is open.
- `loading`, `dataText`, `dataError`: command progress, UTF-8 stdout and helper
  error text. Commands time out after ten seconds and output above 64 KiB is
  refused. Do not use this helper for unbounded output or background jobs.
- `detail`: writable optional tile caption.
- `openPanel(id)`: in-panel navigation to a panel belonging to the same plugin.
- `reportError(message)`: reports a fatal component error and unloads it.

The Loader checks status and replaces failed content with an inline error.
Failures are logged to `$XDG_STATE_HOME/eitr/plugin-ui.log`. After three load
or reported errors across a plugin's components, its visual components are
persistently disabled (including after updates). The tile shows how to reset:
`eitr plugin enable-ui ID`. Close and reopen General to retry before the
threshold; after resetting, the next refresh reloads the component. Script rows,
hooks and services retain their existing independent behavior. Policy and
blocklist refusals also hide visual components. Disabled state lives in
`$XDG_STATE_HOME/eitr/plugin-ui.json`.

**QML is not a sandbox.** Components run inside the bar with the user's full
permissions. The API is a supported interface, not a security boundary: QML
can import other modules, execute code and reach its environment. Loader error
handling cannot contain infinite loops, native crashes or arbitrary runtime
binding warnings. Authors should catch their own fatal runtime errors and call
`reportError`. Install only trusted code. No in-process host can promise crash
isolation against arbitrary plugin code.

Install review lists every QML file, including helpers not declared as entry
points, and displays its full source without executing it. Added, changed or
removed QML raises update RISK flags. Visual updates open the full scrollable
diff before approval and display the candidate's full QML sources as well.
The example includes HelloTile.qml and HelloPanel.qml; select Hello to open
its status panel. It is never installed automatically.


### Desktop widgets and bar items

Nothing in `widgets` or `barItems` appears until the user places it from
**Control Center > Plugins** or **Install > Plugins > plugin > Visuals**.
Widgets require a monitor choice. Each widget supports optional integer
`minWidth`, `minHeight` (default 96), `defaultWidth`, `defaultHeight` (default 192),
with `24 <= min <= default <= 4096` in logical pixels. Like tiles, both kinds
support `dataCommand` and `refreshInterval`. Bar items may name a declared `panel`.
The example's ClockWidget.qml and StatusDot.qml demonstrate both kinds.

Widgets use individual bottom-layer Wayland surfaces, behind ordinary windows,
with input limited to each widget rectangle by default. Their appearance belongs to the author. Eitr backgrounds and theme helpers are optional. The placed widget’s **Edit position** action exposes
move and resize handles; **Done** leaves edit mode. Geometry snaps to the
Hyprland inner gap and is clamped to the monitor's usable area, including reserved
edges. If the screen is smaller than a declared minimum, fitting the screen wins.
Positions are stored in logical monitor-local coordinates. Disconnecting a monitor
hides its widgets and keeps their placements; reconnecting restores them.

`$XDG_CONFIG_HOME/eitr/plugin-placements.json` is machine-local and never shipped:
`{"version":2,"widgets":[{"plugin":"example","id":"clock","monitor":"DP-1",
"x":24,"y":48,"width":240,"height":144,"aboveWindows":false}],"barItems":[{"plugin":"example",
"id":"status-dot"}]}`. Edits use the manager's lock and atomic writer. Removing
or updating a plugin preserves preferences, so a later matching declaration can
restore the placement. Removing a widget from a missing monitor is available in
both management interfaces. Edit mode is session-only.

Bar items occupy fixed icon slots in the existing right-side group, with its
normal hidden/show toggle (always shown in Tabs). They have no hover fill and
use short themed tooltips. Their content is clipped to the slot. Declared panels
use the same attached Full or detached Centered/Tabs geometry, Escape and
outside-click dismissal as built-in controls; their surface is opt-in. The clock's independent screen
centre anchors remain unchanged on every edge and layout.

All four kinds share the loader, style/data API, failure counter and full QML
review. **Re-enable** in Control Center’s Plugins page (or **Re-enable visuals** in Walker) resets the same
counter as `eitr plugin enable-ui ID`. Widgets and visible bar items refresh data
while loaded; tiles and panels refresh while open. The existing QML runtime
limitations still apply; unreported binding warnings are not counted.


### Audio spectrum (schema version 2)

Declare `"capabilities": ["audio-spectrum"]` at the manifest root. Only this
capability is supported; unknown names, duplicates and non-array values are
refused. Version 1 cannot declare capabilities. Installation review describes it
as “Reads the system audio spectrum (levels only, no audio is recorded or sent)”.
Adding it raises an update RISK flag. This is playback-monitor analysis only:
the host fixes PipeWire `source = auto` (sink capture), with no microphone or
input-source API. No audio samples are exposed, stored or transmitted.

The component API adds:

- `spectrum`: read-only array of normalized 0..1 levels, empty while inactive.
- `audioActive`: true when a recent spectrum frame contains a nonzero level.
- `spectrumBars`: writable integer, default 64, clamped to 8–128.
- `spectrumFrameRate`: writable integer, default 30, clamped to 1–60 fps.
- `spectrumSmoothing`: writable boolean, default false; requests light smoothing.

For example, set `api.spectrumBars = 48` and `api.spectrumFrameRate = 30` from
`Component.onCompleted`, then bind a Repeater to `api.spectrum` and each bar's
height to its level. A single reference-counted provider serves all visible
components and the media equalizer. It uses the maximum requested count and fps (capped at 128/60), with weighted
area resampling and capped delivery for each consumer. Configuration changes are
debounced by 300 ms, retaining the last frame during restart. Cava smoothing is
enabled only when all consumers are plugins requesting it; otherwise requesting
consumers smooth locally. The media equalizer alone uses 4 bars at 30 fps with
no smoothing section, preserving its original config.
The private cava config supports bars, framerate, monstercat and noise reduction.
The shared stream stops when the last consumer hides or unloads. Failure retries
back off from 500 ms to 30 seconds; missing frames clear after 1.5 seconds.
Silence yields zero levels. This does not depend on MPRIS metadata.

### Live line streams

Each visual declaration may include `dataStream: {"run": "levels.py",
"arguments": ["--fixed-option"]}`. It has exactly the same executable/path/argv
validation as `dataCommand`, and both may coexist. Install review lists the
command; added or changed stream declarations raise update RISK flags.

`api.streamLine` holds the latest complete stdout line without its newline;
`api.streamReceived(line)` fires for each accepted line, including repeated
identical lines. Output is UTF-8 (invalid bytes replaced), capped at 4096 bytes
per line and 60 accepted lines per second. Oversized lines are discarded through
the next newline, excess lines are dropped, partial EOF lines are discarded,
and stderr is discarded. The transport reads bounded chunks and retains only a
bounded partial line; it does not accumulate output or log payloads.

The command runs in the plugin directory only while its component is visible
and enabled. Exits retry with exponential backoff (500 ms–30 s, reset after ten
seconds running). Hiding/unloading stops the supervisor and kills the child
session's process group, including descendants. The Linux supervisor also
cleans up when its parent exits. Commands must flush stdout. These limits bound
the supported transport, not arbitrary trusted QML or escaped process sessions;
plugins still have the user's full permissions.

### Window layers

Each placed widget offers **Show above windows** in Control Center > Plugins and Walker Visuals.
It switches from Bottom to Top and uses an empty input region except during
**Edit position**. Above-window widgets hide while their monitor has a fullscreen
window. Both layers remain on every workspace; monitor-local geometry and
unplug/reconnect behavior are unchanged. Behind windows remains the default.
Placement version 2 adds boolean `aboveWindows` per widget. Version 1 is migrated
in memory with `false`; the next placement edit atomically saves version 2.


### Plugin manager and artwork

Control Center has a dedicated **Plugins** page (`controlCenter show plugins`).
It lists all installed plugins, including disabled ones, with their name, author,
version, description and status. Expand **Preview** to see a declared screenshot.
Add, Update and Remove open the reviewed terminal flows; removal still asks for
confirmation. General keeps only plugin tiles and their panel navigation.

`eitr plugin disable ID` stops and disables the service, hides all visuals and
Walker actions, and skips hooks and data streams. `eitr plugin enable ID` checks
policy and the approved commit before restoring the service and declarations.
The boolean `enabled` lives in Eitr's existing `plugins.json` approval record;
missing means enabled. Placements and the independent visual failure counter
survive disable, updates and enable. Reset visual failures with `enable-ui`.

New schema v2 installations require `icon`, a relative path inside the repository:
PNG (square, 64–1024 pixels) or a square self-contained SVG, at most 512 KiB.
SVGs contain shapes only, without entities, external references or scripts.
Optional `preview` is a PNG/JPEG screenshot up to 2 MiB and 3840 pixels on either
axis. Optional `homepage` is an HTTPS URL without credentials. Images must have
valid headers and structure; symlinks and paths escaping the repository are
refused. Install/update review lists artwork paths. Schema v1 and existing v2
plugins without an icon remain readable and use a generic glyph, with a review
note. Existing iconless v2 updates may remain iconless; an update cannot remove
a declared v2 icon.

### Widget options and transparent surfaces

A widget declaration accepts `surface: "panel" | "none"` (default `none`).
The placement can override it with the same field. **Background: Transparent**
sets `none`: the host draws no color, border or blur. Transparent widgets use
`eitr-plugin-transparent`, outside the panel-only `eitr-plugin-widget` blur rule.
Plugin QML may draw any colours, images, shaders or animation, including its own opaque background. Edit mode always
shows the outline, title handle, resize grip and Done control.

Right-click a behind-window widget, or any widget while editing, for **Edit
position**, **Size: Smaller / Larger** (90% / 110%, preserving aspect and centre
where bounds permit), **Full width**, **Background**, **Show above windows**,
plugin options and **Remove from desktop**. Size is limited by declared minimums
and the monitor's usable area; fitting the screen takes precedence over minimums.
Full width uses the largest aspect-preserving size that fits the usable screen.
Above-window widgets stay click-through: their options are in **Control Center >
Plugins**, including plugin-declared entries. **Edit widgets** in that page or
Walker Visuals toggles global edit mode (`plugin-widgets edit` IPC); **Done**,
Escape or `plugin-widgets done` exits. Editing temporarily raises widgets above
windows and permits keyboard and pointer input. Dragging uses monitor-local
pointer coordinates and unsnapped motion; release snaps and atomically saves.

Widgets may call `api.setMenu([{id: "wave", text: "Wave", checked: true}])`.
At most 20 entries are accepted, with unique lowercase alphanumeric/hyphen IDs
(up to 64 characters), nonblank single-line text (up to 72 characters), and an
optional boolean `checked`. Invalid lists leave the previous menu intact.
Handle `api.menuTriggered(id)` through a QML `Connections` object; call `setMenu`
again to update checkmarks. These actions run only in the loaded widget instance,
so each monitor can keep independent state. Menus do not execute shell strings.

### Author-controlled appearance

Following Eitr's style is optional for every visual component. Theme colors,
fonts, sizes and radius are helpers, not requirements. Authors may use any
colors, images, shaders and animations. Relative QML asset paths (for example
`Image { source: "images/logo.png" }`) resolve inside the plugin's own directory,
relative to the QML file; assets are part of the reviewed repository.

Panels accept `surface: "none" | "panel"` (default `none`) and boolean `header`
(default `true`). The plugin area is a free canvas: no host fill, border, tint
or content inset is added unless `panel` is requested. Control Center retains
its existing page surface behind that canvas; bar panels have a transparent
outer surface by default. This one default avoids adding a second panel inside
Control Center while allowing bar panels to draw their own appearance.
`header: false` hides the navigation header; Back/Escape navigation remains.
The outer desktop frame, bounds, scrolling, dismissal and navigation are host UI.

Widgets default to `surface: "none"`; `panel` opts into the Eitr background and
blur. Explicit saved placement choices win over the declaration; without a saved
choice the current declaration wins, falling back to `none`. Edit handles remain
host UI. Bar slots never add hover fills or tint to plugin content. Fixed tile,
bar and widget bounds, clock centring, review, capability checks and visual
failure handling apply regardless of appearance. The example's CustomTile.qml
shows independent purple/yellow colors beside the Eitr-styled Hello tile.
