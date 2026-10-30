# Themes, wallpapers and style

## Themes and wallpapers

Open **Style > Theme** or **SUPER + Ctrl + Shift + N**. Pick Dark/Light, then a
theme. Start typing inside the theme carousel to filter; arrows/Tab move and
Enter applies. Backspace edits search first; Escape clears search before closing.
The category picker and wallpaper carousel do not have theme search.

**SUPER + Ctrl + N** opens wallpapers, and **SUPER + Shift + N** advances to
the next one. A checkmark marks the active choice in Walker. Theme/wallpaper
changes stay quiet: they do not send success notifications. Ultrawide monitors
(at least twice as wide as tall) show each wallpaper's 21:9 version, so less of
the picture is cut away; other monitors show the 4K 16:9 one.

The Eitr theme has four wallpapers: Primordial Drop (the default), Runestone,
Élivágar and Venom Rootlight. Select them through the same wallpaper controls;
the palette stays the same. The second wallpaper, Runestone, is live: northern
lights drift slowly behind the rune ring, pause behind fullscreen apps, and
remain still on the lockscreen. Graphite has been retired; saved Graphite
selections switch to Eitr and its default wallpaper.

The 24 shipped themes include ten dark realm palettes: Alfheim, Asgard, Helheim,
Jotunheim, Midgard, Muspelheim, Niflheim, Ragnarök, Svartalfheim and Vanaheim.
Each realm theme has two to five original wallpapers in varied ink,
gouache, cel-shaded and painted styles, in both aspect ratios. The first
wallpaper is the theme's preview.

## Your own wallpapers, themes and lockscreens

Your own pictures, themes and lockscreens stay on this computer, in
`~/.local/share/eitr/` (`wallpapers`, `themes` and `lockscreens`). Eitr never
uploads or shares them, and updates never change them. They appear beside the
shipped ones, marked **Yours**, and only they can be deleted: select one and
press **Delete**, then Enter to confirm or Escape to keep it.

- **Style > Wallpaper > Add My Own Wallpaper** takes a picture file or an https
  address. Downloads stop at 50 MB, and Eitr keeps a copy only after checking
  that the file is a JPEG, PNG or WebP picture. A web page's address works when
  the page offers a main picture; otherwise copy the image's own address. The
  picture is applied right away and appears in the wallpaper list, the carousel
  and SUPER + Shift + N. Deleting the wallpaper in
  use first switches to the theme's first wallpaper. Choose whether your wallpaper appears with all themes or only the current theme.
- **Style > Theme > Create Theme** asks for a picture (the current wallpaper,
  one of yours, the theme's, or another file or https address), light or dark
  (Automatic follows the picture's brightness), and a name. After the review,
  Eitr builds a full palette from the picture, keeping text clearly readable on
  the background, and applies the theme to the bar, terminal, launcher, apps and
  icons. A color list follows: choose Accent, Background, Text or one of the six
  terminal colors, type six hex digits, and the change applies at once; Escape
  finishes. **Ctrl + E** on one of your themes opens the list again. Deleting the
  theme in use first returns to the theme you used before creating it.
- **Style > Lockscreen > Create Lockscreen** uses the Theme Wallpaper or
  Material design with your picture, an optional accent color and an optional
  greeting under the clock, then shows a preview. Select it like any design.
  The login screen cannot read your home folder: it shows the same design, with
  your picture for Theme Wallpaper and the design's own picture for Material.
  Deleting the lockscreen in use first selects its design.

## Bar and corners

**Style > Desktop Bar** selects Blur/Theme Color, full/centered layout and edge.
Walker follows that appearance. **Style > Corners** selects Square, Rounded or
Extra Rounded for EITR surfaces and compositor decorations. Third-party apps
may retain their own internal widget style; circular status dots remain circular.

## Fonts

**Style > Fonts** lists usable installed font families, not every bold/italic
variant. Document/fallback families stay hidden. JetBrainsMono Nerd Font is
the default. Selection updates supported desktop apps; ligatures are enabled
where supported. Removing a family removes its supported installed variants;
the last usable choice cannot be deleted. Package ownership may require review.

## Cursor

**Style > Cursor** offers Bibata Modern, Breeze and Vanilla DMZ; Color offers
Auto, Dark and Light; Size chooses the pointer size. Auto follows the theme's
light/dark category without changing your selected family. Explicit color
overrides persist. The selected row uses a left-side checkmark; other family
choices show previews. Missing assets produce an error rather than saving a
broken selection.

The Limine boot menu shown at power-on uses the current theme's colours, an
EITR title and a larger font. Fresh installations set this up; after a theme
change the menu follows at the next shutdown, and the default theme's colours
are used if yours cannot be read. Boot entries are never changed, and
`limine.conf` is backed up before each change. The style is skipped while
Secure Boot is enabled, because an enrolled Limine config hash would stop the
system booting after an edit.

**Style > Lockscreen** sets the design of both the lockscreen and the login
screen. Existing preferences survive theme changes.

Available designs are Clockwork Neo Orbital, Clockwork Tape, Eitr, Girl Coffee,
Girl Pillow, Material Dark, Material Light, Nothing and Theme Wallpaper, followed
by any lockscreens of your own; previews do not lock the session. A selection of a design
that is no longer shipped moves to Clockwork Tape. Fresh installations start with
Eitr.

Eitr shows the EITR wordmark in your theme's accent inside the boot splash's gold rune ring, which ticks once a second, over a starry sky with the Milky Way, now and then a shooting star, and the desktop's aurora on pure black (on an OLED those pixels stay off). The clock shows hours and minutes in Eitr's own Norse numerals and follows the 12- or 24-hour preference. Each character you type carves a rune into the password field (always the same runes, in order, so only the length shows); arrows, Home and End move the block cursor, and Backspace or Delete crumble the rune beside it. After the password is accepted and the session already unlocked, lightning strikes the middle of the screen and the lockscreen burns away from there like paper, onto your desktop. Reduce motion holds everything still and skips these effects. In a preview, Enter shows the unlock effect without unlocking anything and Escape closes it.

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

On PCs with several accounts, the login screen shows the selected user. Click the left or right half of the user picker, or press Ctrl+Left / Ctrl+Right, to choose another account; Enter still submits the password and Escape keeps its existing behavior. With one account the login layout is unchanged. The lockscreen shows the locked session’s real name when available and only accepts that account’s password. Switch user (Ctrl+Alt+U) opens SDDM’s login screen while keeping the original session locked. Back in the locked session, click the password field once before typing. It appears only when several eligible accounts exist and SDDM reports that switching is available. Previews and the gallery use three fictional accounts and never authenticate.
