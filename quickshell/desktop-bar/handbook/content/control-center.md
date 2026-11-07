# Control Center

Settings and the bar panels share choice controls. Short choices use segments; longer lists open as floating, scrollable dropdowns. Switches keep their existing actions. Gold labels and carved lettering belong to the Settings family of windows: Settings, the Handbook and Themes & Plugins.

Dropdown lists support type-ahead while the selector or list has keyboard focus. Type a label prefix to highlight its first match; accents and case are ignored. Keys typed within 800 ms build the prefix; after a pause a new prefix starts. Repeating one letter cycles its matches. Enter applies the highlighted choice and Escape cancels. Lists show at most eight rows and scroll. They open below the field, including beyond a bar panel’s edge, or upward when the screen has more room above.

**SUPER + ,** opens Settings with **System**, combining your profile and system overview. Themes and Plugins open in their own catalog window. Desktop and Devices pages show their shared controls inline; the Control Center remains available through **SUPER + I**.

## Settings

Settings groups its pages under Overview, Devices, Desktop, Apps & Keys,
Accounts & Security, and System. Rune captions and a sliding gold marker help
navigation; search matches page names and descriptions. Every page has a
breadcrumb, carved title and description. Bordered cards group related rows.
The opaque surface supports light and dark palettes. The Handbook and Themes & Plugins use the same frame, sidebar, page header and cards, and follow the same palette choice.

Connections has **Wi-Fi** (including the reboot-only backend choice) and **Bluetooth** tabs. Displays separates **Displays** and **Night Light**; Appearance separates **Theme & Wallpaper**, **Fonts & Cursor** and **Terminal**. Use Left/Right on a focused tab to switch. Search opens the matching tab. IPC accepts `settings show connections/bluetooth`; `network` remains an alias for Connections.

Picture cards preview bar layouts, position, appearance, media style, window gaps and corners using the current colours and geometry. Lockscreen cards use shipped preview images; the native Hyprlock fallback uses a sketch. Cursor family and size show an available theme sample. Select cards with a click, Space or Enter. Reduce motion disables decorative hover transitions.

Appearance > Theme & Wallpaper > **Settings colours** selects **Theme colours** or **Eitr website** for Settings, the Handbook and Themes & Plugins. The website choice follows the light or dark variant of the Eitr website palette. This independent preference is stored in `eitr/settings-app.json` under the configuration directory and defaults to theme colours. IPC also accepts `settings palette theme` or `settings palette website`. It does not change the desktop theme or bar appearance.

Dropdowns retain theme, fonts, cursor, terminal, workspace style, default apps and keyboard layout choices. Switches control booleans; sliders adjust sizes and levels. Wallpaper keeps its thumbnail grid. Sound, Connections and Displays reuse the existing device controls.

System shows an overview with your profile picture, CPU/GPU/RAM usage, main display, uptime, Eitr version, update channel and theme palette. Hardware refreshes only while this page is visible. The large artwork currently shows your wallpaper. Network transfer rates are not available from the shared data service.

**SUPER + F2**, Appearance’s **More themes**, the theme carousel’s **+**, and the catalog actions open the separate **Themes & Plugins** window with its own sidebar and close button. **SUPER + I** opens the Control Center. Settings stays open when you click outside; use its close button, Escape or the compositor’s close shortcut.

Press **SUPER + I** to toggle the Control Center. It opens from the bar's current
edge and closes on Escape or an outside click. With a Full bar on the left or
right, it starts at the top of the screen, with content padded inside the joined
surface. Closing returns it to General.

Its pages are General, Plugins and Tools. The gear button below them, **All settings**, closes the Control Center and opens Settings, which holds the appearance, bar, device, keyboard, display and system choices. Folding sections usually start closed; click
a section's title to open or close it, remembered until you log out. Where the bar has its own panel, such as OBS, WiFi or Bluetooth, the Control Center opens it.

## General

- **Connectivity:** WiFi and Bluetooth power toggles, plus Airplane mode.
- **Quick Actions:** automatic Idle Lock, Crash Notifications, Do Not Disturb, Game Mode (effects, blur
  and popups off and the performance profile on, until you turn it off) and Night
  Light. A toggle that is on fills with the theme accent. Below them, Hide Bar
  (SUPER+Shift+Space brings it back) and Screensaver run once.
- **Sound:** volume and microphone gain/mute, and two optional switches, off by
  default: **Notification sounds** (a chime, a different one for urgent
  notifications; low-priority ones stay silent) and, on PCs with a battery,
  **Charger sounds** when the charger connects or disconnects. Neither plays during
  Do Not Disturb or Game Mode.
- **Display:** brightness, on laptops with a built-in screen.
- **Media:** cover, artist, playback controls and seeking when supported.
- **Power:** Lock, plus **Power…**, which unfolds Logout, Suspend, Reboot and Shutdown.

