# Troubleshooting

## Check This PC

Open **Settings > System > Maintenance > Check This PC**, or run `eitr check`. Checks are read-only and never repair or restart anything. Cached update lists are not refreshed; DNS resolution uses the network. `eitr check --json` prints technical evidence without prompts.

**Run deeper checks (asks for your password)**: press Enter to run `sudo /usr/lib/eitr/eitr-system selfcheck-deeper` in the same terminal, or Esc to skip. Results replace matching skipped checks. This reads root Snapper configuration, retained pre/post pairs, the last successful package upgrade description, existing Btrfs qgroups, boot guard JSON, an already mounted factory manifest, and trusted Arch Linux/Eitr keys with `pacman-key --list-keys`. It never enables quotas or mounts the factory point. Missing evidence is skipped with a reason. The factory manifest alone does not verify archive integrity. ESP checking uses `fsck.vfat -n` only on a uniquely identified FAT ESP not mounted read-write; otherwise it asks for an unmounted filesystem and skips.

Failed units show up to three names and a status command. Snapshot descriptions do not prove later desktop update steps succeeded; hook logs have no timestamps. Bar load errors have no structured query. Afterwards, **Enter** copies a redacted report and **Esc** closes. Review text before sharing; copying requires `wl-copy`.


## A menu action reports a missing tool

Fresh distro manifests include desktop runtime dependencies, but an existing
Arch desktop may lack some. Read the exact error and install the corresponding
package through Install > Packages > Pacman or a normal full-system update. Do not remove
BlueZ/iwd/PipeWire/WirePlumber merely because their settings are in native panels:
the panels still need those backends.

This handbook does not need `less`. It is bundled Markdown in a native overlay.
If the reader reports a missing/stale catalog, update the EITR desktop files.

## Root-owned helper missing

Network switching, security, battery limits and recovery operations require
reviewed root-owned helpers. A dotfiles-only desktop may not have the packaged
helpers yet. See the relevant chapter; never work around the check by running a
user-writable downloaded helper as root. The selector must not disconnect your
network just because you opened it.

## Configuration or service problems

Quickshell shows a readable reload error and retains the previous working
configuration when possible. Fix the named file; do not repeatedly restart the
login manager. **Never restart SDDM during your desktop session.**

An Elephant restart reloads menu definitions. Its service must retain
`KillMode=process` for helpers and fallback launches. In a uwsm session, launched
apps and terminals run in separate application scopes. Themes regenerate styles, so fix
the generator as well as generated output if a change disappears later.

## WiFi data stops refreshing

The bar shares one WiFi read broker across screens. If it exits, the last good
network data remains marked stale while the broker retries with increasing delays.
After six failed retries it waits for an explicit retry. Native controls remain
available. WiFi actions share an ordered queue and busy state across screens. If an action times out or the broker exits, its outcome is unknown: refresh the state before explicitly retrying. Writes are never replayed automatically. QR generation remains a separate helper.

For a technical status snapshot, use
`eitr-shell desktop-bar ipc call -- data status`. It reports topic ages,
error codes, in-flight reads, observers and restarts without network names or
addresses. Retry with `eitr-shell desktop-bar ipc call -- data retry`.

## Installation and recovery checks

EITR is still in beta: VM coverage does not prove every WiFi adapter, Bluetooth
pairing agent, TPM, GPU, fingerprint reader or Secure Boot setup works. Current
backend/enterprise WiFi code is mock-tested; test real authentication before
depending on it. Existing ISO files do not change when repository manifests
change: rebuild the payload/ISO for those changes to reach a new installation.

Back up your other disks before installing to a spare SSD and verify the target
disk carefully. The installer erases the disk you confirm. Keep encryption
passphrases and recovery keys offline. Snapshots on that same SSD are not an
independent backup. Start with [Recovery & Snapshots](handbook:recovery).

## Reporting a problem

**Settings > System > Information > Report a Problem** collects the EITR and package
versions, graphics hardware, Hyprland errors, failed services, recent warnings,
crashes of the last week, errors from the previous start, the installation log
and recent package changes into `~/Documents/eitr-problem-report-<time>.txt`,
readable only by you. It removes your user name, computer name, home path,
email, IP and MAC addresses, but logs can still mention apps or file names: read
it before sending it.

Nothing is sent by itself, and the terminal shows only where the report was
saved. It then offers ways to send it, or to read it first:

1. **Email** to `reports@eitr.info`: your email app opens a message with a short
   summary; attach the saved file.
2. **GitHub issue** (needs a GitHub account): the browser opens a new issue on
   the Eitr project. Issues are public.
3. **Copy** the report to paste anywhere.
4. **Read** the report: it opens in your text editor.

A report is used only to find and fix the problem, and is deleted once it is
fixed. An email shares your email address; reply to it to have your report
deleted at any time.

### When something crashes

Crash Notifications are on by default. A user service watches new, readable systemd-coredump records for your own programs. Each crash offers Report a problem, Ignore, and Mute this program; Ask the AI appears when a default assistant is installed and selected. Repeated crashes of one program are limited to one notification every five minutes. A crash that ends your session is offered at the next login, but programs that crash in the minute after you log out, restart or shut down are not: they are only losing the desktop around them. Toggle Crash Notifications under Main > Toggle or Control Center > Quick Toggles. Preferences and muted program paths stay in `~/.config/eitr/crash-help.json`; remove a path from `ignored` to allow it again.

Ask the AI opens your default assistant with only the program, signal and backtrace from `coredumpctl info`, asking for an explanation and a proposed fix without changing the system unless you agree. No core dump is passed. Your assistant may send that summary to its provider when you choose this action. Report a problem attaches the same summary to the existing report workflow: review it before sharing; nothing is sent automatically.

## Customizations and updates

EITR's own code is installed under `/usr/share/eitr` and updated with the
`eitr-desktop` package; your settings stay in `~/.config`. Put lasting changes
where updates never touch them:

- Monitors, devices, extra bindings and rules: `~/.config/hypr/local.lua`.
- Shell additions: `~/.config/eitr/shell.local.zsh`.
- Terminal options: `~/.config/kitty/local.conf`.
- Launcher colors: `~/.config/walker/style.override.css`.
- A whole replacement for a shipped file: the same relative path under
  `~/.config/eitr/overrides`. It no longer receives fixes from updates.

Theme files such as `kitty/theme.conf` and the Walker style are regenerated when
you switch themes and once after each package update; the previous copies are
kept under `~/.local/state/eitr/generated-backups`. When an update changes how a
setting is stored, it is converted once at login; a failure is reported and
retried at the next login (`~/.local/state/eitr/migrations.log`).
`eitr-config status` lists the settings and overrides in effect.

Failed task terminals offer **A: ask the AI** when a default assistant is selected; **Esc** closes. Only the last 200 output lines are kept in memory, with ANSI escapes removed and obvious secret lines hidden before sharing: a cloud assistant sends this output to its provider, while Ratatoskr keeps it on this PC.
