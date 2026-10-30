#!/usr/bin/env python3
"""After an update, offer a restart or log-out when changed packages need one.

`snapshot FILE` records installed package versions before the update; `compare
FILE` diffs them afterwards and, when needed, shows a notification whose button
restarts or logs out. The prompt runs in its own session, so it outlives the
update terminal.
"""
import eitr_bootstrap
from eitr_i18n import tr
import os
from pathlib import Path
import re
import subprocess
import sys

# Running processes keep the old copies of these until the system restarts.
RESTART = re.compile(r"^(linux(-lts|-zen|-hardened|-rt)?|linux-firmware.*|.*-ucode|systemd|systemd-libs|"
                     r"glibc|nvidia.*|mesa|lib32-mesa|cryptsetup|dbus|dbus-broker)$")
# The desktop session loads these once; a new session picks up the update.
LOG_OUT = re.compile(r"^(eitr-desktop|hyprland|hypr.*|aquamarine|quickshell|walker|elephant.*|uwsm|qt6-base|"
                     r"qt6-declarative|xdg-desktop-portal.*|pipewire.*|wireplumber)$")
COMMANDS = {"restart": ["systemctl", "reboot", "--no-wall"], "log-out": ["uwsm", "stop"]}


def installed():
    result = subprocess.run(["pacman", "-Q"], check=True, capture_output=True, text=True)
    return dict(line.split(" ", 1) for line in result.stdout.splitlines() if " " in line)


def read_snapshot(path):
    return dict(line.split(" ", 1) for line in Path(path).read_text().splitlines() if " " in line)


def changed(before, after):
    return sorted(name for name, version in after.items() if before.get(name) != version)


def kernel_modules_missing(release=None):
    """Arch deletes the running kernel's modules when the kernel package updates."""
    release = release or os.uname().release
    return not Path("/usr/lib/modules", release).is_dir()


def needed(names, modules_missing):
    restart = [name for name in names if RESTART.match(name)]
    if restart or modules_missing:
        return "restart", restart or ["the kernel"]
    log_out = [name for name in names if LOG_OUT.match(name)]
    return ("log-out", log_out) if log_out else (None, [])


def summary(names):
    shown = ", ".join(tr("the kernel") if name == "the kernel" else name for name in names[:4])
    return tr("{shown} and {count} more", shown=shown, count=len(names) - 4) if len(names) > 4 else shown


def prompt(kind, names):
    if kind == "restart":
        title, button = tr("Restart to finish updating"), tr("Restart now")
        body = tr("Updated {packages}. The system keeps using the old versions until it restarts.", packages=summary(names))
    else:
        title, button = tr("Log out to finish updating"), tr("Log out now")
        body = tr("Updated {packages}. Your desktop uses the new versions after you log back in.", packages=summary(names))
    result = subprocess.run(["notify-send", "--app-name=System Update", "--urgency=critical",
                             "--expire-time=0", f"--action={kind}={button}", "--action=later=" + tr("Later"),
                             "--wait", title, body], capture_output=True, text=True)
    if result.stdout.strip() == kind:
        subprocess.run(COMMANDS[kind], check=False)


def main(arguments):
    if len(arguments) == 2 and arguments[0] == "snapshot":
        Path(arguments[1]).write_text("".join(f"{name} {version}\n" for name, version in installed().items()))
        return 0
    if len(arguments) == 2 and arguments[0] == "compare":
        kind, names = needed(changed(read_snapshot(arguments[1]), installed()), kernel_modules_missing())
        Path(arguments[1]).unlink(missing_ok=True)
        if kind:
            print(tr("Restart to finish updating.") if kind == "restart" else tr("Log out to finish updating."))
            subprocess.Popen([sys.executable, __file__, "prompt", kind, *names], start_new_session=True,
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return 0
    if len(arguments) >= 2 and arguments[0] == "prompt" and arguments[1] in COMMANDS:
        prompt(arguments[1], arguments[2:])
        return 0
    print('Usage: restart-check.py snapshot FILE | compare FILE', file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
