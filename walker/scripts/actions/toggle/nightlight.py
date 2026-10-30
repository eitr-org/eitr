#!/usr/bin/env python3
"""Persist nightlight mode and apply it when the compositor is ready."""

import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config, read_settings, write_settings
from eitr_i18n import tr
import shutil
import subprocess
import tempfile
import time


STATE_DIR = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "desktop-nightlight"
MODE_FILE = STATE_DIR / "mode"
SCHEDULE_FILE = STATE_DIR / "schedule.json"
TIMER_OVERRIDE = user_config("systemd/user/nightlight-auto.timer.d/schedule.conf")
APPLIED_FILE = Path.home() / ".cache/nightlight-enabled"
TEMPERATURE = "4000"
MODES = {"auto", "on", "off"}


def mode():
    try:
        value = MODE_FILE.read_text().strip()
    except OSError:
        return "auto"
    return value if value in MODES else "auto"


def valid_time(value):
    try:
        parsed = dt.datetime.strptime(value, "%H:%M")
    except ValueError as error:
        raise ValueError(tr('Time must use HH:MM (00:00-23:59)')) from error
    if parsed.strftime("%H:%M") != value:
        raise ValueError(tr('Time must use HH:MM (00:00-23:59)'))
    return parsed.hour * 60 + parsed.minute


def schedule():
    data = read_settings(SCHEDULE_FILE)
    try:
        valid_time(data["start"])
        valid_time(data["end"])
        if data["start"] != data["end"]:
            return {key: data[key] for key in ('start', 'end')}
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        pass
    return {"start": "18:00", "end": "09:00"}


def scheduled(now=None, times=None):
    times = times or schedule()
    current = now or dt.datetime.now().astimezone()
    minute = current.hour * 60 + current.minute
    start, end = valid_time(times["start"]), valid_time(times["end"])
    return start <= minute < end if start < end else minute >= start or minute < end


def desired(current_mode, now=None):
    return scheduled(now) if current_mode == "auto" else current_mode == "on"


def running():
    return subprocess.run(["pgrep", "-x", "hyprsunset"], stdout=subprocess.DEVNULL,
                          stderr=subprocess.DEVNULL, check=False, timeout=5).returncode == 0


def status():
    times = schedule()
    return {
        "mode": mode(),
        "enabled": APPLIED_FILE.is_file() and running(),
        "scheduled": scheduled(times=times),
        **times,
        "available": bool(shutil.which("hyprsunset") and shutil.which("hyprctl")),
    }


def save_text(path, value):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", dir=path.parent, delete=False) as temporary:
        temporary.write(value)
        temporary_path = Path(temporary.name)
    temporary_path.chmod(0o600)
    os.replace(temporary_path, path)


def save_mode(value):
    save_text(MODE_FILE, value + "\n")


def save_schedule(start, end):
    valid_time(start)
    valid_time(end)
    if start == end:
        raise ValueError(tr('Start and end times must differ'))
    if SCHEDULE_FILE.is_file() and TIMER_OVERRIDE.is_file() and schedule() == {"start": start, "end": end}:
        return
    override = ("[Timer]\nOnCalendar=\n"
                f"OnCalendar=*-*-* {start}:00\nOnCalendar=*-*-* {end}:00\n")
    save_text(TIMER_OVERRIDE, override)
    write_settings(SCHEDULE_FILE, {"start": start, "end": end})
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "--user", "restart", "nightlight-auto.timer"], check=True)


def apply():
    if not shutil.which("hyprsunset") or not shutil.which("hyprctl"):
        raise RuntimeError(tr('hyprsunset and hyprctl are required'))

    enabled = desired(mode())
    if not running():
        command = ["uwsm", "app", "--", "hyprsunset"] if shutil.which("uwsm") else ["hyprsunset"]
        subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)

    command = ["hyprctl", "hyprsunset", "temperature", TEMPERATURE] if enabled else ["hyprctl", "hyprsunset", "identity"]
    error = ""
    for attempt in range(60):
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode == 0:
            if enabled:
                APPLIED_FILE.parent.mkdir(parents=True, exist_ok=True)
                APPLIED_FILE.touch()
            else:
                APPLIED_FILE.unlink(missing_ok=True)
            return status()
        error = result.stderr.strip()
        if attempt < 59:
            time.sleep(0.25)
    raise RuntimeError(error or "hyprsunset did not become ready")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("status", "apply", "toggle", "set", "schedule", "configure"))
    parser.add_argument("value", nargs="?")
    parser.add_argument("end", nargs="?")
    parser.add_argument("configured_mode", nargs="?")
    args = parser.parse_args()
    if args.action == "status":
        print(json.dumps(status()))
        return 0
    if args.action == "set" and args.value not in MODES:
        parser.error('set requires auto, on, or off')
    if args.action == "schedule" and (args.value is None or args.end is None):
        parser.error('schedule requires START and END in HH:MM format')
    if args.action == "configure" and (args.value is None or args.end is None or args.configured_mode not in MODES):
        parser.error('configure requires START END and auto, on, or off')

    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (STATE_DIR / "lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == "set":
            save_mode(args.value)
        elif args.action in ("schedule", "configure"):
            try:
                save_schedule(args.value, args.end)
                if args.action == "configure":
                    save_mode(args.configured_mode)
            except (ValueError, subprocess.CalledProcessError) as error:
                print(str(error), file=sys.stderr)
                return 1
        elif args.action == "toggle":
            save_mode("off" if status()["enabled"] else "on")
        try:
            print(json.dumps(apply()))
        except RuntimeError as error:
            print(str(error), file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
