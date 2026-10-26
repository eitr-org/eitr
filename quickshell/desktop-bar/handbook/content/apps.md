# Apps and installation

Before installing official packages, the terminal shows that it is checking for pending system updates. This check may take a while before the administrator password is requested. Flatpak installations also announce their preparation stage. If updates are waiting, it explains why: Arch installs apps only on an up-to-date system, and installing now would also upgrade part of the system without a recovery snapshot. Enter runs System Update with its snapshot and then installs; Esc cancels without changing anything.

**SUPER + Space** and Main > Apps open the same app list. Enter launches an app.
Delete is available in Apps and asks for uninstall confirmation. Global search
from **SUPER + F** launches apps but does not expose uninstall actions.
There is no separate pin-based app menu.

Typing in the main menu searches installed apps and actions from all submenus.
Typing inside a submenu, such as System or Install, searches that submenu and
everything below it. Keyboard layouts and what lies below a cloud account
(services, resources, logs) are searched only inside their own menu; the cloud
account lists stay in search. Submenu rows end with **>**; **Shift + Backspace**
returns to the parent.

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
typed where the cursor is, in the language you spoke. You can also tap **SUPER + D**, speak, and tap it again. While it listens, the red
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

When a connected monitor reports HDR support, Eitr defaults Steam Proton games to Wayland and HDR with `PROTON_ENABLE_WAYLAND=1`, `PROTON_ENABLE_HDR=1` and `DXVK_HDR=1`. Machines without an HDR monitor keep their existing defaults. Hardware detection refreshes the generated display configuration when displays are listed or changed, and before that configuration loads at login or reload. Start a new desktop session and restart Steam to inherit changed defaults; an already running Steam process keeps its environment. Enable HDR in the game itself; fullscreen games can switch the monitor automatically even with desktop HDR off. A few games lose the Steam overlay in Wayland mode. To opt out for one game, set its Steam launch options to `PROTON_ENABLE_WAYLAND=0 %command%`. To calibrate a game, set its maximum or peak brightness to your monitor's HDR peak from its specifications (a DisplayHDR 400 monitor peaks around 400 nits), then adjust paper white or overall brightness to taste. If highlights lose detail, lower the peak; if the image looks dull, raise paper white.


## Voice reminders

Hold **SUPER + Shift + D**, speak and release, or open Main > Tools > Reminders > Tell the assistant… to type. Eitr transcribes locally using the same offline model as dictation, then asks your Development > Default Assistant to interpret the request. Only the transcript and reminder context go to that assistant's provider; audio stays local and is deleted after transcription. The assistant runs headless through Eitr's read-only path; Eitr validates its JSON and executes reminder actions itself, without giving the assistant tools to change anything. With Ratatoskr (Development > Default Assistant), the transcript never leaves this PC.

Say “Remind me tomorrow at 15:00 to call” or “Dentist on October 30 at 15:00, alert 30 minutes before”. Appointments alert one hour before by default (or your chosen lead) and at the event; plain reminders alert at their time. A date without a time opens the clock, with any assistant. Other missing details or ambiguity open a terminal with full numbered choices. Type a number or your own answer, or dictate it with SUPER + D; Esc cancels. A notification reports the result. Ask to list or cancel reminders as well.

New Reminder also accepts `tomorrow 15:00`, weekday names, `2026-10-30 09:00`, `Oct 30 15:00`, `9am`, `in 5 minutes` and `every 29th`. Quote multiword dates in the CLI. Each alert has its own timer; cancelling removes all alerts. Missed alerts appear at the next login. A date without a time, typed or spoken, opens a small clock: type a 24-hour time in the HH:MM field; Backspace removes the last digit and arrow keys adjust hours or minutes; Enter sets the time and Esc cancels. Reminder alerts play a short sound, except during Do Not Disturb. The calendar marks event days; click a day to see its reminder times and titles, updated immediately. Each listed reminder has a trash button: click it twice to delete a one-time reminder, or choose This one (only the next occurrence) or All for a repeating one. Escape, a click elsewhere or a few seconds without input keeps the reminder.

Repeating reminders accept `every day 08:00`, `every Monday 09:30`, `weekdays 07:00`, `every Monday and Thursday 09:30`, `every week`, `every month on the 15th` and `every year` (with a time). Quote the whole phrase in `eitr remind "every day 08:00" Stretch`. The assistant also supports intervals and an end date or occurrence count. Monthly dates such as the 31st and yearly February 29 fall back to the month’s last day. Local wall-clock time and relative alerts are preserved. Only the next occurrence has timers; after downtime, one missed occurrence is shown and elapsed occurrences are skipped, counting toward the limit. Upcoming Reminders shows the next time and rule. Choose This occurrence or All future occurrences to cancel; the CLI uses `eitr remind cancel ID occurrence` or `eitr remind cancel ID series`. The calendar marks occurrence days with dots and repeating entries with ↻, keeping its height fixed.

**Main > Tools > Calendars > Add Calendar…** shows a Google, Outlook or other iCal calendar in the calendar panel, read-only and without signing in. Choose the provider: Google and Outlook open their settings in the browser. In Google, copy Settings for my calendars > Integrate calendar > Secret address in iCal format; in Outlook, publish a calendar under Settings > Calendar > Shared calendars and copy its ICS link. Paste the address (`https://` or `webcal://`), then name the calendar. Anyone with that address can read the calendar, so Eitr keeps it in a private file and never shows it in menus, notifications or logs; reset the secret address at the provider if it leaks. Calendars refresh at login, every 15 minutes and when you open the calendar panel (at most once a minute). Events from the last week to the next 60 days appear beside reminders with the calendar's name and no trash button: change them in Google or Outlook. Timed events alert at their start with the reminder sound; all-day events do not alert. Daily, weekly, monthly (a day number or a weekday such as the last Friday) and yearly repeats are shown; rarer rules show only their first event. In the Calendars menu, Enter on a calendar refreshes it now and Delete removes it after you confirm. Two-way sync (creating or editing provider events) is not supported. The terminal stays open while you copy the link in your browser; Enter on the review adds it and Esc cancels.

