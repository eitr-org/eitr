# Themes, wallpapers and style

Settings (**SUPER + ,**) includes Appearance controls; **More themes** opens
the separate Themes & Plugins catalog window (**SUPER + F2**).

## Window layout

Choose **Tiling** (the default, Hyprland dwindle) or **Scrolling** in **Settings > Windows > Window layout** or **Walker > Settings > Style > Window layout**. Scrolling places windows in columns on a moving tape. Choices are saved locally and survive theme changes, config reloads and reboots; selection reloads the compositor configuration without restarting the session.

Scrolling reveals Direction (Right, Left, Down, Up), Default column width (One third, Half, Two thirds, Full), and Focus fit. Center centres the focused column; Fit brings it into view with minimal movement. Follow focus allows the tape to move when focus changes, including clicks. Fullscreen when one column lets a lone column fill the screen; it does not put the application into fullscreen. Defaults are Right, Half, Fit, and both switches on. These options stay saved when returning to Tiling. Walker also offers direction and width submenus.

Only while Scrolling is selected: **SUPER + ALT + arrows** focuses windows; **SUPER + ALT + SHIFT + Left/Right** swaps columns; **SUPER + ALT + Equal/Minus** cycles column width through one third, half, two thirds and full. Width cycles resize the focused column; Default column width controls new columns. See the generated [keyboard reference](handbook:shortcuts).


## Themes & Plugins catalog

The catalog shares the Settings window's frame, sidebar, page header and cards.
It follows the theme's colours, or the Eitr website palette when Settings chooses
it, with the bundled Cinzel lettering.

The left sidebar lists Installed, Official and Community under Themes and under
Plugins. The right side has the page title, description, the All, Light and Dark
filter for themes and an independently scrolling gallery. Up/Down moves between
sidebar rows; Right or Tab enters the content. Left from the first column returns
to the sidebar.

Open **More themes** in Settings > Appearance > Theme & Wallpaper, or press **SUPER + F2**. Themes & Plugins is a separate window. See [Settings](handbook:system) for navigation.

The catalog opens as a movable, resizable window. Hold SUPER and drag with the
left mouse button to move it, or the right button to resize it. Its last size is
remembered. Normal window shortcuts can tile it or send it to another workspace. Opening it again focuses the existing window, including on another workspace.

SUPER + F2 closes it when focused. Its close button, Escape (after dismissing any
review sheet), or the normal window close shortcut also closes it. Installed lists every theme as Built in, Official, Third-party
or Yours in a preview gallery. Click an installed card to apply it through the
normal theme workflow; a check marks the current theme.

All, Dark and Light
filter the gallery. Installed refreshes when the window opens and after actions. Opening the window
also checks package metadata in the background; update pills appear when it
finishes. There is no periodic network check. Update replaces a catalog theme; Update all, beside Add, updates every theme with an update pill in turn, and for plugins opens each update's review in turn. Reapply an updated
active theme to refresh the desktop.

Remove asks inside the window and refuses
the active theme: apply another theme first. Built-in and Yours items stay here.

Official combines built-in themes and the official `eitr-org/eitr-themes`
repository. Community lists community themes. Click a card on either tab to open
its details: preview, description, palette (hover for hex values), source, size,
maintainer and license. Wallpapers appear as thumbnails; community wallpapers
use name tiles with sizes. Click one to view it large, use Previous/Next to browse,
and Back to return. Escape, the close button or clicking outside closes details
and returns focus to the card. Full remote wallpapers download only when opened;
installed artwork is read locally.

A card's Install button toggles its download selection and shows Selected with a
check. Installed cards show Installed and retain Current where appropriate. Select several themes, then use Review & install in the pop-up that appears below the cards to review their previews,
sources and total size; Clear removes the selection. Arrows move between cards,
Space toggles selection, and Enter opens details on Official or Community.

Tab to
Review & install in that pop-up and press Enter to review the selection. Enter still
applies a theme on Installed and confirms an open review. The detail sheet's
Install reviews just that theme; after installation it offers Apply, or Current
when active. Escape cancels a review before closing details or the window.

Downloads, progress and errors stay in the window. Visible card previews and
opened galleries use the user cache. If a repository is unreachable, Retry loads
it again; Installed remains available offline.

Uncached community wallpaper sizes show Size unavailable until opened: obtaining
those sizes from Git would download the full files. Already cached sizes are shown.

The Plugins page lists installed plugins and the official `eitr-org/eitr-plugins`
repository as picture cards, using a screenshot, centered icon or generic glyph.
Badges show installed and disabled plugins. Removal has an in-window confirmation.
Click an Official or Community plugin to see its author, version, source,
components and a gallery of pictures and videos. Select a thumbnail to load that
asset. Videos loop muted; Play/Pause and Unmute/Mute stay inside the sheet.
Selecting another asset or closing details stops playback. Installed plugin cards
on the Installed tab keep their existing behavior.

