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
- `rows`: 1–20 actions. Each requires `title` and `description` (at most 72
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

Version 2 retains all version 1 fields and adds optional `ui`. Version 1
manifests keep their validation and behavior; they cannot declare `ui`.
`ui` accepts only `tiles` and `panels`, each an array of at most eight objects.
Every object requires `id`, `title` (72 characters maximum), and `qml` (a
relative `.qml` path inside the plugin). IDs follow the plugin ID grammar and
must be unique across tiles and panels. Optional `icon` is up to eight characters.
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
Plugin tile QML supplies `api.detail` and optional trailing content (root
`implicitWidth`, capped at 96 px); it must not draw another tile or title.
Declare `panel` on a tile to name one of this plugin's panels. The host handles
click, Return and Space. Panels replace the tiles with a back chevron and title.
Back or Escape returns to tiles; another Escape closes Control Center.
Panel height follows the root `implicitHeight`, scrolling above 360 px.
Placements are prefetched in the background, retained while closed, and refreshed
on installation, update, removal and re-enabling, without open-page polling.

Every root component must be a QtQuick Item and declare
`required property var api`. The injected object exposes:

- `foreground`, `background`, `accent`: live theme colors.
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