## Plugins

A plugin is a Git repository containing scripts, Walker rows and optionally one user service. A plugin runs as you, with your account’s full permissions: it can read your files, SSH keys and browser data, send them anywhere and keep itself running. Eitr has not reviewed its code; the code belongs to its author, not to Eitr, and every plugin row says so, for example Plugin by Ada · not reviewed by Eitr. Only add plugins from people and repositories you trust.

Eitr asks for your password only in a terminal it opened for a step you started, such as System Update, never in a pop-up window. If a plugin asks for your password, it is not Eitr: do not type it.

Main > Install > Plugins > Add Plugin… asks for an HTTPS Git URL, or an SSH one such as `git@github.com:you/plugin.git` for a private repository (it uses your SSH keys through the agent). Adding takes two confirmations, and both default to No. First, before anything is downloaded, a safety page explains these risks; press Enter to download the plugin for review. Then the review starts with the trust warning and any warnings (a background service that starts at every login, binary files), followed by the manifest author, repository, exact commit, Git author and date, version, the number of executable files and the rows. Press Enter to install; Esc cancels at either step, and other keys do nothing. Nothing from the plugin runs before approval. `eitr plugin add URL` asks the same two questions (Enter continues, Esc cancels) and refuses to run without a terminal. Main > Tools > Plugins lists its actions; typing in Tools searches them too. The empty menu shows No plugins installed.

System Update checks plugins even when system packages are current. Each update starts with a summary: old and new commit, commit subjects, changed files with added and removed lines, and RISK flags for a background service that was added, changed or removed, any manifest change, new or changed executable files, binary files, and commits by another author than the approved commit’s. Press `d` to read the full diff in a pager (`delta` when it is installed, otherwise `less -R`), Enter to update, or Esc to keep the current version. When the history was rewritten, so the approved commit is not part of the new one, Eitr does not update automatically and says why; remove the plugin and add it again if you still trust it. Non-interactive updates skip plugins. Install > Plugins > the plugin offers Update and Remove; removal asks for confirmation and removes its files, rows and service. The same flows are available through `eitr plugin list`, `eitr plugin add URL`, `eitr plugin update [ID]` and `eitr plugin remove ID`.

Eitr ships a plugin blocklist inside the signed `eitr-desktop` package, so pacman’s package signature protects it. Each entry names a repository, a commit or a plugin id, with a reason. Adding or updating a blocked plugin is refused. An installed plugin that becomes blocked stops: its rows leave Tools > Plugins, it cannot be launched, its service is stopped and disabled, and one notification names it and the reason, with a Remove button. Install > Plugins marks it as blocked, and selecting it removes it. Its files are never deleted automatically. To report a harmful plugin, open `https://github.com/eitr-org/eitr/issues/new?template=malicious-plugin.yml`; never paste passwords, tokens or keys into the report. An organization profile can also turn plugins off or allow only listed repositories (see Organization profiles).

Plugins live only in `$XDG_DATA_HOME/eitr/plugins/<id>/` (default `~/.local/share/eitr/plugins/`); approvals are in `$XDG_STATE_HOME/eitr/plugins.json`. Services use `$XDG_CONFIG_HOME/systemd/user/eitr-plugin-<id>.service` with `NoNewPrivileges=yes`, so they cannot gain privileges through programs such as sudo. Never use sudo. Updates validate a separate candidate and retain the previous approved commit on refusal or failure. A plugin can modify your files while running; removing it cannot undo those changes.

### Manifest reference

The repository root contains `eitr-plugin.json`. Only these keys are accepted: `id` (lowercase letters/digits separated by single hyphens), `name`, `description` (up to 72 characters), `author`, `version`, `rows` (1–20), and optional `service`, `schemaVersion` and `hooks`. Each row requires `title`, `description` (both up to 72 characters) and `run`; optional keys are `icon` and `arguments` (an array of fixed strings). A service accepts only `run` and optional `arguments`. Commands use argv, never shell strings. `run` must name an executable inside the repository: absolute paths and `..` are refused, and so is a symlink anywhere in the plugin. Unknown or duplicate JSON keys are refused. Submodules are not initialized.

The tiny example in `distro/plugins/example/` contains a manifest and `notify.sh`, one notification action, a theme hook and no service. Copy it into your own Git repository, commit it and publish an HTTPS Git URL to try the complete installation flow. The example is shipped as documentation; it is not installed automatically.

Declare `schemaVersion: 1` in new manifests. Older manifests without it still work, with a reminder in review; higher versions need a newer Eitr. The author guide `distro/PLUGINS.md` (packaged as `PLUGINS.md`) defines the stable version 1 contract.

Plugins can declare `theme-changed`, `wallpaper-changed`, `after-update` and `login` hooks. They run in the background after the action (login once per desktop session), with a 30-second timeout. Failures are logged in `$XDG_STATE_HOME/eitr/plugin-hooks.log` and never fail the action. Review lists hooks; added or changed hooks raise update RISK flags. Blocklist and organization policy apply to hooks too.
