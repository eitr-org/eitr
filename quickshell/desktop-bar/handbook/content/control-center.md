# Control Center

Press **SUPER + I** to toggle the Control Center. It opens from the bar's current
edge and closes on Escape or an outside click. With a Full bar on the left or
right, it starts at the top of the screen, with content padded inside the joined
surface. Closing returns it to General.

Its pages are General, Plugins and Tools. The gear button below them, **All settings**, closes the Control Center and opens Settings, which holds the appearance, bar, device, keyboard, display and system choices. Folding sections usually start closed; click
a section's title to open or close it, remembered until you log out. Where the bar has its own panel, such as OBS, WiFi or Bluetooth, the Control Center opens it.

## General

<!-- eitr-figure: control-center -->

The General page. The buttons on the left switch between General, Plugins and Tools; the gear below them opens Settings. A toggle that is on fills with the theme accent.

- **Connectivity:** WiFi and Bluetooth power toggles, plus Airplane mode.
- **Quick Actions:** automatic Idle Lock, Do Not Disturb, Game Mode (effects, blur
  and popups off and the performance profile on, until you turn it off) and Night
  Light.
- **Screen:** Hide Bar (SUPER+Shift+Space brings it back) and Start Screensaver run once.
- **Sound:** volume and microphone gain/mute, and two optional switches, off by
  default: **Notification sounds** (a chime, a different one for urgent
  notifications; low-priority ones stay silent) and, on PCs with a battery,
  **Charger sounds** when the charger connects or disconnects. Neither plays during
  Do Not Disturb or Game Mode. Walker > Settings > Devices > Event Sounds offers
  the same switches.
- **Display:** brightness, on laptops with a built-in screen.
- **Media:** cover, artist, playback controls and seeking when supported.
- **Power:** Lock, plus **Power…**, which unfolds Logout, Suspend, Reboot and Shutdown.

Airplane mode remembers which radios it blocked and restores only those.
Do Not Disturb suppresses popups without clearing notification history.
Idle Lock is not the same as preventing sleep; be mindful of screen privacy.

## Tools

Timer & Focus (a countdown, a stopwatch, or focus sessions of 25 minutes with
5-minute breaks; a ring beside the clock shows it running and opens it), screenshots
(selection, full screen, window, or a selection straight to the clipboard), recording (the OBS controls, Record, Record + Audio and Stop), OCR,
QR codes, the color picker, Transcode, reminders and LocalSend sharing. The panel
closes before a selection or recording starts.

## Quick chat

Choose your default in Settings > AI Assistant.

The chat icon beside the page tabs opens a disposable conversation with your default assistant, chosen in Development > AI. It is hidden without a default or when organization policy disables assistants. Enter sends; Shift+Enter inserts a line break. Escape or Back returns to the pages. New chat, leaving chat, or closing the Control Center clears all messages and cancels a pending answer.

Replies support selectable Markdown and Copy. The conversation stays in memory; Eitr writes no chat history or logs. The line below the input names the cloud provider, or says Ratatoskr runs on this PC. Cloud providers receive your messages and earlier turns. The machine summary includes Eitr version/channel, kernel, CPU/GPU/RAM and theme, as untrusted context. No usernames, hostnames, files, emails, WiFi names, window titles or clipboard are collected. The assistant uses the read-only headless path with the selected account; it cannot make system changes. Failures appear inline.

The assistant also receives Eitr’s Handbook primer and relevant localized excerpts, a fixed list of installed desktop tools, and whether an HDR monitor is connected. These describe availability, not whether a service is configured. The assistant cannot run commands or change settings.

## Plugins

**Control Center > Plugins** shows a compact row for each installed plugin: icon, name and enable switch. Select a row to see its author, version, description, Update/Remove actions, widgets, bar items and Preview. Use Back or Escape to return to the list. Enable/Disable preserves placements and stops or restores services, Walker rows, hooks and visuals; the CLI is `eitr plugin enable ID` or `eitr plugin disable ID`. Add Plugins, Update and Remove open the reviewed terminal flows; removal asks for confirmation. General keeps only plugin tiles. Visual failures have an independent Re-enable action.

For installation, review and update safety, see [Apps & Installation](handbook:apps).

For Settings (**SUPER + ,**) and profile pictures, see [Settings](handbook:system).
