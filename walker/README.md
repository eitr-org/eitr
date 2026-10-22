# Walker

Style → Cursor offers Bibata Modern (Eitr default), Breeze, and Vanilla DMZ.
Each family has light/dark variants, shown with previews decoded from its actual
cursor artwork. Color → Auto follows the selected theme; Light/Dark remain fixed
until Auto is selected again. Size is configurable, with 24 px as the default.
Preferences are in `~/.config/eitr/cursor.json`. Theme generation syncs Hyprland,
GTK, Qt and Xcursor defaults without changing the selected family or size.

Walker task, status and guide terminals use the theme-colored EITR rune banner.
Successful maintenance tasks close automatically; informational viewers retain
their hold/pager behavior. Cloud tasks show the banner after their initial clear.
Ordinary terminals, interactive editors and About keep their normal workflows.

The launcher uses the current theme and Hyprland's blur settings.
Its icon-labelled search field sits inside the same thin-bordered menu as the
results. The menu follows the desktop bar's Blur/Theme Color preference, including after
theme switches. Results grow naturally up to 520 px before scrolling.
SUPER+F keeps the ordered Main menu when the query is empty; typing searches all
Elephant menus and their Apps entries, ranked by Elephant's fuzzy relevance.
Opened submenus remain scoped for predictable navigation; return to Main with
the launcher shortcut for global search. SUPER+Space opens the same Apps menu as
Main > Apps, with Enter/Open and confirmed Delete/Uninstall. Global app search
offers Enter/Open only. Walker keeps its GTK/compositor animation; it does not share Quickshell's
native DockPanel unfolding/resizing animation.
Apps and Main share the configured launcher width; explicit width arguments override it.
Global search reads a private, session-local index rather than rebuilding every
dynamic submenu on each keystroke. Main prepares it on the first launch and
refreshes stale entries in the background on subsequent launches (60-second
freshness window). Clipboard contents are excluded; open Clipboard History to
search those. Selections are validated against the original provider before
running its existing action. No action commands or clipboard data are cached.

Style > Fonts searches installed main font families, grouping weight/style
aliases and Nerd Font editions into one entry. Enter selects the desktop
default (JetBrainsMono Nerd Font initially); Delete asks for confirmation.
User-installed font files go to Trash. Package-owned fonts open a terminal to
remove the owning package with normal dependency checks, never recursive removal.
The active default and system icon font are protected, including when bundled
with another family. Removing the last font or keyboard layout is forbidden.
System > Devices & Input > Keyboard supports Delete for a layout; keyboard panel rows have the same
guarded removal control.
The picker hides document and icon-only families and keeps one main Noto and
Adwaita choice. Their fallback/script/variant fonts remain installed. A hidden
font already selected as the default remains visible instead of its group's
usual representative.

Font preferences persist separately from themes. Supported consumers include
bar/panel text, Walker, GTK, Qt/KDE defaults, Kitty, VS Code/VSCodium editor and
terminal, SwayOSD and Fontconfig generic families. Ligatures are enabled in
Walker, Kitty and supported code editors; toolkit shaping uses available font
features. Kitty reloads its configuration in place. Some third-party windows may
need reopening; application-
specific font overrides and web-page fonts are not forcibly replaced.
`bin/walker` disables GTK's background-effects protocol only for Walker, allowing
the compositor's layer blur rule to apply. Other GTK applications are unchanged.

The package installs it as `eitr-walker`, and `eitr-config seed` adds a
`~/.local/bin/walker` shim that runs it, so a plain `walker` command gets the
same workaround. Keep `~/.local/bin` ahead of `/usr/bin` in PATH.

## Software and system menus

Main → Install → Packages → Pacman / Yay (AUR) opens a terminal package picker. Type to search
package names, press Tab to select/unselect multiple packages, then Enter to install
the selection in that terminal. Escape cancels without installing. Pacman uses
the local repository databases; AUR downloads its package-name index when opened.
Ctrl+B opens official metadata or the AUR build repository without
executing it; review PKGBUILD, .install files and patches before accepting Yay's
build prompts. Selection lasts only for that picker session.

SUPER+Space and Main → Apps use the same custom Apps provider. SUPER+F opens Main.
The native pin/launch-and-keep-open menu is no longer used. Apps has Enter-to-launch
and back navigation. Delete opens a themed
Cancel/Confirm prompt, then a terminal for package-manager authorization. The
whole owning package is removed, not just one launcher; dependencies are never
force-removed and personal application data is not deleted. Locally created
launchers without an identifiable package are rejected, not silently deleted.
Clipboard History (SUPER+Ctrl+V) Delete removes only the selected stored entry
and its private preview; it does not clear the active system clipboard.

