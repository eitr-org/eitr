# Control Center

Press **SUPER + ,** to toggle the Control Center. It opens from the bar's current
edge and closes on Escape or an outside click. With a Full bar on the left or
right, it starts at the top of the screen, with content padded inside the joined
surface. Closing returns it to General.

Its five pages hold everything outside Development, Apps, Install, Learn and
Gaming, so most settings never need Walker. Folding sections usually start closed; click
a section's title to open or close it, remembered until you log out. Where the bar has its own panel (OBS, WiFi,
Bluetooth, Audio, Display, Hardware, AI Usage, Weather), the Control Center opens it.

## General

- **Connectivity:** WiFi and Bluetooth power toggles, plus Airplane mode.
- **Quick Actions:** automatic Idle Lock, Crash Notifications, Do Not Disturb, Game Mode (effects, blur
  and popups off and the performance profile on, until you turn it off) and Night
  Light. A toggle that is on fills with the theme accent. Below them, Hide Bar
  (SUPER+Shift+Space brings it back) and Screensaver run once.
- **Sound:** volume and microphone gain/mute.
- **Display:** brightness, on laptops with a built-in screen.
- **Media:** cover, artist, playback controls and seeking when supported.
- **Power:** Lock, plus **Power…**, which unfolds Logout, Suspend, Reboot and Shutdown.

Airplane mode remembers which radios it blocked and restores only those.
Do Not Disturb suppresses popups without clearing notification history.
Idle Lock is not the same as preventing sleep; be mindful of screen privacy.

## Style

Style groups its settings into Theme & Wallpaper, Corners, Bar, Workspaces, Lockscreen, Cursor and Terminal. Every group starts folded; click its header to open or fold it, and the Control Center remembers that until you log out; its surface encloses all its options. Bar groups Layout, Position, Appearance, Show on, Clock, Media style and Behavior. Behavior contains Auto-hide, Dock and Reduce motion.

Theme and Wallpaper open their carousels; Fonts opens the font list. The
lockscreen design, cursor (family, size and color), bar appearance, layout,
edge and displays, workspace markers, corners and Kitty's Cursor Fire change right in the
panel and share their preferences with Walker.

Terminal offers Kitty (default) and optional Ghostty; Eitr utility terminals stay on Kitty. See [Terminal and editors](terminal.md) for installation and configuration.

## Tools

Screenshots (selection, full screen, window, or a selection straight to the
clipboard), recording (the OBS controls, Record, Record + Audio and Stop), OCR,
QR codes, the color picker, Transcode, reminders and LocalSend sharing. The panel
closes before a selection or recording starts.

## Settings

- **Devices:** Audio, Microphone, Display (resolution, refresh rate and scale),
  Bluetooth and WiFi panels, Lighting, and the battery charge limit on laptops.
- **Keyboard:** layouts can be selected, added and removed, with at least one kept.
- **Night Light & Main Display:** Night Light's mode and schedule (distinct
  from its manual switch) and the main display, which holds the bar.
- **Information:** About, Hardware, AI Usage, Weather and Report a Problem.
- **Updates:** the update channel, System Update, what each update changed, and
  Pacman-only or AUR-only updates.
- **Snapshots & Cleanup:** restore a file, home snapshots, recovery snapshots and
  their guide, Cleanup and Dotfiles.

Security settings, factory reset and the network backend stay in Walker > Settings,
behind their own confirmations.

## Language

**Settings > Language** shows the current language and follows the system locale.
Open the picker to choose a language or System default, then sign out and back
in to apply it. It changes only your user-session message locale, never the
system locale files. See the [Language guide](handbook:language).

## Quick chat

The chat icon beside the page tabs opens a disposable conversation with your default assistant, chosen in Development > AI. It is hidden without a default or when organization policy disables assistants. Enter sends; Shift+Enter inserts a line break. Escape or Back returns to the pages. New chat, leaving chat, or closing the Control Center clears all messages and cancels a pending answer.

Replies support selectable Markdown and Copy. The conversation stays in memory; Eitr writes no chat history or logs. The line below the input names the cloud provider, or says Ratatoskr runs on this PC. Cloud providers receive your messages and earlier turns. Each message also carries only Eitr version/channel, kernel, CPU/GPU/RAM and theme, as untrusted context. No usernames, hostnames, files, emails, WiFi names, window titles or clipboard are collected. The assistant uses the read-only headless path with the selected account; it cannot make system changes. Failures appear inline.

## Plugins

**Settings > Style > Themes & Plugins**, **Control Center > Style > Themes & Plugins** or **SUPER + F2** opens the catalog window. Its Plugins tab lists installed, official and community plugins, installs and updates them after a review inside the window, checks for updates, and removes installed plugins after confirmation. The terminal flows below remain available.

**Control Center > Plugins** shows a compact row for each installed plugin: icon, name and enable switch. Select a row to see its author, version, description, Update/Remove actions, widgets, bar items and Preview. Use Back or Escape to return to the list. Enable/Disable preserves placements and stops or restores services, Walker rows, hooks and visuals; the CLI is `eitr plugin enable ID` or `eitr plugin disable ID`. Add Plugins, Update and Remove open the reviewed terminal flows; removal asks for confirmation. General keeps only plugin tiles. Visual failures have an independent Re-enable action.

Add Plugins also accepts repositories containing several plugins. A root `eitr-plugins.json` index lists their IDs and folders, each with its own `eitr-plugin.json`. Select one or more entries by name, description and icon, then review each plugin separately. Declining one does not approve the others. Selected plugins share one downloaded repository snapshot and are pinned individually to its exact commit; updating one leaves the others at their approved commits. The Plugins details show the repository URL and plugin folder. A single root `eitr-plugin.json` continues to work unchanged.

System Update only checks for new plugin commits, even when system packages are current, and prints a count and where to update. It never reviews or updates plugins; network errors are silently ignored. Run **Update Plugins** from **Control Center > Plugins** (next to Add Plugins) or **Plugins > Update Plugins**, or use `eitr plugin update`. A small ↑ mark in the plugin row and “Update available” in its details reflect the last check for its approved commit. The separate action keeps the existing per-plugin diffs, risk flags and confirmations.

The Plugins list shows “This plugin has errors” and its first message. Select the plugin and choose View error details to read more; use the enable switch to disable it in one click. Errors are caught only when they name a file in that plugin’s folder. Plugins run with the desktop’s permissions, so install only plugins you trust.

## Profile pictures

Click the round avatar at the top of the Control Center navigation, or open Settings > Security > Users > Profile Picture. Choose Picture… shows your Pictures folder inside the sheet: click a folder to open it, ‹ or Backspace to go up, and click an image to choose it. Then drag the round preview to move the image; use the wheel, slider or +/− to zoom from 1× to 4×, and arrow keys to move. Save (or Enter) applies the crop; Cancel or Escape closes the sheet without applying a pending crop. Remove clears the picture.

Pictures appear as circles in Control Center, the lockscreen and the login screen. Without a picture, your name’s initial appears on a theme-accent circle. Eitr accepts PNG, JPEG, WebP, GIF (first frame) and BMP up to 40 MB and 12000 pixels per side. It applies orientation, strips metadata and saves a 512×512 PNG at `~/.face`, then updates AccountsService for SDDM. If that update fails, the saved picture still works on the lockscreen; the sheet or CLI reports the login-screen error.
