# Theme packages

The JSON backend is `python3 walker/scripts/actions/install/themes.py` with
`index URL`, `install URL ID [ID ...]`, `list`, `check`, `update ID` and
`remove ID`. Each response has `ok` and `result`, or `ok: false` and `error`
with exit status 1. There is no catalog UI yet. HTTPS and SSH Git addresses
are accepted; file URLs are reserved for library tests. No repository code,
checkout filters, hooks, installers or submodules run.

## Authoring

Each package folder contains `eitr-theme.json`:

```json
{
  "schemaVersion": 1,
  "id": "example-dark",
  "name": "Example Dark",
  "description": "Deep forest greens with warm cream text",
  "version": "1.0.0",
  "light": false
}
```

All fields are required. Unknown and duplicate JSON keys are refused. IDs use
lowercase ASCII letters/digits separated by single hyphens, at most 64 characters.
Names and versions are nonempty printable strings of at most 64 characters;
descriptions have a 72-character limit. The light flag is a boolean, and the
schema version is integer 1.

Required files are `colors.toml`, `display-name`, `preview.png`, and a nonempty
`backgrounds/` directory. `display-name` matches `name`. Light themes contain
`light.mode`; dark themes do not. Palettes require background, foreground, accent
and color0 through color15 as six-digit hex colors. Additional palette values
are hex colors, except optional `mode`, which matches the light flag, and
`hyprland_*` border values, which use Hyprland's `rgb(...)`/`rgba(...)` colors
(several for a gradient, optionally followed by an angle such as `45deg`).
Previews are PNG, at most 2 MiB and 2048 pixels per dimension.

Packages contain only `colors.toml`, `display-name`, `light.mode`, `preview.png`,
`artwork.md`, `rgb.color`, `eitr-theme.json`, and assets under `backgrounds/`,
`backgrounds-ultrawide/` or `motion/` (JPEG, PNG and JSON). Case matters.
The limit is 128 MiB and 1000 entries (files plus directories) per theme.
Symlinks, executable bits, special files, hidden paths and other files are refused.

`icons.theme`, `vscode.json`, `neovim.lua`, `btop.theme` and `dolphin.theme`
are generated locally in staging after validation on every install and update;
packages containing any of them are refused. The installer and
`themes/build-theme-files.py` share `themes/theme_files.py`.
Official themes with an entry in Eitr's package-owned
`/usr/share/eitr/themes/integrations.json` use that trusted integration, including
editor plugins and extensions. The 12 themes planned for migration retain their
entries there even after their folders move. Other themes use palette-driven
Neovim colors, built-in VS Code defaults and local application defaults, without
installing any editor plugin or extension. A matching ID in another repository
never grants access to trusted integrations. Dolphin selections are generated
from trusted integration metadata or the default light/dark flavor.

Existing built-ins retain their generated editor artifacts. Export only the
allowed data files when publishing one as a package. This step does not move
the built-in themes.

## Repository index

Run `python3 tools/theme-catalog-index.py REPOSITORY` and commit the resulting
root `eitr-catalog.json`. CI runs the same command with `--check`. It discovers
package manifests recursively, validates each with the installer owner, and
writes a sorted JSON list. Each entry contains `id`, `name`, `description`,
`light`, `folder`, `size` (total file bytes), and `preview` (repository-relative
`folder/preview.png`). IDs and folders must be unique; folders cannot overlap.
The index is limited to 1 MiB and 1000 themes when consumed.

The remote Git server must support partial clone filtering. Index reads clone
with `--filter=blob:none --sparse --no-checkout` and read only the index blob.
Installation reads regular blobs only from selected trees, at one pinned commit;
there is no full checkout. Metadata and downloaded objects are cached under
`$XDG_CACHE_HOME/eitr/theme-repositories`. Update checks fetch Git metadata and
the index, counting commits touching each installed folder, without changing
installed files. Rewritten histories that lose an installed commit fail clearly.

## Installed state

Packages install under `$XDG_DATA_HOME/eitr/themes/ID`. Their private
`.eitr-theme-source.json` records URL, commit, folder and derived official flag;
it is distinct from user-created themes' `own-theme.json`. Official status is
recomputed using the plugins' URL normalization and requires exactly
`github.com/eitr-org/eitr-themes`. Manifests and cached flags confer no trust.

Built-in IDs, whole-theme overrides, user-created themes and existing packages
cannot be overwritten by install. Update replaces only a package from its
recorded repository. Every selected package validates before any destination
changes. Staging and backups live beside destinations; a failed rename restores
previous directories. A process crash or power loss during a multi-theme rename
is not a durable multi-directory transaction. Backend operations share a lock.

Removing the current theme is refused: apply `eitr` first through the existing
theme picker or `eitr theme set eitr`, then retry. This avoids changing desktop
state as a side effect of removal. Built-ins and user-created themes cannot be
removed through this backend. Updating an active package changes its installed
files; reapply it to refresh the copied current theme and generated styles.

Existing Walker and bar pickers, apply.sh and regeneration use the user-data
lookup path already. Only `own-theme.json` enables the pickers' user-created
editing/deleting controls.
