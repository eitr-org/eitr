# EITR code and settings separation

Status: **implemented**, verified in offline VM installs: fresh encrypted and
unencrypted installs, a package upgrade that changes shipped QML (preferences
byte-identical), both factory resets, and an old-layout installation upgraded,
adopted and reset back to its pre-adoption restore point. It also runs on the
owner's real desktop, installed from the ISO and kept current by System Update.

Goal: before v1, a normal package upgrade must update the desktop's code without
touching what the user customised. Shipped code moves to `/usr/share/eitr`, owned
by `eitr-desktop`; `~/.config` keeps only preferences, generated per-user output
and deliberate overrides.

## 1. Before the layout change

Package staging maps config sources to `/usr/share/eitr/config/<source>` and
HOME_FILES to `/usr/share/eitr/home/<source-without-HOME_FILES>`. `eitr-config`
then copies these into each home. Its version-1 checksum ledger records file
contents and symlink targets, not settings. `seed` never overwrites; `update`
replaces unedited files and writes `.eitr-new` beside edited or unmanaged ones,
so a user who edits one line of a shipped file stops receiving fixes for it.
Removed defaults stay in home as obsolete files. Staging copies whole source
directories, including tests, docs and reference artwork. The package builds
committed HEAD, not the working tree.

`install.sh` preflights whole config trees, seeds homes, generates styles and
records installed paths. Hyprland and D-Bus start Quickshell with `-c`, and many
menu actions and IPC calls select shells by config name. The nightlight user unit
executes `%h/.config/walker/...`. The active theme output is `theme/current`
(singular); `themes/` is the catalog. Keep `theme/current` as the only current
theme.

A security issue of that layout is fixed: `configure-desktop.sh` ran the
user-writable `~/.config/quickshell/lockscreen/scripts/install-login.py` as root;
it now runs only the package's copy under `/usr/share/eitr` (section 3).

Out of scope: the signed repository, prebuilt-AUR publication, a general
settings-migration framework, crash reporting and release automation.

## 2. Classification and target ownership

| Class | Meaning | Upgrade rule |
| --- | --- | --- |
| C | Shipped code: executable logic, UI layouts, loaders, behavior templates | Pacman replaces it under `/usr`; never copied into home by default |
| D | Shipped data: artwork, palettes, documentation, catalogs | Package-owned; copied only when it becomes a preference or output |
| G | Generated per-user output, derived from settings | User-owned; regenerated from current shipped code; deliberate edits preserved |
| P | User preference or state, including native application customization | User-owned; seeded once when missing, never reset by an upgrade |

The classification lives in one machine-readable manifest,
`distro/layout-manifest.json`: ordered path patterns mapped to a class and a
`runtime` flag (tests, reference artwork, generation manifests, caches and
development dotfiles are not runtime payload). PKGBUILD staging, `eitr-config`
and a test that fails on any unclassified tracked file all read it, so the
classification cannot drift from the tree. The one-time inventory used to draft
it (949 tracked paths at `56bd586`) is evidence only and is not kept in this
document.