Install opens an in-window review of the source, full commit, author, files,
commands and permissions. Update shows new commits, changed files and risk flags.
Plugins run with your account's full permissions; third-party and community
sources carry a stronger warning. Optional Ask the AI to check shows advice in
the window. Enter confirms; Escape cancels. Nothing installs before confirmation,
and the reviewed commit is preserved even if upstream changes. Reviews expire
after 15 minutes and are discarded when the catalog closes.

Installed > Add from a Git address accepts an HTTPS or SSH repository address for
a plugin or a data-only theme package, then shows its review. No terminal opens.
Walker and Control Center retain their terminal workflows.

Built-in themes ship with Eitr and cannot be removed. The trash button on a
downloaded theme deletes that installed package; the current theme cannot be removed.

Type anywhere in the catalog, or press Ctrl+F or /, to search the current page by
name or description. Words can appear in any order; Escape clears the search first.

## Choose a theme and wallpaper

Choose your theme and wallpaper in Settings > Appearance > Theme & Wallpaper. For Walker’s Dark/Light theme menus, use **Walker > Settings > Style > Theme** or **SUPER + Ctrl + Shift + N**. Double-right-click empty desktop space to open the theme carousel. The Sun filters light themes, the Moon dark themes; click the active filter again for all themes. The + opens the separate catalog with the same filter. Ctrl+Tab cycles filters, typing searches, arrows/Tab move and Enter applies. Backspace edits search or closes when empty; Escape clears search before closing.

**SUPER + Ctrl + N** opens wallpapers, and **SUPER + Shift + N** advances to
the next one. A checkmark marks the active choice in Walker. Theme/wallpaper
changes stay quiet: they do not send success notifications. Ultrawide monitors
(at least twice as wide as tall) show each wallpaper's 21:9 version, so less of
the picture is cut away; other monitors show the 4K 16:9 one.

The Eitr theme has four wallpapers: Aurora Fjord (the default), Dusk Fjord,
Rune Seal and Runestone. Select them through the same wallpaper controls;
the palette stays the same. The fourth wallpaper, Runestone, is live: northern
lights drift slowly behind the rune ring, update more slowly behind ordinary
windows, pause behind fullscreen apps, and remain still on the lockscreen.

Software rendering (for example, a VM without 3D acceleration) uses the selected
still wallpaper; the same fallback applies if the renderer cannot be detected. Graphite has been retired; saved Graphite
selections switch to Eitr and its default wallpaper.

Eitr Light is the light counterpart of Primordial Venom, with pale green surfaces, dark green text, venom yellow-green accents and jade/emerald highlights. Its four still wallpapers are Dusk Fjord (default), The Gates of Yggdrasil, Rune Seal and Primordial Drop, each with a separate panoramic composition. Select it in the Light category; Eitr remains the default. Theme Wallpaper uses the selected still image on the lockscreen.

The 13 built-in themes remain available offline. Install the 14 extra themes, including the light Freyja and Skaði, from the official `eitr-org/eitr-themes` catalog. Existing accounts received the first 12 in the background, with offline retries; their current theme and saved wallpaper stay unchanged. New accounts receive only built-ins.

The 13 shipped themes include ten dark realm palettes: Alfheim, Asgard, Helheim,
Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim and Vanaheim.
Each realm theme has two to five original wallpapers in varied ink,
gouache, cel-shaded and painted styles, in both aspect ratios. The first
wallpaper usually matches the theme's preview; Svartalfheim keeps its independent preview.

If Hyprpaper cannot display the selected wallpaper, the bar draws the same still image on each affected screen, including ultrawide variants. Wallpaper and theme choices still apply in Focus mode; the fallback switches without the wallpaper reveal animation.

## Your own wallpapers, themes and lockscreens

Your own pictures, themes and lockscreens stay on this computer, in
`~/.local/share/eitr/` (`wallpapers`, `themes` and `lockscreens`). Eitr never
uploads or shares them, and updates never change them. They appear beside the
shipped ones, marked **Yours**, and only they can be deleted: select one and
press **Delete**, then Enter to confirm or Escape to keep it.

- **Walker > Settings > Style > Wallpaper > Add My Own Wallpaper** takes a picture file or an https
  address. Downloads stop at 50 MB, and Eitr keeps a copy only after checking
  that the file is a JPEG, PNG or WebP picture. A web page's address works when
  the page offers a main picture; otherwise copy the image's own address. The
  picture is applied right away and appears in the wallpaper list, the carousel
  and SUPER + Shift + N. Deleting the wallpaper in
  use first switches to the theme's first wallpaper. Choose whether your wallpaper appears with all themes or only the current theme.
