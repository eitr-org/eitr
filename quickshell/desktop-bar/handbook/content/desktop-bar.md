# Desktop bar and workspaces

<!-- eitr-figure: bar-anatomy -->

The Full bar. The Eitr logo opens Control Center; Overview, the workspace markers, AI Usage, Hardware and Idle Lock follow it. The date and time stay centered, with media before them and the weather after them. **Show Icons** reveals or hides the status icons on the right; Notifications come last.

Plugin bar items can appear after Idle Lock, before the clock, after the clock or in the status group. Choose a position in Settings > Plugins > the plugin > On the bar. The limits are four after Idle Lock, two on each side of the clock and eight in status, in placement order; extra items stay hidden in their chosen position. Centered and Dynamic reveal them while expanded; Tabs and Islands include them; Drop hides bar plugin items. The clock stays screen-centred. World clock is an optional official plugin and follows the bar's 12/24-hour preference.

Weather is an official, built-in plugin, installed by default after the clock. Remove it in Eitr Store > Plugins > Installed to hide weather everywhere, including Drop's home page. It stays removed after updates; install it again from Discover using the bundled copy, with no download. Its city search remains temporary for the session.

In Settings > Windows, Window layout and Monitors use two-button choices. Number of workspaces and Always show use dropdown lists; Always show offers 2 up to the current workspace count. Descriptions below each setting explain its effect, including the selected window layout and scrolling options.

## Updates

The updates icon, before Notifications, checks shortly after login and every six hours. Click it to run System Update; right-click to check again. A successful System Update marks it up to date until the next check, without starting another check immediately. Offline or failed checks show an unavailable state, never a false “up to date”. The check uses a private package database and does not upgrade packages.

## Change the bar layout

- Double-left-click **empty bar space** to cycle Theme Color → Blur → Website (new
  installations start with Theme Color). Website uses the Eitr website's colors,
  light or dark with the theme.
- Double-right-click empty space to cycle Full → Centered → Tabs → Islands → Dynamic → Drop → Full.
- Drag empty space toward the top, bottom, left or right to move the bar. Left and right bars are as thin as top and bottom ones: the clock shows the hour over the minutes with a calendar icon, and the weather shows its icon; hover them for the date and temperature.
- **Clock** under Settings > Desktop Bar shows 12-hour time with AM/PM (the default) or 24-hour time, on every bar edge.
- The same settings are under **Settings > Desktop Bar**, in its Layout, Look and Behaviour tabs.
- **Displays** (Show on) puts the bar on the main display only, the default, or
  on every display. With a bar on every display, each one marks the workspace
  shown on its own screen, shortcuts such as SUPER + I open on the display you
  are using, and notifications pop up on the main display only. Choose the
  main display in the Display panel.

<!-- eitr-figure: bar-layouts -->

The six layouts in the order double-right-click cycles them. At rest, Centered shows only the clock, Dynamic three small islands and Drop a single time pill; Centered and Dynamic unfold on hover.

Choose a layout in Settings > Desktop Bar. All six work on every screen edge.

| Layout | What to expect |
| :--- | :--- |
| Full | Full keeps the whole bar at the edge. Panels join it. |
| Centered | Centered shows the clock until hovered. Use the pin, or Keep expanded under Settings > Desktop Bar (also in Walker), to keep it expanded; panels float beside it. |
| Tabs | Tabs uses three tabs joined by a thin strip. Status icons and the weather stay visible. |
| Islands | Islands gives each group its own pill, with every status icon always shown. Opening a panel expands its pill and moves neighbouring groups aside. |
| Dynamic | Dynamic starts with three islands: logo, clock and network/battery, plus a media island between the logo and the clock while something plays. Hover one to expand it; opening a panel grows that island into the panel. |
| Drop | Drop shows only the time in one pill at the centre of the edge. Click it to grow its dashboard; right-click goes straight to the quick controls. With auto-hide, nothing stays on screen until a drop falls from the edge and swells into the pill. |

**Island style** (Settings > Desktop Bar > Layout, or Walker > Settings > Desktop > Desktop Bar > Island style) chooses how Islands, Dynamic and Drop meet the screen edge: Floating keeps the pills half the outer gap off the edge; Attached puts them against it, square on the edge side with straight sides, and their panels grow from the edge too. **Side style** chooses how Tabs and Centered meet the edge: 45° slopes, or straight sides (straight Tabs also drop the thin strip between the tabs).

## Drop's dashboard