| Repository source | Class | Target and consumers |
| --- | --- | --- |
| `quickshell/{desktop-bar,lockscreen,emoji-picker,wallpaper-transition}/` QML, JS, helpers | C | `/usr/share/eitr/quickshell/...`; Quickshell, menu actions, IPC, Hyprland, D-Bus |
| Quickshell assets, emoji data, corner styles, Handbook catalog, content and images | D | Same shipped tree; catalog built before packaging |
| `elephant/menus/*.{toml,lua}`, shared Elephant Lua modules | C | `/usr/share/eitr/elephant/...`; Elephant and the global search index |
| `walker/bin`, `walker/scripts`, Walker theme XML layouts | C | `/usr/share/eitr/walker/...`; stable `/usr/bin/eitr-*` launchers dispatch into it |
| `walker/config.toml` | D baseline | System config directory; a user file is a reported full override (section 3) |
| Walker `style.css`, `workspace-examples.css`, copied icons | G | User theme output beside links to the shipped XML |
| `hypr/hyprland.lua`, scripts, idle/lock/paper baselines | C | `/usr/share/eitr/hypr/...`; a tiny user loader includes it |
| `hypr/theme-env.conf` | D baseline | Shipped toolkit defaults; an existing user copy remains P |
| `hypr/cursor-env.conf` | G | User config; generators never write the shipped tree |
| `hypr/{local.lua,keyboard-layouts.lua,primary-display,preferred-outputs}` | P | User config; `local.lua` still runs last and guarded |
| `themes/<id>/` palettes, artwork, app theme definitions | D | `/usr/share/eitr/themes/<id>`; menus, generators, Neovim |
| `theme/current/` | G | User config; the selection itself is a versioned preference |
| `kitty/kitty.conf` | C baseline | `/usr/share/eitr/kitty/kitty.conf`, included by a tiny user file |
| `kitty/{theme,fonts,cursor-fire}.conf` | G | User config, included by absolute path |
| `nvim/` | P, seeded once | User config; LazyVim configs are meant to be edited, so upgrades never touch them |
| `Kvantum/*#/*`, `kvantum.kvconfig`, `swayosd/style.css` | G | User config; regenerated colors, fonts and corners |
| `swayosd/config.toml`, `dolphinrc`, `filetypesrc`, `mimeapps.list` | P | Seeded when missing |
| `xdg-desktop-portal/hyprland-portals.conf` | D baseline | Native system path; a user file wins |
| `fastfetch/eitr.py` and assets | C/D | Shipped tree; About and task banners resolve it independently of settings |
| HOME_FILES shell functions and loaders | C baseline | Shipped file sourced by a small user loader; personal additions stay P |
| HOME_FILES desktop entries, icons, D-Bus activation | D/C | Native system locations where precedence allows |
| `systemd/user/*` | C | `/usr/lib/systemd/user`; overridden with native user drop-ins |

Package files are root-owned (directories 0755, files 0644, entry points 0755).
No secrets or owner-machine configuration enter the package.

### Runtime-only settings and outputs

These are not all in Git; their readers and writers were found in source. Native
third-party account files (`gcloud/`, OBS, AWS/Azure/AI credentials, browser and
editor profiles) are left exactly where they are and never copied, versioned or
logged.

| Path relative to the config/state/cache root | Class | Reader/writer |
| --- | --- | --- |
| `quickshell/desktop-bar/{bar-settings,workspace-style,notification-settings,obs-recording}.json` | P | Bar helpers and services |
| `eitr/{cursor,font,style,cloud-contexts,terminal}.json`, `eitr/cloud.env` | P | Cursor, font, style, cloud and terminal helpers |
| `eitr/git-accounts.json`, `~/.gitconfig` managed include | P | Opt-in Git Accounts setup; versioned identities and folder rules |
| `eitr/git-accounts/{active.gitconfig,generations/**}` | G | Git Accounts generates native includes from preferences |
| `eitr/git-accounts/cli/**`, `~/.ssh/eitr-*` | Private account data | Provider CLI tokens and SSH keys; never packaged or backed up by Git Accounts |
| `lockscreen/selected` | P | Lockscreen settings, launcher and SDDM selection |
| `hypr/{primary-display,preferred-outputs,local.lua,keyboard-layouts.lua}` | P | Display helper, bar, Hyprland |
| `theme/current/**`, `walker/themes/current/**`, `kitty/{theme,fonts,cursor-fire}.conf`, `swayosd/style.css` | G | Theme switch and generators |
| `btop/themes/current.theme` plus three owned `btop.conf` keys | G/P | `btop.sh`; other btop settings untouched |
| `gtk-{3,4}.0/settings.ini`, `qt{5,6}ct/*.conf`, `Kvantum/*#`, `kdeglobals` | G/P | System, font and cursor generators |
| `Code/User/settings.json` | P with generated keys | Font and VS Code helpers; JSONC-safe narrow updates |
| State `desktop-nightlight/{mode,schedule.json}`, timer drop-in `schedule.conf` | P / G | `nightlight.py` |
| State `eitr/{installed-paths,user-defaults-state.json,welcome-*}` | State | Installer, `eitr-config`, welcome |
| Cache `current-theme`, `current-wallpaper`, `current-wallpaper-image` | G | Menus, bar, wallpaper; derived from the appearance preference |
| Runtime `eitr-search/index.json`, lock and IPC files; AI, weather, preview caches | G | Regenerated; never packaged or migrated |