Install → Development Languages, JavaScript Tools, and AI CLIs install optional
tools explicitly. Lazygit and Lazydocker are mandatory distro defaults, not a
Developer Tools submenu. Install → Browsers
offers Firefox, Tor Browser Launcher, Edge, Chromium and Chrome. Install →
Databases offers DBeaver, MariaDB Client, MongoDB Shell (AUR), pgcli, Valkey (a Redis-compatible
server) and SQLite; none is a default install, and installing Valkey does not enable its
service. Install → Productivity and Developer Apps offer desktop apps such as
LibreOffice, 1Password, Slack, Insomnia, Postman and VS Code; packages whose
licenses forbid redistribution are never on the ISO. Install → Web Apps
(`webapps.py`) creates launchers that open a site in a Chrome or Chromium app
window, downloading the site's icon on the user's machine; Delete removes one
there or in the Apps menu. Existing packages
are reused with --needed. Official-package installs first run `checkupdates`;
if system updates are pending they stop and point to System Update, so upgrades
never happen outside its recovery snapshots (Arch does not support partial
upgrades). Managed tool installers use official endpoints recorded in
`distro/installers.json` and never edit shell profiles; `HOME_FILES/.zshrc`
already adds their PATH entries. The runtime catalog ships in `/usr/share/eitr/`
with the eitr-desktop package (a copy in `~/.local/share/eitr/` takes precedence);
a missing catalog is shown as an error row in the menu.

System → Security separates password changes, fingerprint enrollment and FIDO2
security-key enrollment. Enrolling does not automatically change PAM; enabling
authentication is a separate confirmed operation through the root-owned helper.
Password fallback remains. Fingerprint is added to the hyprlock, SDDM and sudo
PAM stacks so "password only" also applies to the lockscreen; pam_fprintd may
delay the password prompt for up to 10 seconds. A FIDO2 biometric key is not a laptop fingerprint reader.
Touch ID on the host Mac is not passed through as a normal Linux fingerprint reader.
System → Maintenance → Snapshots requires the reviewed privileged integration described
in [the distro guide](../distro/README.md). Update works normally on existing
desktops. System Update upgrades official and AUR packages, with pre/post
snapshots enabled only on distro installs. Update also offers Update Channel.
Terminal commands `eitr update pacman`, `eitr update aur` and `eitr update full`
remain available without automatic snapshots.
No PAM or snapshot setup runs at login.
System → Devices & Input → Battery Charge Limit sets 60/80/90% or removes the limit after a typed
`yes`, through `eitr-system battery-limit`. It needs a laptop battery whose
firmware exposes `charge_control_end_threshold`; elsewhere it explains that no
control exists. The limit is restored at boot and after resume.
System → Maintenance → Factory Reset offers Erase Everything and Keep My Files on computers
installed with the Eitr ISO, after two warnings and typing `RESET MY COMPUTER`;
Reset Status only checks. See [FACTORY-RESET.md](../distro/FACTORY-RESET.md).

Gaming offers Steam (with GameMode and MangoHud), RetroArch and NVIDIA's official GeForce NOW Flatpak. NVIDIA's cloud
service is not restricted to local NVIDIA GPUs; no AMD-branded equivalent is
invented. Accounts, subscriptions and VM/cloud-client compatibility are separate.

Wallpaper and theme selections use the same 650 ms center-out reveal behind
application windows, without an input grab. Hyprpaper remains the persistent
wallpaper backend; if the transition cannot run, the static wallpaper still applies.

Development > Cloud lists AWS profiles from `aws configure list-profiles`. To show
friendly labels or pin a default region, copy
`scripts/menus/cloud/cloud.env.example` to `~/.config/eitr/cloud.env`; that file
is machine-local and never committed.

Cloud account, service and resource navigation uses generated Elephant Lua menus
with real `Parent` links. Shift+Backspace moves up one menu. The private
`~/.config/eitr/cloud-navigation.json` file holds the selected provider account,
AWS profile, Azure subscription/tenant, Google configuration/account/project and
resource choices. It never changes provider CLI defaults. Account workspaces keep
their own `selection.json` for native contexts, scopes and regions. Reports,
fzf log searches, reviewed setup terminals and Walker delete confirmations keep
their existing commands. Free-text prompts remain Walker text input.

The search box stays at a fixed top position while filtered results shrink below
it. The theme generator centres a full 656 px menu against the main display's
logical height (physical height divided by scale, accounting for rotation), with
a minimum offset of zero and a 212 px fallback when display data is unavailable.
This reference height includes the 520 px list, search, padding and hints; font
metrics can vary slightly. Display panel changes and mode-trial reverts refresh
the same generated style used by menus and dmenu lists.
