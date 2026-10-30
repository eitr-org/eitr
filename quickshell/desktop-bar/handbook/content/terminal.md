# Terminal and editors

**SUPER + Enter** opens your selected terminal (Kitty by default). **SUPER + Ctrl + Enter** opens/attaches the main
tmux session. **SUPER + P** fuzzy-finds files; **SUPER + Ctrl + P** searches file
contents. Learn > Cmux Commands, Tmux Commands and LazyVim Commands are
searchable references; selecting a command copies it, rather than executing it.

Kitty shows a short cursor trail on jumps of at least two cells, such as
Enter, Home/End and moving between words. It starts after the cursor has rested
for 3 ms and fades in 0.05–0.15 seconds. To customize it, set `cursor_trail`,
`cursor_trail_decay` or `cursor_trail_start_threshold` in
`~/.config/kitty/local.conf`; `cursor_trail 0` disables it. Personal options
override the packaged defaults and survive theme changes.

### Cursor Fire

**Style > Terminal > Cursor Fire** offers **Disabled** (the default) and
**Enabled**. Enabled selects Kitty's built-in `cursor-trail-blaze` effect on
cursor movements, with no typing-speed detection. Disabled returns to the
normal configured fast trail and any personal shader selection.

The effect needs Kitty 0.49+ and `shader-slang`, included in Eitr's desktop
dependencies. Enabling validates the built-in shader before saving or reloading
Kitty. The machine-local preference is `~/.config/eitr/terminal.json`; the helper
writes `kitty/cursor-fire.conf`, included last by Kitty's user loader. While
enabled, it selects the fire shader and lowers the movement threshold to one
cell. Fonts, themes and personal config files remain intact.

## Choosing your terminal

**Style > Terminal** in Walker and **Control Center > Style > Terminal** offer
**Kitty** (the default) and **Ghostty**. The machine-local `terminal` field in
`~/.config/eitr/terminal.json` controls Super+Enter, tmux, user terminal sessions,
AI/project terminals and Walker's open-in-terminal actions. If Ghostty is missing,
choosing it opens the normal official-package Install flow: Enter installs,
Esc cancels. Kitty remains selected until installation succeeds. If Ghostty is
later removed, launches fall back to Kitty. Ghostty is optional and is not in
the ISO payload.

Theme switches regenerate `~/.config/ghostty/eitr.conf` with the theme's sixteen
ANSI colours, background, foreground, selection and text cursor colours. Font
changes regenerate the selected family; the default size is 10 points. Ghostty
runs the same zsh and prompt, with 75% opacity and zero ordinary-window padding.
Hyprland supplies blur and the same normal window decorations/rules. The pointer
family, size and Auto/Light/Dark choice in `eitr/cursor.json` continue through
GTK and the compositor; they are separate from the terminal's text cursor.

Ghostty loads the generated file through the Eitr launcher. Put personal settings
such as `font-size = 12` or `cursor-style = bar` in
`~/.config/ghostty/local.conf`, loaded last and preserved on theme changes.
Running Ghostty sessions receive their supported reload signal after theme/font
changes. Some options apply only to new windows. Kitty's cursor trail and
Cursor Fire are Kitty-only; Ghostty has no equivalent built-in blaze setting.

Eitr's task, menu, status and setup terminals always use Kitty, including
`eitr-menu-terminal`, `eitr-plugins` and `fif-terminal`: their `--class`, `--hold`,
`--title` options and floating-window rules remain Kitty-specific. They do not
change when selecting Ghostty.


## The eitr command

`eitr` gathers Eitr's tools in one command; run it alone for the list. It runs the
same scripts as the menus, so both always behave alike.

```
eitr update                  # System Update: snapshot, packages, AUR, Flatpak
eitr update aur              # only AUR packages, without a snapshot
eitr theme list              # installed themes, the current one marked *
eitr theme set "Eitr" # switch theme
eitr firewall on             # also: off, status
eitr snapshots               # recovery snapshots
eitr snapshots changes       # what each update changed
eitr reset keep-files        # factory reset, after the usual two warnings
eitr report                  # prepare a problem report
eitr handbook troubleshooting
eitr version
eitr about
```

`eitr about` opens About Eitr, or focuses its window if it is already open.

