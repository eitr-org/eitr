# Updates, cleanup and recovery

The terminal names each update check and snapshot stage while it runs. If everything is up to date, the message stays visible for three seconds before the terminal closes.

Waiting steps in System Update show a spinning rune and flow with Bifröst rainbow text on truecolour terminals, or the theme accent otherwise, followed by translated Norse phrases and elapsed time. Successful steps settle as a plain check mark and step text.

Open **System > Maintenance**. Review terminal output and keep independent
backups before system changes. Snapshot protection is not an off-disk backup.

System Update first checks official packages with checkupdates in a separate temporary database, AUR packages (including development packages), and user Flatpaks. When all checks confirm no updates, it exits without snapshots, upgrades or a restart prompt. If a check fails or a tool is missing, the normal update workflow continues.

## Update

**Update > System Update** is the normal complete package-update workflow.
On a configured fresh EITR distro, it verifies snapshot support and creates
pre/post snapshots with boot archives. If protection fails, no upgrade begins.
An existing Arch desktop without the distro policy does not require this setup
just to update. System Update also updates apps installed from Flatpak, such as
GeForce NOW; a Flatpak failure is reported without undoing the system update.

Before upgrading, System Update and terminal updates of official packages check
Arch Linux's news for posts since your last upgrade. Arch uses them to announce
upgrades that need a manual step. When there is news, it shows the titles and
links and asks **Continue the update? [y/N]**: Enter cancels before anything
changes, so you can read the post first. Without news, or without internet, it
just continues.

**Update > Update Channel** lists both channels with yours marked; choosing the
other asks for your password in a terminal and switches. It chooses where Eitr's
own updates come from. Stable,
the default, gets them once they have been tried. Testing gets new builds as
soon as they are published, to try changes early; everything else still comes
from Arch. Switching back to stable keeps a newer Eitr version until stable
catches up. From a terminal: `eitr channel` shows it, `eitr channel testing` or
`eitr channel stable` switches.

If an update leaves the computer unable to start, the **boot guard** undoes it:
when two starts in a row after an update never reach the login screen, the next
start restores the system and boot files from just before the update and
restarts. Your home folder is not touched, and the next login tells you what
happened. It works on computers installed with the Eitr installer; see
[Recovery & Snapshots](handbook:recovery) for the details.

**Home folder snapshots** keep earlier versions of your own files: turn them on
in **System > Maintenance > Snapshots > Home Folder Snapshots**. They are taken
every hour for a day and every day for a week, and the oldest go when the disk
gets full; caches, Downloads, VM disks and games are left out. To get a file
back, choose **Restore a File or Folder**, type its path and pick a time. The
old version appears next to the current one, so nothing is replaced.

System Update covers official, AUR and Flatpak packages with snapshots on supported distro installs. For rare cases such as updating only official packages when an AUR build fails, or skipping the snapshot, use a terminal: `eitr update pacman`, `eitr update aur` or `eitr update full` (no automatic snapshots), or plain `sudo pacman -Syu` / `yay -Sua`. Flatpaks, development runtimes and separate home data are not covered by root snapshots.

Avoid partial Arch upgrades. Read package prompts rather than accepting an
unexpected removal blindly. Successful update tasks close; failures remain
visible so you can troubleshoot rather than lose their output.

After a successful update, a notification asks to finish it when needed:
**Restart now** after kernel, firmware, microcode, systemd, glibc, graphics
driver or disk-encryption updates, or **Log out now** after desktop updates
such as EITR, Hyprland, Quickshell, Walker or PipeWire. **Later** keeps working;
the new versions take effect at the next restart or login.

## Cleanup and snapshots

Cleanup runs its maintenance workflow and keeps the report open for reading.
Review what it proposes; do not treat every orphan package as unused.
Snapshots offers the existing Snapper status/configuration workflows. Read
[Recovery & Snapshots](handbook:recovery) for supported layouts and bootloader limits.

## Factory reset

Only a supported distro install with its first-login restore point can reset.
That private baseline is separate from ordinary Snapper lists and cleanup.
Root can still delete it, and disk failure can destroy it. Two separate warnings
and a typed confirmation are required. Read [Factory Reset](handbook:factory-reset)
for exactly what Erase Everything and Keep My Files preserve.

## Power

Main > Power and Control Center > General (behind **Power…**) expose Lock,
Logout, Suspend, Reboot and Shutdown. Save work first. These are actions, not simulated demonstrations.

## Package mirrors

In System > Maintenance, choose Choose fastest mirrors. The terminal explains the change; Enter confirms and Esc cancels. Reflector selects up to ten HTTPS mirrors synchronized within 12 hours, sorted by download speed. It prefers the country identified by the system timezone when known, then tries worldwide mirrors if too few qualify. The three shipped worldwide servers always remain last; if ranking fails, the list stays unchanged, including custom mirrors. Each reflector run is limited to two minutes.

The previous list is saved beside `/etc/pacman.d/mirrorlist` as `mirrorlist.eitr-<timestamp>.bak`. When a backup exists, the same flow offers restoration: type `restore` and press Enter. Restoration also backs up the current list. The resulting list stays visible until Esc.

Fresh installations schedule one background attempt two minutes after each boot, up to three attempts with a connection. Offline boots skip silently and do not count; a successful ranking stops further attempts. Login never waits for ranking. Run the menu action later if all attempts fail. Only Arch package mirrors change; Eitr and Flatpak repositories are unaffected.

Read-only status: `/usr/lib/eitr/eitr-system mirrors-status` prints JSON with `last_ranking_time` (UTC, or null before success), `mirror_count`, `shipped_fallback` and `backup_available`. Status reads local files without network access or sudo.
