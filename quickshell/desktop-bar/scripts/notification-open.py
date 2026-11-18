#!/usr/bin/env python3
"""Open the app a notification came from: called when a notification without its own
click action is clicked. Focuses the window of the process that sent it, or else a
window whose class matches the app or its desktop entry. Herdr notifications come from
its background server, so they focus the terminal running a herdr client and switch
herdr to the workspace and tab the notification names ("Doola · 1 · Automations")."""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import urlsplit


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


def herdr_find(listing, kind, label):
    """The id of the herdr workspace or tab with this label, from its `list` output."""
    try:
        entries = json.loads(listing)["result"][kind + "s"]
    except (ValueError, KeyError, TypeError):
        return ""
    return next((entry.get(kind + "_id", "") for entry in entries if entry.get("label") == label), "")


def herdr_names(body):
    """The workspace and tab names in a herdr notification body, without its numbers."""
    names = [part.strip() for part in body.split(" · ") if part.strip() and not part.strip().isdigit()]
    return (names + ["", ""])[:2]


def safe_http_url(raw):
    """Return a normalized http(s) URL, or an empty string for any unsafe or non-http input."""
    if not isinstance(raw, str) or not raw or len(raw) > 4096:
        return ""
    if re.search(r"[\x00-\x20\x7f-\x9f\\<>\"']", raw):
        return ""
    if re.search(r"%(?:0[0-9a-f]|1[0-9a-f]|7f|25|5c)|%(?![0-9a-f]{2})", raw, re.IGNORECASE):
        return ""
    parts = urlsplit(raw)
    scheme = parts.scheme.lower()
    if scheme not in {"http", "https"} or not parts.netloc or parts.username or parts.password or "@" in parts.netloc:
        return ""
    try:
        port = parts.port
    except ValueError:
        return ""
    if port is not None and not (1 <= port <= 65535):
        return ""
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or len(host) > 253:
        return ""
    if host != "localhost":
        try:
            ip = ipaddress.ip_address(host)
        except ValueError:
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+", host):
                return ""
            if re.fullmatch(r"(?:0x[0-9a-f]*|[0-9]+)", host.rsplit(".", 1)[-1], re.IGNORECASE):
                return ""
        else:
            if ip.version != 4 or any(re.match(r"^0\d", octet) for octet in host.split(".")):
                return ""
    authority = host + (f":{port}" if port is not None else "")
    suffix = (parts.path or "/") + (f"?{parts.query}" if parts.query else "") + (f"#{parts.fragment}" if parts.fragment else "")
    return f"{scheme}://{authority}{suffix}"


def open_url(url):
    try:
        subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except OSError:
        return False
    return True


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
    parser.add_argument("--url", default="")
    options = parser.parse_args(argv)
    if options.url:
        url = safe_http_url(options.url)
        if not url:
            return 1
        return 0 if open_url(url) else 1
    try:
        windows = json.loads(run(["hyprctl", "clients", "-j"]) or "[]")
    except ValueError:
        windows = []
    window = None
    if options.app.lower() == "herdr":
        herdr = shutil.which("herdr")
        label, tab_label = herdr_names(options.body)
        workspace = herdr_find(run([herdr, "workspace", "list"]), "workspace", label) if herdr and label else ""
        if workspace:
            run([herdr, "workspace", "focus", workspace])
            tab = herdr_find(run([herdr, "tab", "list", "--workspace", workspace]), "tab", tab_label) if tab_label else ""
            if tab:
                run([herdr, "tab", "focus", tab])
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
