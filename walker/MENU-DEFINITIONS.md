# Menu definitions and projections

Fixed rows belong in `elephant/menu-rows/<menu>.json`. Keep title (`text`),
description (`subtext`), icon, keywords, submenu and actions together. Provider
metadata and Parent remain in `elephant/menus/<menu>.lua`; shortcut links do not
change a destination's Parent. Main retains its custom order; other menus sort
folders before actions through the existing translation adapter.

`elephant/row-entry.lua` owns the common browse/search presentation, including
turning `>` into submenu state without a description. `scoped-menu.lua` supplies
browse actions; `search-index-entries.lua` supplies validated provider activation.
The prepared index never stores commands or gains Apps uninstall actions.

`distro/lib/eitr_menu.py` loads the same fixed definitions for search metadata,
Control Center actions and remote status. Dynamic providers still own their live
rows: apps, clipboard, cloud/account navigation, plugins, installed software,
themes, wallpaper, fonts, keyboard layouts and current setting choices. Search
snapshots those providers rather than maintaining a second list of their choices.

## Live menu search

Dynamic providers wrap their final browse loader with
`dofile(paths.code("elephant/live-menu.lua"))(Name, load, context)`.
`load()` returns the unchanged browse entries and an optional list of descendant
groups, each `{parent = label, entries = rows}`. The same function supplies both
projections from its loaded data. Descendant actions bind their account/plugin
ID explicitly; they must not depend on selecting a folder first. Do not project
context-dependent submenu links that require another menu's `lastMenuValue`.
Keep the destination's real `Parent` for Shift+Backspace.

An empty query refreshes the snapshot. The adapter stores it as JSON in Elephant's
per-menu string state because every query runs in a fresh Lua VM. Typing reuses
that snapshot and appends prepared scoped-index rows, leaving matching to Elephant
as `scoped-menu.lua` does. Child results show their parent as the description.
The optional context function reads only local state and invalidates a snapshot
when the selection changes; a cold or invalidated typed query returns no rows
until the menu is opened again. Locale changes also invalidate the snapshot.
Never call a provider, cloud CLI, or network service on the typing path.

Git account rows carry their action projection from the loaded account model.
Plugin loaders share installed metadata and launch rows for their descendant
projection; blocked plugins expose no child actions. Keyboard shares one catalog
loader between Keyboard's child projection and Add Layout. Calendar sources,
web apps, AI accounts and other leaf providers retain their browse actions.
Reminders uses fixed rows and remains on scoped-menu.

Keyboard layouts stay searchable only within Keyboard and Add Layout. Cloud
account lists never expand into account contents. Inside an opened cloud account,
the snapshot projects static service actions, skipping descendant resource selectors
and external providers that need further reads. A resource picker loads its own
rows only when opened. Plugin visual choices that require compositor reads remain
in Visuals. Global app search keeps launch actions only; uninstall remains in Apps.


## Duplication inventory and ownership

| Previous repeated definition/projection | Owner and adapters |
| --- | --- |
| Fixed JSON/TOML loading in search-index and menu-action | eitr_menu loads definitions; both callers retain their own authorization and presentation |
| Submenu marker, description, icon and keywords in browse and search Lua | row-entry; caller retains navigation and action routing |
| Remote panel rows loaded indirectly through menu-action | eitr_menu rows; remote-status only filters and translates the panel view |
| Learn shell shortcut labels/bindings/actions and indexed shortcuts | Indexed rows remain in menu-rows/shortcuts.json; shortcut-reference.json references their titles and derives bindings/actions from them |
| Assistant primer parsing Learn shell text | eitr_assistant_context uses the shared shortcut projection |
| Shell-only shortcut groups and bindings | shortcut-reference.json; shortcut-reference.py renders the shell chooser; handbook-build renders tables from the same projection |
| Focus shortcuts in chooser/provider/Handbook | Existing eitr_focus shortcut_entries and focus-mode entries adapter remain authoritative |
| Current marks and fixed setting choices | Existing choice-entries, bar-settings-entries and setting owners remain authoritative; index consumes their provider output |
| Identical destinations exposed in different menu locations | Each placement retains its own description, icon and parent; these are separate rows, not alternative definitions of one row |

The reference preserves the shell view's existing labels and order. Its command
field is only needed for shell-only bindings or existing differences from the
indexed command (for example fullscreen and terminal launch). It never overrides
an indexed row. Do not add another binding/action list to the shell script or
Handbook builder. The shell reference remains English as before; the indexed view
continues through menu translations. `walker/tests/fixtures/menu-parity.json`
records the pre-refactor fixed rows, parents and shell reference for regression
checks, not runtime consumption.
