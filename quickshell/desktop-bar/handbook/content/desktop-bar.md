# Desktop bar and workspaces

The bar keeps the date and time centered. Its left side starts with the Eitr logo, which opens Control Center, then Overview,
workspace markers, AI Usage, Hardware and Idle Lock; its right side contains device/status
controls. Click **Show Icons** to reveal or hide that right-side group.

## Updates

The updates icon in the right-side group, before Notifications, checks for
package and AUR updates shortly after you log in and every six hours. When it
finds new updates, a notification offers to run System Update. It spins while checking,
then shows a check mark when the system is up to date, or an update icon whose
tooltip gives the number of updates and the download size. Click it to run
System Update; right-click it to check again. It checks again automatically when
System Update finishes. When offline, it shows up to date and checks again at
the next login. The check uses a private copy of the package databases, so it
never leaves the system partially upgraded.

## Position and appearance

- Double-left-click **empty bar space** to switch Blur/Theme Color (new
  installations start with Theme Color).
- Double-right-click empty space to cycle Full → Centered → Tabs → Islands → Full.
- Drag empty space toward the top, bottom, left or right to move the bar. Left and right bars are as thin as top and bottom ones: the clock shows the hour over the minutes with a calendar icon, and the weather shows its icon; hover them for the date and temperature.
- **Clock** under Style > Desktop Bar and Control Center > Style > Bar shows 12-hour time with AM/PM (the default) or 24-hour time, on every bar edge.
- The same settings are under **Style > Desktop Bar** and Control Center > Style.
- **Displays** (Show on) puts the bar on the main display only, the default, or
  on every display. With a bar on every display, each one marks the workspace
  shown on its own screen, shortcuts such as SUPER + , open on the display you
  are using, and notifications pop up on the main display only. Choose the
  main display in the Display panel.

Centered meets the screen edge with square edge ends and the same softly rounded 45° slopes as Tabs on both sides. These slopes rotate with the bar on all four edges and ignore the corner preference; its detached panels still follow that preference.

Centered mode shows the clock until you hover. Icons unfold in their usual
order. Each side fits its content while the clock stays at the screen center on every edge. The pin between media and the clock keeps the bar open; open panels
also keep it expanded. Full-bar panels join the bar; centered-bar panels sit
beside it. Both open and close with the same fluid animation.

Islands gives the logo, Overview/workspaces, AI Usage/Hardware/Idle Lock, clock, weather and status controls separate content-sized pills, preserving their order and Full’s icon spacing. Media and capture indicators get pills only while active. The clock stays exactly screen-centred; weather has its own pill beside it. Pills follow Square/Rounded/Extra Rounded, the bar colour/transparency and blur. Pills sit half of Hyprland’s live outer gap from the screen edge, with the full gap between neighbouring pills, on all four edges. The reserved window space includes the pill depth and that half gap; auto-hide reserves none. Gaps and rounded corners pass clicks through. Empty space on each pill supports the usual double-click and drag gestures. Panels use Tabs’ detached rounded surfaces at Full’s positions, with the live inter-window gap and 320 ms reveal. The status group retains Full’s manual show/hide toggle.

Tabs uses a continuous 7 px strip and three content-sized tabs for the left, centre and right groups. Tabs retain the full bar depth (30 px horizontally), fixed trapezoid joins with straight 45° slopes outside the tab padding. The clock stays exactly screen-centred, including with media visible. Panels float beside the bar on detached rounded surfaces, aligned left, centre or right like Full and inset from screen edges by the outer gap, with the live Hyprland inter-window gap and the same 320 ms reveal as Centered. Gaps pass clicks through; the full tab depth is reserved for windows. Double-right-click cycles Full → Centered → Tabs → Islands → Full. The slopes have subtly softened bends and do not follow the corner preference; screen-edge ends stay square and filled. Tabs always shows all right-side controls without a show/hide arrow. Weather is hidden until the centre tab is hovered, then slides out after the fixed clock in 320 ms; it retracts after a short hover delay and stays visible while its panel is open. Only the trailing side grows, along the bar axis on every edge, with 4 px after the last visible item.

## Workspaces

The bar starts with 1–5 and expands through the current/highest occupied
workspace, up to 10. Empty higher markers disappear when no longer needed.
Right-click a marker to choose Dots, Glyph, Numbers or Runes, with live examples.
Runes is the default. The active marker uses the accent-colored glyph without a filled background.
Runes shows workspaces 1 to 10 as the first ten Elder Futhark runes (ᚠ ᚢ ᚦ ᚨ ᚱ
ᚲ ᚷ ᚹ ᚺ ᚾ).

