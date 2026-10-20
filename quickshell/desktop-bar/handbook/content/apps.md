# Apps and installation

**SUPER + Space** and Main > Apps open the same app list. Enter launches an app.
Delete is available in Apps and asks for uninstall confirmation. Global search
from **SUPER + F** launches apps but does not expose uninstall actions.
There is no separate pin-based app menu.

Typing in the main menu searches installed apps and actions from all submenus.
Typing inside a submenu, such as System or Install, searches that submenu and
everything below it. Submenu rows end with **>**; **Shift + Backspace** returns
to the parent.

## Install

Apps already on the system show **Installed** under their name; choosing one
says so instead of installing it again. This also recognizes tools installed by
their own managers, such as Java from SDKMAN or Node.js from NVM. Packages that
need a runtime, such as DBeaver's Java, bring a small one only when no package
provides it yet.

- **AI CLIs:** optional AI command-line clients.
- **Browsers:** supported browser choices.
- **Databases:** optional tools such as DBeaver, database clients and Valkey
  (the Redis-compatible server Arch ships instead of Redis).
- **Development Languages:** optional language toolchains; Java/Flutter are
  not mandatory desktop dependencies.
- **JavaScript Tools:** optional JavaScript runtimes and tooling.
- **Packages > Pacman** and **Packages > Yay (AUR):** search the official Arch
  packages or the community AUR packages, each labeled with where it comes from
  and whether it is installed. The search is on top, the packages under it and
  the selected package's details below; **Ctrl+B** shows its build file
  (PKGBUILD) instead and back, **Ctrl+O** opens its page in the browser, **Tab**
  selects several and **Enter** installs them. AUR packages are built on this
  computer from their build file, so read it first; they are not official Arch
  packages.

Installation/update/setup terminals show the themed EITR banner. Successful
tasks normally close; failures stay visible. Reports such as Cleanup stay open
so you can read them. Ordinary terminals and About do not show the task banner.

## Tools

**Calculator** in Apps (or the keyboard's calculator key) opens Eitr's
calculator in the current theme's colors. Type or click: `+ − × ÷`, `^` for
powers, `%` for percent (`200×15%`), `√` and brackets; a number before a
bracket multiplies (`2(3+4)`). Enter shows the result, Backspace removes a
character, Escape clears (twice closes) and Ctrl+C or **Copy** copies the result.
It works out the expression itself rather than running it as code.

**Offline dictation** is speech-to-text that never leaves the computer. Hold
**SUPER + D**, speak, and release: the words are
typed where the cursor is, in the language you spoke. While it listens, the red
dot beside the weather becomes a small waveform that moves with your voice, so
you can see it hears you; after release it pulses until the words are typed.
The first use downloads the
speech model once (148 MB, checked against its published checksum) to
`~/.local/share/eitr/whisper/`; after that it works offline. Transcribing takes a
moment after release, longer on older processors.

**Main > Tools > Reminders > New Reminder** asks when (a delay such as `10m` or `1h30m`, or a
time of day such as `18:30`) and what about, then shows a notification at that
time that stays until you dismiss it. **Upcoming Reminders** lists the waiting
ones; pick one to cancel it. Reminders survive a restart, and any that came due
while the computer was off appear at the next login. From a terminal:
`eitr remind 25m Take the tea out`, and `eitr remind` alone lists them.

## Gaming

Main > Gaming lists **GeForce NOW**, **RetroArch** and **Steam**. Choosing one
opens it when it is installed, and installs it otherwise. RetroArch comes from
Arch's official packages with cores for the classic consoles: NES, SNES, Game
Boy and Game Boy Advance, Mega Drive/Genesis, PlayStation, Nintendo 64, Nintendo
DS, PSP and Dreamcast. Add your own games and, where a console needs one, its
BIOS files; Eitr ships neither. GeForce NOW installs from Flatpak.

**Toggle > Game Mode** gets the desktop out of the way while you play: window
animations, blur and shadows turn off, notification popups wait (do not
disturb), and the power profile switches to performance where the computer has
one. Turning it off restores exactly what it changed. Steam installs with
**GameMode** and **MangoHud**: add `gamemoderun mangohud %command%` to a game's
launch options in Steam to boost the CPU during play and show the FPS overlay.

LocalSend's packaged app includes its runtime requirements: you do not need
the Flutter SDK just to run it. Developer tools remain optional.

Use [Updates & Cleanup](handbook:maintenance) for upgrading; installing one
package is not the same as the snapshot-protected System Update workflow.