Airplane mode remembers which radios it blocked and restores only those.
Do Not Disturb suppresses popups without clearing notification history.
Idle Lock is not the same as preventing sleep; be mindful of screen privacy.

## Tools

Screenshots (selection, full screen, window, or a selection straight to the
clipboard), recording (the OBS controls, Record, Record + Audio and Stop), OCR,
QR codes, the color picker, Transcode, reminders and LocalSend sharing. The panel
closes before a selection or recording starts.

## Quick chat

The chat icon beside the page tabs opens a disposable conversation with your default assistant, chosen in Development > AI. It is hidden without a default or when organization policy disables assistants. Enter sends; Shift+Enter inserts a line break. Escape or Back returns to the pages. New chat, leaving chat, or closing the Control Center clears all messages and cancels a pending answer.

Replies support selectable Markdown and Copy. The conversation stays in memory; Eitr writes no chat history or logs. The line below the input names the cloud provider, or says Ratatoskr runs on this PC. Cloud providers receive your messages and earlier turns. Each message also carries only Eitr version/channel, kernel, CPU/GPU/RAM and theme, as untrusted context. No usernames, hostnames, files, emails, WiFi names, window titles or clipboard are collected. The assistant uses the read-only headless path with the selected account; it cannot make system changes. Failures appear inline.

## Plugins

**Settings > Style > Themes & Plugins** in Walker, **More themes** on the Settings Appearance page or **SUPER + F2** opens the Themes & Plugins window. Its Plugins group lists installed, official and community plugins, installs and updates them after a review inside the window, checks for updates, and removes installed plugins after confirmation. The terminal flows below remain available.

**Control Center > Plugins** shows a compact row for each installed plugin: icon, name and enable switch. Select a row to see its author, version, description, Update/Remove actions, widgets, bar items and Preview. Use Back or Escape to return to the list. Enable/Disable preserves placements and stops or restores services, Walker rows, hooks and visuals; the CLI is `eitr plugin enable ID` or `eitr plugin disable ID`. Add Plugins, Update and Remove open the reviewed terminal flows; removal asks for confirmation. General keeps only plugin tiles. Visual failures have an independent Re-enable action.

Add Plugins also accepts repositories containing several plugins. A root `eitr-plugins.json` index lists their IDs and folders, each with its own `eitr-plugin.json`. Select one or more entries by name, description and icon, then review each plugin separately. Declining one does not approve the others. Selected plugins share one downloaded repository snapshot and are pinned individually to its exact commit; updating one leaves the others at their approved commits. The Plugins details show the repository URL and plugin folder. A single root `eitr-plugin.json` continues to work unchanged.

System Update only checks for new plugin commits, even when system packages are current, and prints a count and where to update. It never reviews or updates plugins; network errors are silently ignored. Run **Update Plugins** from **Control Center > Plugins** (next to Add Plugins) or **Plugins > Update Plugins**, or use `eitr plugin update`. A small ↑ mark in the plugin row and “Update available” in its details reflect the last check for its approved commit. The separate action keeps the existing per-plugin diffs, risk flags and confirmations.

The Plugins list shows “This plugin has errors” and its first message. Select the plugin and choose View error details to read more; use the enable switch to disable it in one click. Errors are caught only when they name a file in that plugin’s folder. Plugins run with the desktop’s permissions, so install only plugins you trust.

## Profile pictures

Open Settings > User (or click your picture on Settings' System overview) and choose Change picture. The system file chooser floats centred above Settings, showing only images; pick one and the crop editor opens in a sheet over Settings. Drag the round preview to move the image; use the wheel, slider or +/− to zoom from 1× to 4×, and arrow keys to move. Save (or Enter) applies the crop; Cancel or Escape closes the sheet without applying it. Remove, beside Change picture, clears the picture.

Pictures appear as circles in Control Center, the lockscreen and the login screen. Control Center only displays the picture at the top of its navigation; without one it shows nothing there, and neither do the lockscreen and login screen. Settings shows your name’s initial on a theme-accent circle instead. Eitr accepts PNG, JPEG, WebP, GIF (first frame) and BMP up to 40 MB and 12000 pixels per side. It applies orientation, strips metadata and saves a 512×512 PNG at `~/.face`, then updates AccountsService for SDDM. If that update fails, the saved picture still works on the lockscreen; the sheet or CLI reports the login-screen error.

## More Settings pages

Keybinds lists the complete Learn shortcut reference with a search field. Default apps chooses installed handlers for the browser, files, text, images, video, music, mail and PDF; Terminal uses the same preference as Appearance > Terminal. User shows your picture and display name with Change picture and Remove. Git & Cloud shows saved identities, folder rules and provider contexts; its buttons open the existing Walker account flows. Security keeps privileged changes in their existing confirmation flows. Updates shows the channel and pending packages; System Update opens the existing update flow. Check This PC runs read-only diagnostics only when pressed. About shows release, kernel, hardware, licence and project links. Each page scrolls to its final row and links to the Handbook.