Click Drop's time pill and the pill itself grows into a dashboard. Drag a page sideways (right goes forward, left back, both wrap), or use the arrow keys or horizontal scrolling. Esc or a click outside closes it. Nothing on it opens another panel: details open in place with a back arrow.

| Page | What it holds |
| :--- | :--- |
| Calendar and weather | The weather beside the month. Click the weather for the full forecast and a city search; click a day for its plans and to add a reminder at a time that day. |
| Media | The cover ringed by bars that follow the music, the song, its lyrics, the controls and a progress bar. Shown while something plays. |
| OBS | Recording and streaming status with pause, stop and go live, a chapter mark, the recordings folder and OBS itself. Shown while OBS is open. |
| Quick controls | WiFi, Bluetooth, Sound and Microphone open their networks and devices in place; Airplane, Silence, Night Light, Idle Lock, Record and Settings; volume, microphone and (on laptops) brightness. |
| Timer and focus | A countdown, a stopwatch, or 25-minute focus sessions with 5-minute breaks. It keeps running with the dashboard closed and notifies you at the end. |
| Performance, AI Usage and Notifications | CPU, GPU, RAM and storage; each assistant's limits (click one for all of them); the notification list. |

In every layout the clock shows what is happening beside it, where the recording dot sits: a calendar mark when an event starts within ten minutes (click it for that day's plans) and a ring while a timer or focus session runs (click it for Control Center > Tools > Timer & Focus). A new notification rings the bar's bell twice; where the bell is hidden (Centered while collapsed, Dynamic at rest) a bell slides out beside the clock instead. A laptop's battery briefly replaces the time with its percentage in red at 15% and 5%; where the workspaces are hidden, so does the number of the workspace you switch to.

Around the time Drop's pill shows what is happening, making room only where needed. Before the time: a red dot while recording, a calendar mark when an event starts within ten minutes, a ring while a timer runs, a turning arrow while the bar checks for updates and the updates mark while their notification is up (click it for System Update), and a note while music plays (click it for Media). After it: a bell that rings twice for a new notification (click it for the list). Changing workspace briefly replaces the time with its number; a laptop's battery does the same in red at 15% and 5%. Drag the note to the right to turn the pill into one line of lyrics; drag either way, pause or stop to turn it back.

**Online lyrics** (Settings > Desktop Bar > Behaviour, or Walker > Settings > Desktop > Desktop Bar > Online lyrics) is off by default. When on, Drop looks up the playing song on LRCLIB (lrclib.net), sending its title, artist, album and length. Lyrics a player sends itself are always used first.

## Workspaces

Settings > Windows > Workspaces (also Walker > Settings > Desktop > Windows > Workspaces) selects **Monitors**, **Number of workspaces** (5–10, default 10) and **Always show** (2 up to the count, default 5). **Shared numbers**, the default, gives every monitor its own 1…N: SUPER+k switches all monitors together, and SUPER+Shift+k moves the window on its current monitor, and every monitor switches to that number with it. **Split across monitors** divides N evenly, with the main display first and the remainder assigned there first; other displays follow left to right, then by name. SUPER+k focuses the owning display. Keys above N do nothing. The marker floor is relative to each monitor’s range; higher markers appear through the current or highest occupied workspace, then disappear when no longer needed. Connecting or removing displays and changing Main display recomputes assignments without losing windows; windows move to the nearest valid number on their current display. One monitor keeps the same behavior in both modes.
Right-click a marker to choose Dots, Glyph, Numbers or Runes, with live examples.
All four choices fit in the popup on every bar edge without scrolling.
Runes is the default. The active marker uses the accent-colored glyph without a filled background.
Runes shows workspaces 1 to 10 as the first ten Elder Futhark runes (ᚠ ᚢ ᚦ ᚨ ᚱ
ᚲ ᚷ ᚹ ᚺ ᚾ).

**SUPER + 1–9/0** switches workspace; **SUPER + Shift + 1–9/0** moves a window.
**SUPER + Tab** opens Overview. Click a preview or use arrows and Enter;
1–9/0 switches directly. Only occupied numbered workspaces appear, and their
previews stay in memory. Escape/outside click closes Overview.

**SUPER + S** toggles the special workspace, which is separate from Overview.
**SUPER + Shift + Space** switches the bar's auto-hide on or off; if the bar was hidden from the Control Center, it brings it back first. Notifications keep working either way.

On empty desktop space, the wallpaper/theme mouse gestures are listed under
**Learn > Mouse Gestures**. Use the keyboard carousel shortcuts when in doubt.

The Audio/Mic control opens one panel with separate output and microphone sections. Streaming sits immediately before OBS. A switch in its header starts sharing, details follow, and setup or diagnostic actions are in the "…" menu. Icon buttons show their background on hover; panels refresh by themselves when they open, a refresh icon spins only while they load, and tooltips appear near the pointer. Switches and inset action buttons use compact shared sizes.

**Music Visualizer** opens cava with theme colours. Right-click the media equalizer to open the same visualizer; left-click still opens media details. Press **q** or **Esc** to close it. On existing desktops, a missing cava package is installed first.

**Auto-hide**, under Settings > Desktop Bar, slides the bar away after a short pointer-leave delay. Touch its screen edge to reveal it. It works on all four edges with Full, Centered, Tabs, Islands, Dynamic and Drop layouts; with Drop a drop in the bar's colour falls from the edge and swells into the time pill. A new notification brings the bar out until its popup closes. Open panels and popups, and dragging the bar, keep it visible; it hides again afterwards. While auto-hide is on, the bar reserves no window space: it slides over windows instead of moving them. The setting is saved independently of the centered-layout pin and is off by default on new installations.

**Reduce motion**, under Settings > Desktop Bar, makes panel unfolding and folding, Overview entrances, notification transitions and decorative bar animations instant. It is off by default and saved in `bar-settings.json`. Timers that refresh data, dismiss notifications or delay auto-hide keep their normal behavior.

Media style is saved in `bar-settings.json`: choose Bars (default, ten bars) or Line (a simple smooth audio wave) under Settings > Desktop Bar. The indicator precedes the playback controls, keeps a fixed size in every layout and rotates on left/right edges. Hover for the song name; left-click opens media details and right-click opens Music Visualizer. Drag it to the left for one line of lyrics in its place; drag the line either way to get it back. Paused playback settles the line flat. Reduce motion keeps live audio levels without easing and stops decorative fallback motion.

## Edge dock

Touch the screen edge opposite the bar to reveal the application dock. It unfolds from that edge, its straight sides meeting the edge, over windows without moving or resizing them and hides 350 ms after the pointer leaves, with the shared 320 ms motion (instant with Reduce motion). It appears on the main screen, or on every screen when Displays is set to all, and never reveals over a fullscreen window.

The dock shows pinned apps first, followed by other open applications in Hyprland’s window order. Each 36 px icon slot has a 6 px gap and uses the application’s desktop icon, with a glyph fallback; Eitr’s own task and menu terminals share one Eitr logo icon. Dots below an icon count its windows, up to three, and dim when none is on the current workspace of that screen.

Hover for its name and window count; icons near the pointer grow, the closest one most, and the dock lengthens to keep them inside, unless **Reduce motion** is on. Click to focus its most recently used window (including switching workspace); click again to move to its next window. Middle-click closes the most recent window.

Long lists scroll along the dock. The surface follows Blur/Theme Color and the corner preference.

**Dock** in **Settings > Desktop Bar** turns it off or on. The `dock` setting in `bar-settings.json` defaults to `"yes"`. There is no dock shortcut.

Pinned apps stay at full opacity with no dots when closed; click one to launch it in its own application scope. Right-click an icon for Keep in Dock / Remove from Dock, New Window (when a desktop entry is available), and Close or Close All Windows. Escape or a click outside dismisses the menu. Apps without a desktop entry cannot be pinned.

Drag icons along the dock to reorder pins. Drag a running app into the pinned section to keep it there, or drag a pin past that section to remove it. Other icons make room with a short animation (instant with Reduce motion); unpinned apps retain Hyprland’s window order. A thin divider separates pins from other running apps only when both sections contain apps. Menus and drags keep the dock revealed.

Pins are desktop-entry IDs stored in order in the machine-local `quickshell/desktop-bar/dock-pins.json` under `$XDG_CONFIG_HOME` (normally `~/.config`), written atomically. Fresh installs have no pins. Window matching uses desktop-entry IDs, StartupWMClass and application classes.

Blur strength is shared with terminals. Choose Gentle, Medium (default) or Strong under Desktop Bar in Walker or in Settings (SUPER + ,). See [Terminal and editors](handbook:terminal) for the global blur limitation and personal overrides.

Settings > Desktop Bar includes workspace markers (Dots, Glyph, Numbers and Runes). The Windows page keeps window effects and gaps.
