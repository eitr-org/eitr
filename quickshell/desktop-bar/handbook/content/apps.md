# Apps and installation

Before installing official packages, the terminal shows that it is checking for pending system updates. This check may take a while before the administrator password is requested. Flatpak installations also announce their preparation stage.

**SUPER + Space** and Main > Apps open the same app list. Enter launches an app.
Delete is available in Apps and asks for uninstall confirmation. Global search
from **SUPER + F** launches apps but does not expose uninstall actions.
There is no separate pin-based app menu.

Typing in the main menu searches installed apps and actions from all submenus.
Typing inside a submenu, such as System or Install, searches that submenu and
everything below it. Submenu rows end with **>**; **Shift + Backspace** returns
to the parent.

## Install

Press Delete on an installed entry in the named Install lists to uninstall it after confirmation. Web Apps retain their removal action. Packages (Pacman and Yay) remain install-only and have no Delete action. Required system dependencies are never removed recursively; pacman refuses removals that would break another package.

Managed language bundles show their full removal warning in a terminal before asking for confirmation with [y/N]; Enter cancels. Node removal includes all NVM-managed versions and their global npm tools. Python removal affects uv-managed versions and uv, not system Python. Java removes the current SDKMAN Java and Maven versions; Rust removes only its stable toolchain. Rails and Laravel remove their framework tools while retaining Ruby, PHP and Composer. Projects, settings and credentials are kept, but dependent tools and environments may stop working. Native assistant removal keeps cached versions and settings.


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

Press **Esc** to close waiting task, account, report and About terminals. Enter remains for answers and confirmations, including acknowledging a recovery key and powering off the installer.

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
dot just left of the clock becomes a small waveform that moves with your voice, so
you can see it hears you; after release it pulses until the words are typed.
The first use downloads the
speech model once (148 MB, checked against its published checksum) to
`~/.local/share/eitr/whisper/`; after that it works offline. Transcribing takes a
moment after release, longer on older processors. Recording stops when D is released, even if SUPER was released first, or after 120 seconds; the words are then transcribed as usual.

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

**Music Visualizer** in **Main > Tools** opens cava with theme colours. Right-click the media equalizer to open the same visualizer; left-click still opens media details. Press **q** or **Esc** to close it. On existing desktops, a missing cava package is installed first.

## Voice reminders

Hold **SUPER + Shift + D**, speak and release, or open Main > Tools > Reminders > Tell the assistant… to type. Eitr transcribes locally using the same offline model as dictation, then asks your Development > Default Assistant to interpret the request. Only the transcript and reminder context go to that assistant's provider; audio stays local and is deleted after transcription. The assistant runs headless through Eitr's read-only path; Eitr validates its JSON and executes reminder actions itself, without giving the assistant tools to change anything.

Say “Remind me tomorrow at 15:00 to call” or “Dentist on October 30 at 15:00, alert 30 minutes before”. Appointments alert one hour before by default (or your chosen lead) and at the event; plain reminders alert at their time. Missing details or ambiguity open a terminal with full numbered choices. Type a number or dictate it with SUPER + D; Esc cancels. A notification reports the result. Ask to list or cancel reminders as well.

New Reminder also accepts `tomorrow 15:00`, weekday names (09:00 if no time), `2026-10-30 09:00` and `Oct 30 15:00`. Quote multiword dates in the CLI. Each alert has its own timer; cancelling removes all alerts. Missed alerts appear at the next login. The calendar marks event days; click a day to see its reminder times and titles, updated immediately. Repeating reminders and external calendar synchronization are not supported yet.

## Plugins

A plugin is a Git repository containing scripts, Walker rows and optionally one user service. Plugins run with your account’s full permissions. Eitr has not reviewed their code: trust the author and repository before approving installation or an update.

Main > Install > Plugins > Add Plugin… asks for an HTTPS Git URL. The review shows the manifest author, repository, exact commit, Git author and date, added rows and background service. Scroll through the review and press `y` to install; Enter or Esc cancels. Nothing from the plugin runs before approval. Main > Tools > Plugins lists its actions; typing in Tools searches them too. The empty menu shows No plugins installed.

System Update checks plugins even when system packages are current. Each update shows old/new commits, commit subjects and changed files, and asks with `[y/N]`; Enter declines. Non-interactive updates skip plugins. Install > Plugins > the plugin offers Update and Remove; removal asks for confirmation and removes its files, rows and service. The same flows are available through `eitr plugin list`, `eitr plugin add URL`, `eitr plugin update [ID]` and `eitr plugin remove ID`.

Plugins live only in `$XDG_DATA_HOME/eitr/plugins/<id>/` (default `~/.local/share/eitr/plugins/`); approvals are in `$XDG_STATE_HOME/eitr/plugins.json`. Services use `$XDG_CONFIG_HOME/systemd/user/eitr-plugin-<id>.service`. Never use sudo. Updates validate a separate candidate and retain the previous approved commit on refusal or failure. A plugin can modify your files while running; removing it cannot undo those changes.

### Manifest reference

The repository root contains `eitr-plugin.json`. Only these keys are accepted: `id` (lowercase letters/digits separated by single hyphens), `name`, `description` (up to 72 characters), `author`, `version`, `rows` (1–20), and optional `service`. Each row requires `title`, `description` (both up to 72 characters) and `run`; optional keys are `icon` and `arguments` (an array of fixed strings). A service accepts only `run` and optional `arguments`. Commands use argv, never shell strings. `run` must name an executable inside the repository: absolute paths, `..`, and symlinks escaping the folder are refused. Unknown or duplicate JSON keys are refused. Submodules are not initialized.

The tiny example in `distro/plugins/example/` contains a manifest and `notify.sh`, one notification action and no service. Copy it into your own Git repository, commit it and publish an HTTPS Git URL to try the complete installation flow. The example is shipped as documentation; it is not installed automatically.
