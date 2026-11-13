# Find a setting

Press **SUPER + ,** to open Settings. System is the overview, not a folder containing every setting.

Search the Settings sidebar for an individual setting, such as **Cursor size**, or a page. Results show the page and tab beneath the setting name. Use Up/Down and Enter, or click a result, to open its tab, scroll to the control and briefly highlight it. Escape clears the search first. With Reduce motion, the highlight appears and disappears without fading.

<!-- eitr-figure: settings-window -->

The Settings window has a searchable sidebar and cards for related controls. It stays open when you click outside. Close it with Escape, its close button or the normal close-window shortcut.

Panel footer links close the panel and open the matching Settings page. The Control Center’s All settings button does the same; use **SUPER + I** for quick controls. See [Control Center](handbook:control-center).

Choose Settings colours in Settings > Appearance > Theme & Wallpaper: Theme colours follows your desktop, while Eitr website uses the website palette. This affects Settings, the Handbook and Add-ons, not the desktop theme. Walker > Settings > Desktop > Appearance > Settings Colours opens this choice.

The separate Add-ons catalog opens with SUPER + F2 or More themes in Appearance.

## Choose a page

Use the page names below. See the linked chapters for instructions.

| Page | Read more |
| :--- | :--- |
| System | [System](handbook:information) |
| Displays — Displays, Night Light | [Displays](handbook:devices) |
| Sound | [Sound](handbook:devices) |
| Connections — Wi-Fi, Bluetooth | [Connections](handbook:connectivity) |
| Streaming | [Streaming](handbook:remote-access) |
| Input | [Input](handbook:devices) |
| Appearance — Theme & Wallpaper, Fonts & Cursor, Terminal | [Appearance](handbook:appearance) |
| Desktop Bar | [Desktop Bar](handbook:desktop-bar) |
| Windows | [Windows](handbook:appearance) |
| Lockscreen | [Lockscreen](handbook:appearance) |
| Notifications | [Notifications](handbook:information) |
| Focus | [Focus](handbook:focus) |
| AI Assistant | [AI Assistant](handbook:development) |
| Keybinds | [Keybinds](handbook:shortcuts) |
| Default apps | [Default apps](handbook:apps) |
| Users | [Users](handbook:security) |
| Security | [Security](handbook:security) |
| Updates | [Updates](handbook:maintenance) |
| Check This PC | [Check This PC](handbook:troubleshooting) |
| About | [About](handbook:information) |

## Change your profile picture

Open Settings > Users (or click your picture on Settings' System overview) and click your picture. The system file chooser floats centred above Settings, showing only images; pick one and the crop editor opens in a sheet over Settings. Drag the round preview to move the image; use the wheel, slider or +/− to zoom from 1× to 4×, and arrow keys to move. Save (or Enter) applies the crop; Cancel or Escape closes the sheet without applying it. The trash icon below your picture removes it after you confirm.

Pictures appear as circles in Control Center, the lockscreen and the login screen. Control Center only displays the picture at the top of its navigation; without one it shows nothing there, and neither do the lockscreen and login screen. Settings shows your name’s initial on a theme-accent circle instead. Eitr accepts PNG, JPEG, WebP, GIF (first frame) and BMP up to 40 MB and 12000 pixels per side.

It applies orientation, strips metadata and saves a 512×512 PNG at `~/.face`, then updates AccountsService for SDDM. If that update fails, the saved picture still works on the lockscreen; the sheet or CLI reports the login-screen error.

## Change your password

Open Settings > Users and choose Change password beside your name. Type your current password, then the new one twice: Enter moves to the next field and confirms on the last one; Escape cancels. The system's password rules decide what is accepted, and a refused password shows the reason. Eitr also moves the login keyring to the new password, so saved passwords keep unlocking when you sign in. A disk encryption passphrase is separate and stays the same. Walker > Settings > Security > Update Password does the same in a terminal.

## Manage accounts

Administrators have **Users** and **Manage** tabs in Settings > Users. Standard accounts see only the Users list. Manage offers Create User…, Change type, Set password for other accounts, and Remove with a home-folder choice. Confirm in the sheet, then press Enter in the task terminal to continue or Esc to cancel; enter passwords only in that terminal. Home folders are kept by default. See [User accounts](handbook:security) for permissions, keyring limitations and removal safeguards.

## Use Walker as an alternative

**SUPER + F** opens Walker. Its Settings menu follows the Settings app's groups: Devices, Desktop, Apps & Keys, Accounts & Security and System, with Control Center and Dotfiles at the bottom. Apps & Keys opens the Default Apps and Keybinds pages of the Settings app.

<!-- eitr-figure: launcher -->

Walker’s Settings menu is an alternative with its own folders. The > marker opens a submenu; the description below an action explains what it does.

Walker lists folders before actions. Type to search, Enter to open and Shift + Backspace to go back. Language selection remains in Walker > Settings > Devices > Language; see [Language](handbook:language).
