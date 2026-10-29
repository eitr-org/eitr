# Desktop Lockscreen

Local Quickshell lockscreen configuration with selectable designs derived from
[qylock](https://github.com/Darkkal44/qylock). Original designs and compatibility
components retain their GPL-3.0 license (see `LICENSE`). No external checkout or
upstream installation script is needed at runtime.
Imported from upstream revision `f6561e2ceae33f26e5e660742a5df2f725cbe514`.

## Use

- Walker: Style > Lockscreen. Enter selects a design for future locks.
- Ctrl+P previews without locking; Escape returns to the selector.
- Super+M locks with the selected design. Hyprlock remains the safety fallback.
- Preferences: `~/.config/lockscreen/selected` (machine-local; Hyprlock when absent).
- Create Lockscreen (same menu) stores a user's own lockscreen in
  `~/.local/share/eitr/lockscreens/<id>/` as `lockscreen.json` and a picture. It
  is selected as `user:<id>` and drawn by its shipped design (Theme Wallpaper or
  Material) with `background`, `accent` and `greeting` added to the config; no
  user QML is ever loaded. The login screen shows that design.

Idle locking uses the same launcher through `hypr/hypridle.conf`: lock after
15 minutes, screen off after 30 minutes, and suspend after 60 minutes. Hypridle
must be restarted after editing that config; reloading Hyprland alone does not
replace the running daemon's lock command. Design selections need no restart.

Dependencies: `quickshell`, `qt6-declarative`, `qt6-5compat`, `hyprlock`, and
`python`. Keep Hyprlock installed: its PAM configuration is used
for password authentication and it remains the safety fallback, but is not
listed in the design selector.

Real locks use Wayland's session-lock protocol on every monitor, not an overlay.
Previews are explicitly separate overlays: authentication and power actions
are disabled. The adapter accepts the current user's password only, never
switches users/sessions, and never kills existing lockers. Multi-prompt PAM/MFA
flows are not supported; select Hyprlock for those configurations.

The screens can be edited under `themes/`. The authentication/session-lock core
lives in `AuthAdapter.qml` and `shell.qml`, separately from the presentation.
`scripts/settings.py` discovers designs by `Main.qml` and reads their INI config.
If the Quickshell lock fails to start or exits without a successful unlock,
`scripts/launch.sh` hands the session to Hyprlock.

## Writing Designs

### EITR designs

All nine shipped designs live under `themes/`: Clockwork Neo Orbital, Clockwork
Tape, Eitr, Girl Coffee, Girl Pillow, Material Dark, Material Light, Nothing and
Theme Wallpaper. Eitr, the default for fresh installations, shows the EITR
wordmark in the theme's accent inside the boot splash's gold rune ring, which
ticks once a second, over a starry sky with the Milky Way, shooting stars and
the desktop's aurora on black. The clock uses Eitr's Norse glyphs, typed
characters carve runes into the password field and deleted ones crumble, and the
unlock strikes with lightning and burns the lockscreen away (ARTWORK.md has the
details). The current light/dark theme, clock format and Reduce motion
preference are read at launch; Reduce motion holds every layer still and skips
the effects.
Tape
and Neo Orbital use the procedural scene in
`EitrClockworkDesign.qml`, with the existing shared login controller. Tape rolls
the hour/minute/second strips; Neo Orbital has rune markers, a rotating indicator, an
offset dial and diagonal orbital track. Both light and dark palettes are supported.
Retained designs target 3840×2160 (16:9). Girl Coffee/Pillow retain their soft
anime mood with Norse clothing; Material keeps its abstract palette with drawn
runes. Nothing retains its original visual design. Raster sources smaller than
4K use a documented Lanczos export; procedural QML/SVG stays resolution-independent.
Clockwork uses installed JetBrainsMono Nerd Font and Noto Sans Runic, without
bundled fonts or background files. Its scene updates time once per second and
uses scene-graph animations;
it does not decode video or run a frame-rate JavaScript timer.

For the full gallery, run `bash quickshell/lockscreen/scripts/gallery.sh` from the
repository root. It uses mock authentication and generic user data, never a real
session lock. Escape dismisses it; Ctrl+Left/Right browse all nine designs.
This preview does not select a design or install SDDM files. Artwork prompts
and reference/provenance notes are in `ARTWORK.md`. All designs use system fonts
and still or procedural backgrounds; no bundled fonts or videos are needed.

### Component structure

A design is a directory under `themes/` with `Main.qml`, `theme.conf`,
`metadata.desktop`, `preview.png`, and its own assets. Shared pieces live in the
`LockscreenComponents` module (`imports/LockscreenComponents`); the launcher puts
it on the QML import path and the login installer copies it into every SDDM design.

- Media comes from `theme.conf`: set `background=` under `[General]` and pass it
  through `Qt.resolvedUrl(config.background)`, which resolves next to `Main.qml`.
  Replacing a wallpaper means replacing that file or editing that one value;
  shared QML never names media files.
- Still backgrounds use `Image` with `fillMode: Image.PreserveAspectCrop`.
  Shipped designs do not load videos or bundled fonts.
- Login: use `LoginController` for the user, session, and password flow, and
  never gate `login()` on `isQuickshell`; the Quickshell bridge already refuses
  logins in previews. Quickshell exposes `sddm`, `userModel`, `sessionModel`,
  `keyboard`, and `config` to `Main.qml` only, so pass them to shared components:

  ```qml
  LoginController {
      id: login
      sddm: typeof sddm !== "undefined" ? sddm : null
      userModel: typeof userModel !== "undefined" ? userModel : null
      sessionModel: typeof sessionModel !== "undefined" ? sessionModel : null
      onLoginFailed: errorText.text = "Try again"
  }
  // login.login(password), login.userName, login.cycleUser(), login.isQuickshell
  ```

- Variants of one layout share a module component configured by `theme.conf`.
  `material-you` and `material-you-dark` use `MaterialYouDesign` with
  `themeMode=light|dark`; their `Main.qml` files are identical.

Older imported designs still carry their own login boilerplate; move them to
these pieces when they are next edited. `tests/test_lockscreen.py` checks the
rules above.

## Login Screen

Install `eitr-desktop`, then configure the desktop user's selection policy once:

```sh
sudo python3 -I /usr/share/eitr/quickshell/lockscreen/scripts/install-login.py
```

The package owns `desktop-lockscreen-*` designs under `/usr/share/sddm/themes`;
package upgrades replace their code without copying from a user's home. The
setup command only configures account policy and selection. SDDM uses its native authentication, user model, and session selector;
the Quickshell authentication adapter is not installed into SDDM.

Walker selections then update both screens. A root-owned helper validates the
requested design against its installed manifest before atomically updating
`/etc/sddm.conf.d/90-desktop-lockscreen.conf`. Its sudo rule permits only this
selector, not arbitrary commands or file copying. If login selection fails,
the lockscreen selection stays unchanged. Previews never update either selection.
SDDM is never restarted; changes appear at the next login.

To restore the previous SDDM theme without changing your lockscreen, remove
`/etc/sddm.conf.d/90-desktop-lockscreen.conf` with sudo. To disconnect automatic
login selection, also remove `/etc/sudoers.d/desktop-login-select` and
the corresponding account policy; do not delete package-owned helpers.

### Recovery

Greeter test mode checks startup/rendering, not real password authentication.
If the login screen fails, press Ctrl+Alt+F3 and log in at the text console, then:

```sh
sudo mv /etc/sddm.conf.d/90-desktop-lockscreen.conf /etc/sddm.conf.d/90-desktop-lockscreen.conf.disabled
sudo systemctl restart sddm
```

This restores the previously configured SDDM theme. Restarting SDDM closes any
graphical session; use it only after saving your work or from a failed login.

Regenerate the 4K artwork with `python3 quickshell/lockscreen/references/build-artwork.py`.
Render all privacy-safe 4K previews with
`python3 quickshell/lockscreen/references/render-previews.py`; this runs offscreen,
with mock authentication, and never locks or captures the desktop.

### Theme Wallpaper

Style > Lockscreen > Theme Wallpaper uses the selected desktop wallpaper with
an adapted Sword layout: the clock at top left and the user/password controls
at bottom right, with dark gradients for readability. Walker previews the current
wallpaper; Ctrl+P shows the complete layout without locking. Each launch resolves
the latest selection. A missing saved image falls back to a current-theme image,
then the packaged Eitr default; without any image the dark gradient stays usable.
The login screen uses it too: SDDM cannot read the home folder, so
`settings.py` hands a JPEG copy of the wallpaper to `desktop-login-select
--wallpaper` (stdin only; it checks the JPEG and stores
`/var/lib/eitr/login-wallpaper.jpg`) when the design is chosen and after every
wallpaper change while it is selected. Without that copy the login screen shows
the Eitr runestone.
Its bundled 4K preview uses public Norse artwork, never an owner's wallpaper.

### Eitr review matrix

`python3 quickshell/lockscreen/references/render-eitr.py` writes 18 offscreen
mock previews to `../eitr-lockscreen-renders/`: ultrawide, landscape and portrait,
Eitr dark and Daylight light palettes, and empty, typed and rejected passwords.
Use `--output DIRECTORY` for a sandbox-writable destination. It also writes four
unlock-effect frames over a synthetic desktop, never the owner's desktop. The wordmark
SVG is a byte-identical copy of the branding master; the rune ring is the boot
splash's 24 Noto Sans Runic letters, drawn as text. Native rendering uses
precompiled Qt shaders; `bash quickshell/lockscreen/themes/eitr/shaders/build.sh`
regenerates the brand, sky and burn shaders with Qt's `qsb` (qt6-shadertools). Aurora uses
`quickshell/desktop-bar/shaders/aurora.frag.qsb` directly, drawn as the live
wallpaper draws it: half resolution scaled twice, advancing every 50 ms. The
checkout resolves that relative path; SDDM staging points to the same asset under
`/usr/share/eitr`. There is no lockscreen copy or Canvas aurora. Reduce motion
holds every layer still.

Qt's software scene graph does not support ShaderEffect, so it cannot display
the aurora. For privacy-safe offscreen review, the renderer compiles
`references/render-aurora.cpp` (Qt6Gui, EGL/OpenGL and a C++ compiler required),
executes the unchanged desktop GLSL through surfaceless Mesa/llvmpipe at each
requested native size, and injects those frames into the reference fixture only.
The fixture then captures the normal QML composition. `render-method.json`
records the canonical source hash, renderer and timings. This is a full-resolution
software OpenGL reference, not a separate approximation or a hardware GPU test.


### Eitr unlock effect

PAM success releases the session lock immediately. A separate normal layer
surface can then play the unlock effect over the most recent in-memory lockscreen
capture for 820 ms: by default lightning strikes the centre and the capture burns
away from there (`unlockEffect=lightning` in `themes/eitr/theme.conf`; `bifrost`
opens it like a gate instead). It is eligible only after successful
authentication, with both lock states released, a ready snapshot and Reduce
motion off. It takes no keyboard or pointer input, hides on animation completion
or its independent 1050 ms deadline, and the lockscreen process exits after at
most 1200 ms. This wait is after lock release, not an authentication delay.
Missing/late captures, loader errors or an unavailable compositor state skip the
cosmetic effect. Captures cover only the design, clear the active password field
first, stay in memory, and are never written to a file. Other designs keep their
existing exit.

Enter dismisses an Eitr preview with the same effect, without authentication;
Escape exits immediately. Offscreen mocks exercise the safety gates, capture
failures and preview flow. Actual compositor handoff and hardware shader/GPU
performance still require a live-session review; offscreen software results do
not establish them.
