---
name: eitr
description: Understand and safely customize the Eitr Arch Linux desktop using its installed Handbook and tools.
---

Read the offline Handbook before changing desktop behavior. Open it with
`eitr handbook` or `eitr handbook troubleshooting`; installed Markdown lives at
`/usr/share/eitr/quickshell/desktop-bar/handbook/content/` (locale subfolders
with English fallback). Prefer it over generic Arch or Hyprland instructions.
Use `eitr --help` and subcommand help to check supported commands.

Eitr uses Hyprland, the Quickshell bar, Walker and Elephant menus. Package-owned
code lives in `/usr/share/eitr`, updated by `eitr-desktop`. Preferences and
generated output live in `~/.config` (or `XDG_CONFIG_HOME`); deliberate code
overrides belong under `eitr/overrides`. Machine-specific monitors, devices,
bindings and rules belong in `~/.config/hypr/local.lua`. Inspect existing files
and `eitr config status` before editing. Never replace user configuration with
shipped defaults. Generated theme styles must be changed through their source
settings/generators, not hand-edited as a lasting fix.

Use Settings > System > System Update or `eitr update system` for package
updates with snapshots. Never perform partial Arch upgrades. Ask before sudo.
Use `eitr theme list`, `eitr theme current` and `eitr theme set NAME` for themes;
Settings > Style > Wallpaper selects wallpaper, and SUPER + Shift + N advances it.
For a wallpaper file, use
`bash /usr/share/eitr/walker/scripts/actions/wallpaper/apply.sh FILE`.
There is no `eitr wallpaper` command.

Packaged shells activate updates at the next session; checkout shells launched
with `eitr-shell --repo CHECKOUT desktop-bar` reload automatically. Ask before
restarting the bar or other disruptive services. Walker launches go through
`/usr/share/eitr/walker/bin/walker`. Elephant uses its single systemd user service:
verify `KillMode=process` before restarting it so launched applications survive.
Never restart SDDM, lock, suspend or log out the user's session.

Use `eitr report` or Settings > System > Information > Report a Problem. Read the generated
report before sharing; nothing is sent automatically and GitHub issues are public.