### Settings versions

Only EITR-owned JSON preferences gain a version: `{ "version": 1, ...existingFields }`.
Writers keep the version and unknown fields; a newer unsupported version fails
read-only instead of resetting to defaults. Files whose format belongs to another
program (Lua, env, INI, TOML, the `lockscreen/selected` text ID, display lists)
stay unversioned. If a later migration ever needs to change one, that migration
adds its own marker then.

Appearance selection moves to `eitr/appearance.json` (version, theme ID, wallpaper).
The cache strings above become derived outputs, so clearing the cache no longer
loses the selection.

## 3. Code roots and loaders

One packaged path resolver, with thin shell, Python, Lua and QML interfaces,
defines precedence for every component:

- code root `/usr/share/eitr`;
- preferences `$XDG_CONFIG_HOME` (default `~/.config`); data, state and cache
  under their XDG roots, falling back to `$HOME` paths only when unset or relative;
- deliberate code overrides under `$XDG_CONFIG_HOME/eitr/overrides`.

Global `XDG_CONFIG_HOME` is never changed to make a third-party program find
shipped code. A developer checkout is selected by an explicit launch flag, never
by an environment variable honored by root helpers. Root helpers always execute
package-owned code and never source user files as commands.

### Quickshell (all four shells)

`quickshell --help` and `quickshell ipc --help` both accept `-p` for a directory or
QML file; `-c` performs named XDG discovery. A stable launcher `eitr-shell COMPONENT`
resolves the component once and runs `quickshell -n -p /usr/share/eitr/quickshell/COMPONENT`.
The IPC wrapper uses **the same resolved `-p`**; changing startup alone would
break every `-c desktop-bar` caller and the lock fallback's instance checks. Keep
existing IPC targets, actions and duplicate-instance protections.

QML imports, JS, assets, the Handbook catalog and helper scripts keep resolving
beside the shipped code (`Quickshell.shellDir`, `Qt.resolvedUrl`). Preference
FileViews use the config-root resolver; nothing writes beside `shellDir`. The
emoji picker, wallpaper-transition helper and appearance picker move in the same
change.

Override: a complete component tree at `eitr/overrides/quickshell/COMPONENT/shell.qml`
wins. This is an intentional fork, not a per-file overlay, because relative
imports need a coherent tree. `eitr-config status` reports it with the package
version it was based on. Leftover `~/.config/quickshell` trees never silently win.
Session-lock authentication keeps the PAM adapter and Hyprlock fallback whichever
design is selected.

### Hyprland, idle, lock and wallpaper

A tiny user `hypr/hyprland.lua` loads `/usr/share/eitr/hypr/hyprland.lua` and then
the existing guarded `hypr/local.lua` exactly once, moving the local loader out of
the shipped file so it cannot run twice. Load the shipped file with the same
guarded `loadfile`/`dofile` and absolute paths the config already uses for
`local.lua` and keyboard layouts; that mechanism is proven on the running
compositor, so no absolute-path `require` is needed. Toolkit env, cursor env and
keyboard preferences still come from user config; machine settings load last.

Override: `hypr/local.lua` for rules, bindings, devices and environment. Replacing
the tiny `hyprland.lua` loader itself is an advanced override that `eitr-config
status` reports; it receives no shipped defaults unless it loads them.
Hypridle, Hyprpaper and Hyprlock start through a packaged launcher that passes an
existing user config if present, otherwise the shipped baseline, via `-c`
(`hypridle --help`, `hyprpaper --help` and `hyprlock --help` all accept it). Keep
idle timings and fallback behavior.

### Elephant menus and cloud tools

