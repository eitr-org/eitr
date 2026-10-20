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
