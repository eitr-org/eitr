#!/usr/bin/env python3
"""Open the app a notification came from: called when a notification without its own
click action is clicked. Focuses the window of the process that sent it, or else a
window whose class matches the app or its desktop entry. Herdr notifications come from
its background server, so they focus the terminal running a herdr client and switch
herdr to the workspace named in the notification."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def run(command, timeout=3):
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False).stdout
    except (OSError, subprocess.SubprocessError):
        return ""


def parent(pid, proc=Path("/proc")):
    try:
        # The parent pid follows the command name, which is in parentheses and may hold spaces.
        return int((proc / str(pid) / "stat").read_text().rsplit(")", 1)[1].split()[1])
    except (OSError, ValueError, IndexError):
        return 0


def window_of(pid, windows, proc=Path("/proc")):
    """The window owned by pid or by its nearest ancestor."""
    by_pid = {window.get("pid"): window for window in windows}
    seen = set()
    while pid > 1 and pid not in seen:
        if pid in by_pid:
            return by_pid[pid]
        seen.add(pid)
        pid = parent(pid, proc)
    return None


def window_by_name(names, windows):
    wanted = {name.lower().removesuffix(".desktop") for name in names if name}
    matches = [window for window in windows
               if {str(window.get("class", "")).lower(), str(window.get("initialClass", "")).lower()} & wanted]
    # Hyprland numbers focus history from 0 (most recent).
    return min(matches, key=lambda window: window.get("focusHistoryID", 1 << 30), default=None)


def herdr_clients(proc=Path("/proc")):
    """Pids of herdr client processes (not its server)."""
    found = []
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            argv = (entry / "cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if argv and Path(argv[0].decode(errors="replace")).name == "herdr" and b"server" not in argv[1:]:
            found.append(int(entry.name))
    return found


def herdr_workspace(label, listing):
    """The id of the herdr workspace with this label, from `herdr workspace list`."""
    try:
        workspaces = json.loads(listing)["result"]["workspaces"]
    except (ValueError, KeyError, TypeError):
        return ""
    return next((workspace["workspace_id"] for workspace in workspaces if workspace.get("label") == label), "")


def focus(window):
    address = str(window.get("address", ""))
    if address.startswith("0x"):
        run(["hyprctl", "dispatch", 'hl.dsp.focus({ window = "address:' + address + '" })'])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app", default="")
    parser.add_argument("--desktop-entry", default="")
    parser.add_argument("--pid", type=int, default=0)
    parser.add_argument("--body", default="")
    options = parser.parse_args(argv)
    try:
        windows = json.loads(run(["hyprctl", "clients", "-j"]) or "[]")
    except ValueError:
        windows = []
    window = None
    if options.app.lower() == "herdr":
        herdr = shutil.which("herdr")
        label = options.body.split(" · ")[0].strip()
        workspace = herdr_workspace(label, run([herdr, "workspace", "list"])) if herdr and label else ""
        if workspace:
            run([herdr, "workspace", "focus", workspace])
        window = next(filter(None, (window_of(pid, windows) for pid in herdr_clients())), None)
    if window is None and options.pid > 0:
        window = window_of(options.pid, windows)
    if window is None:
        window = window_by_name([options.desktop_entry, options.app], windows)
    if window is not None:
        focus(window)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