- **Walker > Settings > Style > Theme > Create Theme** asks for a picture (the current wallpaper,
  one of yours, the theme's, or another file or https address), light or dark
  (Automatic follows the picture's brightness), and a name. After the review,
  Eitr builds a full palette from the picture, keeping text clearly readable on
  the background, and applies the theme to the bar, terminal, launcher, apps and
  icons. A color list follows: choose Accent, Background, Text or one of the six
  terminal colors, type six hex digits, and the change applies at once; Escape
  finishes. **Ctrl + E** on one of your themes opens the list again. Deleting the
  theme in use first returns to the theme you used before creating it.
- **Walker > Settings > Style > Lockscreen > Create Lockscreen** uses the Theme Wallpaper or
  Material design with your picture, an optional accent color and an optional
  greeting under the clock, then shows a preview. Select it like any design.
  The login screen cannot read your home folder: it shows the same design, with
  your picture for Theme Wallpaper and the design's own picture for Material.
  Deleting the lockscreen in use first selects its design.

## Change the bar layout

**Settings > Desktop Bar** selects the layout, position and appearance; see [Desktop Bar](handbook:desktop-bar). **Settings > Windows > Corners** selects Square, Rounded or Extra Rounded. Window gaps and Reduce motion are on the same Windows page. Third-party apps may keep their own internal styling.

<!-- eitr-figure: window-style -->

Window gaps and Corners as **Settings > Windows** shows them, with your current choices checked. Default gaps are 6 px between windows and 12 px at the screen edges.

Use **Settings > Windows > Window gaps** or **Walker > Settings > Style > Window gaps** to choose None, Small, Default or Large. The choice is saved locally with Corners and survives theme changes and reloads.

## Change fonts

Choose an installed font in Settings > Appearance > Fonts & Cursor. JetBrainsMono Nerd Font is the default. The choice updates supported desktop apps; some apps keep their own font settings. To remove an installed font family, use Walker > Settings > Style > Fonts and review the packages it belongs to. The last usable family cannot be deleted.

## Change the pointer

Open Settings > Appearance > Fonts & Cursor. Cursor family chooses Bibata Modern, Breeze or Vanilla DMZ. Cursor colour offers Auto, Dark or Light; Auto follows the theme without changing your family. Cursor size adjusts the pointer size. Explicit colour and size choices survive theme changes. The page previews the selected pointer when its assets are available.

## Choose a lockscreen

**Settings > Lockscreen** sets the design of both the lockscreen and the login
screen. Existing preferences survive theme changes.

Available designs are Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee,
Girl Pillow, Material Dark, Material Light, Nothing and Theme Wallpaper, followed
by any lockscreens of your own; previews do not lock the session. A selection of a design
that is no longer shipped moves to Clockwork Tape. Fresh installations start with
Eitr.

Eitr shows the EITR wordmark in your theme's accent inside the boot splash's gold rune ring, which ticks once a second, over a starry sky with the Milky Way, now and then a shooting star, and the desktop's aurora on pure black (on an OLED those pixels stay off). The clock shows hours and minutes in Eitr's own Norse numerals and follows the 12- or 24-hour preference.

Each character you type carves a rune into the password field (always the same runes, in order, so only the length shows); arrows, Home and End move the block cursor, and Backspace or Delete crumble the rune beside it. Successful authentication unlocks immediately. Submitting, a failed login and switching accounts clear the runes instantly without crumbling.

Reduce motion holds everything still and skips the carving and crumbling effects. In a preview, Enter and Escape close it immediately without unlocking anything.

The artwork targets 4K (3840×2160, 16:9). Coffee and Pillow keep their
relaxed anime style with Norse clothing; Material and Clockwork use subtle rune
ornaments. Nothing keeps its existing design. QML and SVG remain scalable.

Compare the nine shipped EITR designs using
`bash quickshell/lockscreen/scripts/gallery.sh`. This does not change the selected
lockscreen; authentication and power actions are disabled in the gallery.
Clockwork uses procedural QML; Coffee, Pillow, Material and Nothing retain the
licensed layouts with new artwork and installed JetBrainsMono Nerd Font. No
bundled fonts or videos are required.

**Theme Wallpaper** uses the selected desktop wallpaper with a clock at the top
left and password controls at the bottom right. Its Walker preview shows the
current wallpaper. It follows later wallpaper changes at the next lock or
preview; Ctrl+P previews the full layout without locking. The login screen cannot
read your home folder, so it shows a copy of the wallpaper that Eitr stores when
you choose this design and again whenever you change wallpaper. If the saved image
is unavailable it uses another current-theme wallpaper or the Eitr default.

On PCs with several accounts, the login screen shows the selected user. Click the left or right half of the user picker, or press Ctrl+Left / Ctrl+Right, to choose another account; Enter still submits the password and Escape keeps its existing behavior. With one account the login layout is unchanged.

The lockscreen shows the locked session’s real name when available and only accepts that account’s password. Switch user (Ctrl+Alt+U) opens SDDM’s login screen while keeping the original session locked. Back in the locked session, click the password field once before typing. It appears only when several eligible accounts exist and SDDM reports that switching is available.

Previews and the gallery use three fictional accounts and never authenticate.

## Technical notes

The Limine boot menu shown at power-on uses the current theme's colours, an
EITR title and a larger font. Fresh installations set this up; after a theme
change the menu follows at the next shutdown, and the default theme's colours
are used if yours cannot be read. Boot entries are never changed, and
`limine.conf` is backed up before each change. The style is skipped while
Secure Boot is enabled, because an enrolled Limine config hash would stop the
system booting after an edit.
