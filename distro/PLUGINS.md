# Plugin author guide

## Schema version 1

Declare `"schemaVersion": 1` in the root `eitr-plugin.json`. A missing field is
accepted as version 1 for existing plugins, with a review reminder. Other values
are refused; a higher integer requires a newer Eitr. Booleans are not versions.

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
