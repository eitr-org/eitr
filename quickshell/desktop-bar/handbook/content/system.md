# Finding your way around Settings

Open **SUPER + F > Settings**. Folders come first, then actions, in alphabetical order. Global search also finds settings by their old names, including System and Toggle.

**Connectivity**, **Devices & Input**, **Language**, **Security**, **Style** and **System** are folders. **Control Center** opens the same controls as SUPER + comma. **Dotfiles** opens your configuration folder in VS Code or LazyVim.

Connectivity opens the native Bluetooth and WiFi panels, Network Backend and Remote Access. Backend selection prepares the next boot without restarting the live connection.

Devices & Input contains Audio, Battery Charge Limit, Display, Keyboard, Lighting and Microphone. Battery Charge Limit appears only with a system battery and requires supported firmware. Peripheral batteries do not enable laptop controls. Display includes brightness, Night Light and supported laptop power profiles.

Lighting is off by default. Follow Theme lets theme changes recolour devices controlled by OpenRGB.

Style contains the existing theme, wallpaper, lockscreen, Fonts and desktop appearance choices. Main now calls Toggle Quick Actions; Start Screensaver starts the screensaver immediately.

**Settings > System** contains **Information**, **Maintenance**, **Update Channel**, **About** and **System Update**. About opens the EITR system summary. Information contains AI Usage, Hardware, Report a Problem and Weather. Calendar, Workspace Overview and Ragnarök remain available through global search.

Maintenance contains Factory Reset, Snapshots, Check This PC, Choose Fastest Mirrors and Cleanup. Factory Reset requires two warnings and typed confirmation; read [Factory Reset](handbook:factory-reset) first.

Security keeps its existing authentication, firewall and user controls. Secure Boot documentation remains in [Secure Boot](handbook:secure-boot). Keep hardware overrides in `~/.config/hypr/local.lua` and secrets out of configuration backups.

**Walker > Settings > Language** lists available languages with the current choice checked; see [Language](handbook:language). English and translated names remain searchable. Main and Apps keep their custom order.

Security: Assistant Access, FIDO2 Security Key, Fingerprint, TPM Disk Unlock, Users, Firewall, Return to Password Authentication, Update Password.
