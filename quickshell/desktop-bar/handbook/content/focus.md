# Focus

![Focus tab strip with example windows and two joined panes.](assets/focus-strip.png)

Focus replaces the desktop bar with a 28 px tab strip at the top of every monitor.
Open **Style > Focus** or **Control Center > Style > Focus**, or run
`eitr focus on`. `eitr focus status` prints `on` or `off` without contacting
Hyprland. `eitr focus off` restores the normal desktop, including its bar layout,
effects and shortcuts. There is no dedicated toggle shortcut.

The preference lives in `~/.config/eitr/focus.json` (under `$XDG_CONFIG_HOME`
when set). Reboots, package updates and theme changes preserve it. Normal bar
preferences are kept separately and are never replaced by this preset.

## Tabs and panes

Existing windows, including floating windows and windows on the special workspace,
are gathered into native Hyprland groups. One group fills the available screen
below the strip. Gaps, borders, rounded window corners, blur, shadows and animations
are disabled. The strip follows the theme, uses square edges like the Tabs layout,
and shows only window titles, a clock and network/battery status. Battery status
appears only with a system battery. Long titles are shortened; crowded tabs scroll.
A highlighted tab identifies the focused window. Accent lines join the visible
split panes on the strip. Application popups may keep their own internal styling.

- **SUPER + 1–9** selects tab 1–9 on the focused monitor.
- **SUPER + Tab / SUPER + Shift + Tab** selects the next/previous tab.
- **SUPER + backslash** splits the focused group with its next tab side by side.
- **SUPER + minus** stacks that next tab below it.
- **SUPER + H/J/K/L** focuses the left/down/up/right pane.
- **SUPER + Shift + H/J/K/L** resizes narrower/taller/shorter/wider, as on the normal desktop.
- **SUPER + Shift + backslash** returns the focused window to a full-screen tab group, folding all split panes back into tabs.

A split needs another tab in the focused group. At most four panes are allowed:
two panes can be side by side or stacked; three or four use a 2×2 grid (the third
pane fills the bottom row until a fourth is added). Resize adjusts the grid's
shared dividers. The return shortcut restores one full-screen tab group in one press.
Tab numbers follow compositor window order, also used by the strip. The normal
workspace, floating, move-window and bar-visibility shortcuts are inactive;
launchers, close-window, Control Center and Handbook shortcuts remain available.
Learn > Shortcuts shows the Focus keys while the preset is on.

## Monitors and recovery

Each monitor has its own windows, strip and up to four panes. Tab shortcuts act
on the focused monitor; pane focus can cross a monitor boundary when no pane is
available in that direction. Connecting a monitor creates its strip; after a
disconnection, Hyprland moves its windows to an available monitor and Focus
gathers them there. Normal bar display selection does not limit Focus strips.

Turning Focus off ungroups windows and spreads them over normal numbered
workspaces, two per workspace, keeping their current monitors. Earlier workspace
positions, floating geometry and application fullscreen states are not retained.
An empty desktop and repeated on/off commands are supported. Native groups remain
when the strip process crashes; keyboard navigation still works. Run
`eitr focus off` from a terminal to recover even without the strip. A Hyprland
reload reapplies the saved preset and gathers new windows without dismantling
existing splits; divider sizes and the two-pane orientation reset on reload.
If a command fails, it reports the error; retry `eitr focus off` after Hyprland
is reachable. Closing a pane lets the native layout expand the remaining panes.