From Elephant's source (commit `a35b3b54ae8bfddaa3bae82d1409cf2d6dfebf3b`;
[files.go](https://github.com/abenz1267/elephant/blob/a35b3b54ae8bfddaa3bae82d1409cf2d6dfebf3b/pkg/common/files.go),
[config.go](https://github.com/abenz1267/elephant/blob/a35b3b54ae8bfddaa3bae82d1409cf2d6dfebf3b/pkg/common/config.go),
[menucfg.go](https://github.com/abenz1267/elephant/blob/a35b3b54ae8bfddaa3bae82d1409cf2d6dfebf3b/pkg/common/menucfg.go)):
`ConfigDirs()` considers user config, then XDG system config dirs, and `--config`
restricts the search to one directory. Provider configuration reads the first
matching file. `LoadMenus()` walks configured `paths` first, then each config
dir's `menus`, then community menus, and a later definition with the same name
replaces an earlier one. Adding `/usr/share/eitr` to `XDG_CONFIG_DIRS` would
therefore let shipped menus replace user menus.

Arrangement:

- Package `/usr/share/eitr/elephant/menus.toml` with
  `paths = ['/usr/share/eitr/elephant/menus']`, exposed as
  `/etc/xdg/elephant/menus.toml`. Provider plugins stay at their native
  `/etc/xdg/elephant/providers` location; do not use `--config`.
- A user `elephant/menus/<name>.{toml,lua}` is the deliberate named-menu override;
  it loads after the shipped path. Shared Lua helpers resolve package code.
- A user `elephant/menus.toml` is a provider-settings override that must keep the
  shipped `paths` entry; `eitr-config status` reports when it drops it. Duplicate
  EITR-owned menu names from other sources fail deterministically.

Global search enumerates the same effective menu set. Menu names, parents,
actions, Apps uninstall scoping and ordering stay unchanged; so do AWS behavior,
Google/Azure context selection and credential locations. Cloud terminals and
their return paths call packaged commands. Install-recipe readers stop preferring
`~/.local/share/eitr` over `/usr/share/eitr`; existing local copies are reported,
not silently honored. Installed Elephant is 2.22.1; the source reading is
confirmed by the Phase 2 prototype gate, not assumed.

### Walker configuration, layouts and generated theme

From Walker's source (commit `a515085fd39fae80acc086c8fbfd9b7771a9a11d`;
[config.rs](https://github.com/abenz1267/walker/blob/a515085fd39fae80acc086c8fbfd9b7771a9a11d/src/config.rs),
[theme/mod.rs](https://github.com/abenz1267/walker/blob/a515085fd39fae80acc086c8fbfd9b7771a9a11d/src/theme/mod.rs)):
Walker reads built-in defaults plus the **first** `config.toml` found in the XDG
config dirs, without layering; theme discovery also honors
`additional_theme_location`. Installed Walker is 2.17.2 and has no config-directory
flag.

Ship the EITR config as `/usr/share/eitr/xdg/walker/config.toml`; the
`walker` package owns `/etc/xdg/walker/config.toml`, so the Walker wrapper every
launch goes through puts `/usr/share/eitr/xdg` first in `XDG_CONFIG_DIRS`. Seed
**no** user `walker/config.toml`. A user who creates one replaces the EITR config entirely,
which `eitr-config status` reports, and the Handbook explains how to start from
the shipped file. No runtime config merging and no per-process
`XDG_CONFIG_HOME` change: those leak into every app Walker launches. The GTK blur
workaround and main-search wrapper stay package-owned launchers.

`walker/themes/current` holds the generated CSS and links to the current shipped
XML and icons; links are refreshed when layouts are added or removed. A real file
in that view is a deliberate layout override that generators never replace;
generated styles append an optional `walker/style.override.css` last.

### Theme catalog and generators

Theme IDs resolve in user `themes/<id>` first, then `/usr/share/eitr/themes/<id>`;
a user theme directory is a deliberate whole-theme override, not a copied
catalog. The same resolver serves Elephant, appearance items, wallpaper
next/apply/transition, Neovim theme discovery and Learn previews. Shipped theme
code is never run as root.

Generators move with their templates to `/usr/share/eitr/walker`, keep their
script-relative imports, and write only to user directories. After a package
upgrade, `eitr-session` regenerates the theme output once for the new package
version (recorded in `/usr/share/eitr/version`), from the existing preferences,
after copying the previous files to `~/.local/state/eitr/generated-backups`.
Theme switches already rewrite these files, so lasting customizations go in the
override files (`hypr/local.lua`, `kitty/local.conf`, `walker/style.override.css`,
`eitr/shell.local.zsh`). No pacman hook runs user generators or restarts
desktop services.

The generators' current whole-file writes (GTK/Qt settings, Kvantum) keep their
behavior in this change; narrowing them to owned keys is deferred (section 6).

### Kitty

A tiny user `kitty.conf` includes `/usr/share/eitr/kitty/kitty.conf`, then
`globinclude`s the generated `theme.conf` and `fonts.conf` and an optional
`kitty/local.conf` by relative path, which resolves beside the user file. kitty
does not expand `${KITTY_CONFIG_DIRECTORY}` while reading its configuration. The shipped baseline drops its relative
`include theme.conf`: relative includes resolve beside the including file, which
would now be under `/usr/share` ([Kitty configuration](https://sw.kovidgoyal.net/kitty/conf/)).
Replacing the tiny `kitty.conf` is a reported override.

### SDDM, user services, shell and other applications

Login designs become **package-owned**: the PKGBUILD builds them from the shipped
lockscreen source into `/usr/share/sddm/themes/desktop-lockscreen-*`, including the
relative `import "LockscreenComponents"` rewrite and the bundled module copy, so
pacman updates the login screen and no root step copies from a home directory.
The ID manifest and the narrow selector helper ship in the package too.
`configure-desktop.sh` keeps only the per-account sudo policy and the initial
selection, using package files. Preserve
`/etc/sddm.conf.d/90-desktop-lockscreen.conf` and existing permissions; never
restart SDDM. Directories created by the old installer are checked against pacman
ownership before adoption; never resolve a conflict with `--overwrite '*'`.

User units keep native drop-in and full-unit precedence, and `ExecStart` points at
package launchers (the nightlight unit included). Elephant keeps
`KillMode=process`. Quickshell starts with the desktop session and owns
notifications. Shell loaders source
shipped functions, then personal additions; `.p10k.zsh` and personal environment
stay user-owned. Streaming launchers, desktop entries, icons and About assets move
to standard system locations with native user precedence. Inspect the
`~/.local/bin/walker` symlink before replacing it, and never shadow `/usr/bin/walker`
with a recursive wrapper.

## 4. Transition

There are no external installations yet, so this is a one-time adoption, not a
general migration engine.

**Old-layout homes keep working.** A home that still has copied code runs that
copy, because its own `hyprland.lua` and launch paths point there. Installing the
new package does not change it, and nothing migrates homes as root or from a
pacman hook.

**Owner's machine:** `eitr-config adopt-layout --dry-run`, then `--apply`, run as
the user:

1. For each legacy file in a C or D location, compare it with the shipped file
   from the package version being adopted. Equal files are archived and retired;
   outdated tests and docs, which never run, are archived without a decision.
   Differing files stop that component, listing the files; the owner chooses per
   component: keep the edits as an override tree, or archive them and use the
   shipped code. Keeping a component is refused while its files still call home
   code that adoption retires. Never auto-merge edited QML, Lua or shell code.
   Files the user added in those folders are kept and listed.
2. Preferences stay in place; EITR JSON files gain `version: 1` without changing
   values (with backups). Generated outputs regenerate at the next session.
3. A legacy file that a native loader replaces (`hyprland.lua`, `kitty.conf`,
   `.zshrc`) is swapped in one rename so watchers such as Hyprland's never see it
   missing; emptied folders are removed. Old user copies of the packaged units
   give way to the package's, with their enable links re-pointed. Root first
   archives unowned files the package now installs (the old installer's login
   designs, a hand-installed network helper; `distro/system/adopt-unowned-files.sh`),
   because pacman refuses to install over them.
4. Archives go to `$XDG_STATE_HOME/eitr/layout-backups/<timestamp>/` (0700),
   preserving bytes, modes and symlink targets, without following symlinks out of
   the user's roots. The report lists paths and decisions, never setting values.
5. The tiny loaders are installed last; a rerun after completion changes nothing.
   Undo restores the archive.
6. Activation happens at the next session. Shells running the packaged code do
   not watch their files, since an upgrade replaces them mid-transaction; only
   `eitr-shell --repo` checkouts and personal overrides reload live. Shells and
   scripts a checkout starts inherit its `EITR_CODE_ROOT`, so they run from the
   checkout too (a wallpaper change tried with `eitr-run --repo` uses the
   checkout's transition). Any live
   change uses that auto-reload and a config-only Hyprland reload where possible, asks before a bar
   restart, verifies `KillMode=process` before restarting Elephant, and never
   restarts SDDM.

Before any write, each live file is compared with the repository; a mismatch stops
that component with a report. Never sync the checkout over home, run a fresh
`install.sh` on this machine or touch `eitr-alpha-test`.

**Alpha ISO installations** (the test VMs) are reinstalled, not migrated.

**Fresh installations and factory reset.** Guided and online installers install
shipped code, seed preferences and the tiny loaders, set keyboard, theme, cursor
and lockscreen, generate outputs offline and set up system integration **before**
capturing the restore point. No first-login builds, password prompts or downloads
are added. Existing restore points are never rewritten by a package update: they
hold their matching old `/usr` and old home layout, and a reset restores that
pair. Both reset modes must be tested against an old-layout and a new-layout
restore point.

## 5. Risks

- **Session identity:** moving from `-c` to `-p` touches IPC, kill, duplicate and
  lock-fallback checks; launchers and every caller change together.
- **Elephant precedence:** provider config is first-match and menus are
  later-match; verify both on the payload's Elephant before switching.
- **Walker override:** a user `config.toml` replaces the EITR config entirely;
  it must be reported clearly rather than discovered by broken menus.
- **SDDM adoption:** old root-owned copies need an ownership preflight.
- **Live upgrade:** loaded QML and scripts can outlive a package replacement;
  prefer apply-at-next-session and no restarts from hooks.
- **Catalog consistency:** every theme, design and search reader shares one
  resolver, including Handbook paths.
- **Licensing:** moving artwork does not resolve its licensing review.

## 6. Phase 2 sequence and verification

Small cohesive commits, after approval:

1. **SDDM packaging** (the security fix): package-owned login designs, selector and
   manifest; `configure-desktop.sh` no longer runs home code as root.
2. **Prototype gate on the builder VM**, before converting components: the
   Hyprland user loader including the shipped file plus `local.lua`; Elephant
   loading `/etc/xdg/elephant/menus.toml` `paths` with a same-name user menu
   overriding a shipped one; Walker reading the system config with no
   user config. If one fails, revise this design first.
3. `distro/layout-manifest.json`, the path resolver, versioned JSON readers and
   packaging tests; code under `/usr/share/eitr` with no home copies.
4. Quickshell launchers and IPC, Hyprland loaders, user units.
5. Elephant menus and global search; Walker system config and theme view.
6. Generators, the theme catalog resolver and Kitty.
7. `eitr-config adopt-layout` and `status`, installer and payload integration,
   restore-point compatibility; documentation and the Handbook kept current.

Tests before claiming completion:

- Every tracked file is classified by the manifest; the runtime payload contains
  no tests, secrets or reference artwork and is root-owned with no symlink escapes.
- Versioned JSON: missing, legacy, version 1, future and malformed values; unknown
  fields kept; atomic writes.
- Adoption: unedited and edited files, extras, symlinks, `.eitr-new` leftovers,
  interrupted apply, rerun and undo; no home writes from package installation.
- Loaders: one resolved path for shell and IPC, no duplicate notification server,
  lock fallback on failure; no real PAM or power tests on the live machine.
- Elephant: shipped menus visible with an empty home, a user menu wins, search sees
  the effective set, AWS unchanged. Walker: EITR actions with no user config, a
  user config reported, new XML layouts arrive on upgrade.
- Hyprland defaults load before `local.lua`, and errors there keep the defaults.
- SDDM: an upgrade replaces login QML and the selection survives.
- Builder VM and **new isolated test VMs**, never `eitr-alpha-test`: build payload
  and ISO, install offline (also encrypted), reboot, log in; bar, menus,
  lockscreen, theme and cursor; both factory resets against old- and new-layout
  restore points; a simulated upgrade changing shipped QML leaves preferences
  byte-for-byte unchanged.
- `bash tools/check.sh` and the Handbook `--check`; report mocked, VM and untested
  hardware results separately.

**Deferred** (separate changes, not needed to separate code from settings):
narrowing GTK/Qt/Kvantum whole-file writes to owned keys; restructuring Neovim into
a shipped runtime with user extensions; portal, Dolphin and MIME adjustments;
version markers for non-EITR file formats.
