"""Cleaning mode controller: locks input behind a Hyprland submap and full-screen overlay."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import secrets
import signal
import subprocess
import sys
import tempfile
import threading
import time

from eitr_paths import state

INHIBIT_WHAT = "handle-power-key:handle-suspend-key:handle-hibernate-key:handle-lid-switch:idle"
SAFETY_HOLD_SECONDS = 360


def _runtime_path(name):
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    if os.path.isabs(runtime):
        return Path(runtime) / "eitr" / name
    return state(f"eitr/{name}")


def state_path():
    return _runtime_path("clean.json")


def lock_path():
    return _runtime_path("clean.lock")


def read_state():
    path = state_path()
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (FileNotFoundError, OSError, ValueError):
        return {}


def write_state(data):
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + path.name + "-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(data, output)
            output.write("\n")
            output.flush()
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def clear_state():
    state_path().unlink(missing_ok=True)


def is_inhibitor_alive(record):
    pid = record.get("pid")
    token = record.get("token")
    if type(pid) is not int or pid <= 1 or not isinstance(token, str) or not token:
        return False
    try:
        os.kill(pid, 0)
    except (ProcessLookupError, PermissionError):
        return False
    proc = Path(f"/proc/{pid}")
    if proc.is_dir():
        try:
            stat = (proc / "stat").read_text()
            right = stat.rfind(")")
            if right != -1 and stat[right + 2:right + 3] == "Z":
                return False
            cmdline = (proc / "cmdline").read_bytes()
            if token.encode("utf-8") not in cmdline:
                return False
        except OSError:
            return False
    return True


def _terminate_pid(pid, sig):
    try:
        os.killpg(pid, sig)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            os.kill(pid, sig)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def stop_inhibitor(record, sleep=time.sleep):
    pid = record.get("pid")
    if is_inhibitor_alive(record):
        _terminate_pid(pid, signal.SIGTERM)
        for _ in range(10):
            if not is_inhibitor_alive(record):
                break
            sleep(0.05)
        if is_inhibitor_alive(record):
            _terminate_pid(pid, signal.SIGKILL)
    clear_state()


def _default_run(command):
    return subprocess.run(command, text=True, capture_output=True)


def _default_spawn(command):
    return subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )


def current_submap(runner=_default_run):
    try:
        result = runner(["hyprctl", "submap"])
    except OSError:
        return ""
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _inhibit_command(token, max_seconds=SAFETY_HOLD_SECONDS):
    return [
        "systemd-inhibit",
        f"--what={INHIBIT_WHAT}",
        "--who=Eitr",
        "--why=Cleaning mode",
        "--mode=block",
        sys.executable,
        str(Path(__file__).resolve()),
        "_hold",
        "--token",
        token,
        "--max-seconds",
        str(max_seconds),
    ]


def start(runner=_default_run, spawner=_default_spawn, sleep=time.sleep):
    lock = lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        record = read_state()
        started_inhibitor = False
        if not is_inhibitor_alive(record):
            token = secrets.token_hex(8)
            proc = spawner(_inhibit_command(token))
            if proc.poll() is not None and proc.returncode != 0:
                raise RuntimeError("Could not start systemd-inhibit")
            write_state({"pid": proc.pid, "token": token})
            started_inhibitor = True

        try:
            runner(["eitr-shell", "desktop-bar", "ipc", "call", "--", "panels", "close"])
        except OSError:
            pass

        try:
            overlay = runner(["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "show"])
        except OSError as error:
            if started_inhibitor:
                stop_inhibitor(read_state(), sleep=sleep)
            raise RuntimeError(f"Could not show cleaning overlay: {error}") from error
        if overlay.returncode != 0:
            if started_inhibitor:
                stop_inhibitor(read_state(), sleep=sleep)
            detail = (overlay.stderr or overlay.stdout or "").strip()
            raise RuntimeError(detail or "Could not show cleaning overlay")

        try:
            submap = runner(["hyprctl", "dispatch", 'hl.dsp.submap("clean")'])
        except OSError as error:
            try:
                runner(["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "hide"])
            except OSError:
                pass
            if started_inhibitor:
                stop_inhibitor(read_state(), sleep=sleep)
            raise RuntimeError(f"Could not switch Hyprland to clean submap: {error}") from error
        if submap.returncode != 0:
            try:
                runner(["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "hide"])
            except OSError:
                pass
            if started_inhibitor:
                stop_inhibitor(read_state(), sleep=sleep)
            detail = (submap.stderr or submap.stdout or "").strip()
            raise RuntimeError(detail or "Could not switch Hyprland to clean submap")


def stop(runner=_default_run, sleep=time.sleep):
    lock = lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open("w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        for command in (
            ["hyprctl", "dispatch", 'hl.dsp.submap("reset")'],
            ["eitr-shell", "desktop-bar", "ipc", "call", "--", "clean", "hide"],
        ):
            try:
                runner(command)
            except OSError:
                pass
        stop_inhibitor(read_state(), sleep=sleep)


def status(runner=_default_run):
    if is_inhibitor_alive(read_state()):
        return "on"
    if current_submap(runner) == "clean":
        return "on"
    return "off"


def _hold(max_seconds):
    done = threading.Event()

    def handle_signal(_signum, _frame):
        done.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)
    done.wait(max(1, max_seconds))
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["start", "stop", "status", "_hold"])
    parser.add_argument("--token", default="")
    parser.add_argument("--max-seconds", type=int, default=SAFETY_HOLD_SECONDS)
    arguments = parser.parse_args(argv)
    if arguments.action == "start":
        start()
        return 0
    if arguments.action == "stop":
        stop()
        return 0
    if arguments.action == "status":
        print(status())
        return 0
    return _hold(arguments.max_seconds)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