**SUPER + 1–9/0** switches workspace; **SUPER + Shift + 1–9/0** moves a window.
**SUPER + Tab** opens Overview. Click a preview or use arrows and Enter;
1–9/0 switches directly. Only occupied numbered workspaces appear, and their
previews stay in memory. Escape/outside click closes Overview.

**SUPER + S** toggles the special workspace, which is separate from Overview.
**SUPER + Shift + Space** hides/shows the bar, not the notification service.

On empty desktop space, the wallpaper/theme mouse gestures are listed under
**Learn > Mouse Gestures**. Use the keyboard carousel shortcuts when in doubt.

The Audio/Mic control opens one panel with separate output and microphone sections. Tailscale and Streaming sit immediately before OBS. A switch in their header connects Tailscale or starts sharing, details and devices follow, and setup or diagnostic actions are in the "…" menu. Icon buttons show their background on hover; panels refresh by themselves when they open, a refresh icon spins only while they load, and tooltips appear near the pointer. Switches and inset action buttons use compact shared sizes.

**Music Visualizer** in **Main > Tools** opens cava with theme colours. Right-click the media equalizer to open the same visualizer; left-click still opens media details. Press **q** or **Esc** to close it. On existing desktops, a missing cava package is installed first.

**Auto-hide**, under Style > Desktop Bar and Control Center > Style, slides the bar away after a short pointer-leave delay. Touch its screen edge to reveal it. It works on all four edges with Full, Centered, Tabs and Islands layouts. Open panels and popups, and dragging the bar, keep it visible; it hides again afterwards. While auto-hide is on, the bar reserves no window space: it slides over windows instead of moving them. The setting is saved independently of the centered-layout pin and is off by default on new installations.

**Reduce motion**, under Style > Desktop Bar and Control Center > Style > Bar, makes panel unfolding and folding, Overview entrances, notification transitions and decorative bar animations instant. It is off by default and saved in `bar-settings.json`. Timers that refresh data, dismiss notifications or delay auto-hide keep their normal behavior.

Media style is saved in `bar-settings.json`: choose Bars (default, eight bars) or Line (a simple smooth audio wave) under Style > Desktop Bar or Control Center > Style > Bar. The indicator precedes the playback controls, keeps a fixed size in every layout and rotates on left/right edges. Hover for the song name; left-click opens media details and right-click opens Music Visualizer. Paused playback settles the line flat. Reduce motion keeps live audio levels without easing and stops decorative fallback motion.

## Edge dock

Touch the screen edge opposite the bar to reveal the application dock. It unfolds from that edge, its straight sides meeting the edge, over windows without moving or resizing them and hides 350 ms after the pointer leaves, with the shared 320 ms motion (instant with Reduce motion). It appears on the main screen, or on every screen when Displays is set to all, and never reveals over a fullscreen window.

The dock shows pinned apps first, followed by other open applications in Hyprland’s window order. Each 36 px icon slot has a 6 px gap and uses the application’s desktop icon, with a glyph fallback; Eitr’s own task and menu terminals share one Eitr logo icon. Dots below an icon count its windows, up to three, and dim when none is on the current workspace of that screen. Hover for its name and window count. Click to focus its most recently used window (including switching workspace); click again to move to its next window. Middle-click closes the most recent window. Long lists scroll along the dock. The surface follows Blur/Theme Color and the corner preference.

**Dock** in **Style > Desktop Bar** and **Control Center > Style > Bar** turns it off or on. The `dock` setting in `bar-settings.json` defaults to `"yes"`. There is no dock shortcut.

Pinned apps stay at full opacity with no dots when closed; click one to launch it in its own application scope. Right-click an icon for Keep in Dock / Remove from Dock, New Window (when a desktop entry is available), and Close or Close All Windows. Escape or a click outside dismisses the menu. Apps without a desktop entry cannot be pinned.

Drag icons along the dock to reorder pins. Drag a running app into the pinned section to keep it there, or drag a pin past that section to remove it. Other icons make room with a short animation (instant with Reduce motion); unpinned apps retain Hyprland’s window order. A thin divider separates pins from other running apps only when both sections contain apps. Menus and drags keep the dock revealed.

Pins are desktop-entry IDs stored in order in the machine-local `quickshell/desktop-bar/dock-pins.json` under `$XDG_CONFIG_HOME` (normally `~/.config`), written atomically. Fresh installs have no pins. Window matching uses desktop-entry IDs, StartupWMClass and application classes.
