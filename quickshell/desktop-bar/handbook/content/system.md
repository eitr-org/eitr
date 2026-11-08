# Find a setting

Press **SUPER + ,** to open Settings. Start typing in its sidebar search to find a page; a matching tab opens directly. System is the overview, not a folder containing every setting.

<!-- eitr-figure: settings-window -->

The Settings window has a searchable sidebar and cards for related controls. It stays open when you click outside. Close it with Escape, its close button or the normal close-window shortcut.

Panel footer links close the panel and open the matching Settings page. The Control Center’s All settings button does the same; use **SUPER + I** for quick controls. See [Control Center](handbook:control-center).

Choose Settings colours in Settings > Appearance > Theme & Wallpaper: Theme colours follows your desktop, while Eitr website uses the website palette. This affects Settings, the Handbook and Themes & Plugins, not the desktop theme.

The separate Themes & Plugins catalog opens with SUPER + F2 or More themes in Appearance.

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
| User | [User](handbook:security) |
| Git & Cloud | [Git & Cloud](handbook:git-accounts) |
| Security | [Security](handbook:security) |
| Updates | [Updates](handbook:maintenance) |
| Check This PC | [Check This PC](handbook:troubleshooting) |
| About | [About](handbook:information) |

## Change your profile picture

Open Settings > User (or click your picture on Settings' System overview) and choose Change picture. The system file chooser floats centred above Settings, showing only images; pick one and the crop editor opens in a sheet over Settings. Drag the round preview to move the image; use the wheel, slider or +/− to zoom from 1× to 4×, and arrow keys to move. Save (or Enter) applies the crop; Cancel or Escape closes the sheet without applying it. Remove, beside Change picture, clears the picture.

Pictures appear as circles in Control Center, the lockscreen and the login screen. Control Center only displays the picture at the top of its navigation; without one it shows nothing there, and neither do the lockscreen and login screen. Settings shows your name’s initial on a theme-accent circle instead. Eitr accepts PNG, JPEG, WebP, GIF (first frame) and BMP up to 40 MB and 12000 pixels per side.

It applies orientation, strips metadata and saves a 512×512 PNG at `~/.face`, then updates AccountsService for SDDM. If that update fails, the saved picture still works on the lockscreen; the sheet or CLI reports the login-screen error.

## Use Walker as an alternative

**SUPER + F** opens Walker. Its Settings menu still has folders such as Style, Devices & Input and System. These are Walker paths, not pages in the Settings app.

<!-- eitr-figure: launcher -->

Walker’s Settings menu is an alternative with its own folders. The > marker opens a submenu; the description below an action explains what it does.

Walker lists folders before actions. Type to search, Enter to open and Shift + Backspace to go back. Language selection remains in Walker > Settings > Language; see [Language](handbook:language).