`eitr config` and `eitr git` pass their arguments to `eitr-config` and `eitr-git`.
Each command has `--help`.

## Your own hooks

A hook is a small script of yours that Eitr runs at a certain moment, so you can
add to what it does without changing Eitr itself. Put an executable file named
after the moment in `~/.config/eitr/hooks/`:

| File | Runs | Gets |
| --- | --- | --- |
| `post-update` | after System Update or a pacman/AUR update | `system`, `pacman`, `yay` or `full` |
| `theme-set` | after switching theme | the theme's folder name |
| `battery-low` | once each time the battery drops to 15% | the percentage |
| `post-boot` | at the first login after each start | nothing |

For example, to recolor Spotify (with Spicetify) whenever the theme changes,
create `~/.config/eitr/hooks/theme-set`:

```
#!/usr/bin/env bash
spicetify config color_scheme "$1" && spicetify apply
```

then make it executable with `chmod +x ~/.config/eitr/hooks/theme-set`. Each hook
gets up to 60 seconds; its output and any failure go to
`~/.local/state/eitr/hooks.log`, and a failing hook never stops the update or
theme switch. `eitr hook list` shows which hooks exist, and
`eitr hook run theme-set eitr` tries one. Updates never touch this folder.

## cmux TUI

Run `cmux` in Kitty, or `cmux --session work` for a named session. cmux TUI
is an optional workflow alongside tmux, not a replacement for Kitty or its
existing shortcuts. Fresh EITR installs include a pinned official binary at
`/usr/bin/cmux`; existing per-user installs may take precedence on PATH.
Use `command -v cmux` to see which one is selected. `less` is included for
reading terminal output and text files.

The default prefix is **Ctrl-b**: release it, then press the next key.

| Shortcut | Action |
| --- | --- |
| Ctrl-b ? | Show current shortcuts |
| Ctrl-b W | Create workspace |
| Ctrl-b c | Create screen |
| Ctrl-b % / Ctrl-b " | Split right / down |
| Ctrl-b t | New terminal tab |
| Ctrl-b h/j/k/l | Focus left/down/up/right |
| Ctrl-b s | Show/hide sidebar |
| Ctrl-b d | Quit locally or detach from a server |

For a session that continues without the UI, run
`cmux --headless --session work`, then `cmux attach --session work` to attach.
Browser tabs require Chrome/Chromium. Closing tabs, panes or workspaces may
affect running tasks; check before using those actions. Learn > Cmux Commands
includes session commands, navigation, mouse controls and closing shortcuts.
Defaults can change or be overridden; **Ctrl-b ?** is the live reference.

## Task terminals

Terminals that menus open, and the update and problem-report notifications'
terminals, float centered above your windows and use the theme's solid background. AI assistant sessions and LazyVim projects (Development menu)
open as ordinary tiled windows, like terminals you open yourself, with the
translucent background.
Ordinary terminals are interactive and unbranded. Installer/update/setup
terminals show the themed rune-style EITR banner; successful tasks normally
close, and failures stay open until dismissed. Informational reports may stay
open intentionally. Restarting Elephant is not supposed to close launched apps:
apps and terminals opened from menus, key bindings and bar buttons use separate
application scopes in a uwsm session. Without uwsm they launch directly. Elephant
keeps process-only stopping for desktop helpers and fallback launches.

Press **Esc** to close waiting task, account, report and About terminals. Enter remains for answers and confirmations, including acknowledging a recovery key and powering off the installer.

## Shell history

`history` lists recent commands. In zsh, inspect the actual history path with:

```sh
printf '%s\n' "$HISTFILE"
```

To open it in Neovim:

```sh
nvim "$HISTFILE"
```

History may contain tokens or credentials; do not copy it into a bug report.
Close other shells before manually editing it, because running shells can
write their in-memory history back. Extended zsh history can include timestamp
metadata and multiline commands; remove the whole relevant entry, not an
arbitrary fragment. Back it up privately if you need an undo.

## Editor appearance

Theme changes update generated VS Code and LazyVim preferences. Supported live
LazyVim sessions refresh without reopening. User overrides/plugins can choose
their own colors; verify their configuration if an editor does not follow the
desktop. Default-font integration is applied only where the app supports it.
