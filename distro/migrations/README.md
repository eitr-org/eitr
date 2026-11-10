# Settings migrations

When a release changes the shape of a user preference (a renamed key, a moved
file), add a migration here instead of resetting the setting. Each file is a
Python script named `YYYYMMDDHHMMSS-description.py`; the package installs them
under `/usr/share/eitr/migrations`.

At login, `eitr-session` runs every migration the user has not run yet, in name
order, and records each success under `~/.local/state/eitr/migrations`. A failing
migration stops the run, is logged to `~/.local/state/eitr/migrations.log`, and
is retried at the next login. Fresh installations and `eitr-config adopt-layout`
mark all shipped migrations as done, because their settings already have the
current shape.

A migration must be safe to rerun after a partial failure, keep unknown fields,
write files atomically (`eitr_paths.write_settings`) and never touch credentials.
Add a focused test with it.

## Deferred extra-theme installation

`20261103120000-extra-theme-packages.py` only writes a pending list and succeeds,
so offline downloads never stop later settings migrations. Fresh adoption marks
the migration done without creating this list. After login settings are ready,
`eitr-session` starts `eitr_theme_migration.py` in the background when pending.
A nonblocking per-user lock prevents duplicate workers. Git runs with its usual
deadlines and prompting disabled; network failures keep the pending list for the
next login, without notifications. The worker uses one sparse
repository and the catalog's validated data-only multi-theme install, ordered
with the current theme first. It never applies a theme, regenerates output or
writes appearance/wallpaper preferences. While the current extra theme is
pending, session upgrade regeneration is deferred, preserving generated output.

Each retry removes already installed package IDs from the pending list before
fetching; installation validates all remaining themes before publishing any.
After the first full success the list is deleted. Neither later removals nor
new logins recreate it.

## Tailscale plugin

`20261110190000-tailscale-plugin.py` queues the official Tailscale plugin, which now
draws Tailscale's bar icon and panel; fresh installs queue it from `install.sh`. After
login settings are ready, `eitr-session` starts `eitr_tailscale_migration.py` in the
background. It installs only on desktops with the `tailscale` command and without a
plugin of that ID, from `eitr-org/eitr-plugins` at the pinned reviewed commit, through
the normal validated install (its bar icon is placed, its receive service enabled) and
then notifies. Network failures keep the queue for the next login without notifications.
