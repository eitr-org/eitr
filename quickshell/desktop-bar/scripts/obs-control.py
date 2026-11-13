#!/usr/bin/env python3
"""Control OBS and seed safe capture defaults for a new configuration.

Profiles are left alone, except that a recording folder still at OBS's default
(the home folder) becomes ~/Videos/Records.
"""
import json
import configparser
import os
from pathlib import Path
import re

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config
from eitr_app import app_command
from eitr_i18n import tr
# The capture domain loads this file by path, so its own folder is not always importable.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import obs_options
import obs_screen
import secrets
import shlex
import signal
import subprocess
import tempfile
import time
from urllib.parse import quote


def launch_background():
    result = subprocess.run([
        "hyprctl", "eval",
        'hl.exec_cmd(' + json.dumps(shlex.join(app_command(['obs', '--minimize-to-tray'])), ensure_ascii=False)
        + ', { workspace = "special:obs-background silent" })',
    ], capture_output=True, timeout=3)
    if result.returncode:
        raise RuntimeError(tr('Could not launch OBS in the background'))


def reveal_window():
    clients = subprocess.run(["hyprctl", "-j", "clients"], capture_output=True, text=True, timeout=2)
    if clients.returncode == 0:
        for client in json.loads(clients.stdout):
            if client.get("class") == "com.obsproject.Studio" and client.get("workspace", {}).get("name") == "special:obs-background":
                workspace = subprocess.run(["hyprctl", "-j", "activeworkspace"], capture_output=True, text=True, timeout=2)
                if workspace.returncode == 0:
                    current = json.loads(workspace.stdout)["id"]
                    target = json.dumps("address:" + client["address"])
                    subprocess.run(["hyprctl", "eval", f"hl.dispatch(hl.dsp.window.move({{ workspace = {current}, window = {target}, follow = false }}))"], capture_output=True, timeout=2)
    subprocess.run(["hyprctl", "eval", 'hl.dispatch(hl.dsp.focus({ window = "class:^(com.obsproject.Studio)$" }))'], capture_output=True)


WEBSOCKET_ENV = "OBS_WEBSOCKET_URL"


def records_folder():
    """Records inside the user's Videos folder (named for their language by xdg-user-dirs)."""
    videos = Path.home() / "Videos"
    try:
        for line in user_config("user-dirs.dirs").read_text().splitlines():
            if line.startswith("XDG_VIDEOS_DIR="):
                value = line.split("=", 1)[1].strip().strip('"').replace("$HOME", str(Path.home()))
                if value.startswith("/") and Path(value) != Path.home():
                    videos = Path(value)
    except OSError:
        pass
    return videos / "Records"


# Where OBS's Simple, Advanced and Advanced custom FFmpeg outputs keep their recording folder.
RECORDING_PATHS = (("SimpleOutput", "FilePath"), ("AdvOut", "RecFilePath"), ("AdvOut", "FFFilePath"))


def default_recording_folder():
    """Point OBS's recording folder at ~/Videos/Records while it is still OBS's default.

    OBS rewrites its profile when it exits, so callers run this only while OBS is
    closed; a folder anyone chose is never replaced. Returns whether the profile changed.
    """
    profile = obs_options.profile_file()
    try:
        text = profile.read_text()
    except FileNotFoundError:
        text = ""
    current = configparser.ConfigParser(interpolation=None, strict=False)
    current.optionxform = str
    current.read_string(text)
    updated = text
    for section, key in RECORDING_PATHS:
        if current.get(section, key, fallback="").rstrip("/") in ("", str(Path.home())):
            updated = obs_options.set_ini_value(updated, section, key, str(records_folder()))
    records_folder().mkdir(parents=True, exist_ok=True)
    if updated == text:
        return False
    profile.parent.mkdir(parents=True, exist_ok=True)
    temporary = profile.with_name(".basic.ini.eitr")
    temporary.write_text(updated)
    os.replace(temporary, profile)
    return True


def websocket_settings():
    """OBS's WebSocket settings, turning the server on (with a password) when it is off.

    OBS ships it off and rewrites its plugin settings when it exits, so the change
    is only made while OBS is closed. Authentication always stays required.
    """
    path = user_config("obs-studio/plugin_config/obs-websocket/config.json")
    try:
        config = json.loads(path.read_text())
    except FileNotFoundError:
        config = {}
    except (OSError, ValueError) as error:
        raise RuntimeError(tr('OBS WebSocket settings are unreadable')) from error
    if config.get("server_enabled"):
        return config
    if obs_options.obs_running():
        raise RuntimeError(tr('Close OBS once so Eitr can turn on its WebSocket, then try again'))
    config.update(server_enabled=True, auth_required=True, first_load=False,
                  server_password=config.get("server_password") or secrets.token_urlsafe(24))
    config.setdefault("server_port", 4455)
    config.setdefault("alerts_enabled", False)
    path.parent.mkdir(parents=True, exist_ok=True)
    # mkstemp creates the file readable only by its owner; it holds the password.
    descriptor, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(config, output, indent=4)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return config


def websocket_command():
    """Return the obs-cmd command and export its connection URL.

    The URL contains the WebSocket password, so it is passed through this
    process's environment (inherited by obs-cmd children) instead of argv,
    which other local users can read from the process list.
    """
    config = websocket_settings()
    password = config.get("server_password", "") if config.get("auth_required") else ""
    os.environ[WEBSOCKET_ENV] = f"obsws://localhost:{config.get('server_port', 4455)}/{quote(password, safe='')}"
    return ["obs-cmd"]


def parse_status(text):
    fields = dict(line.strip().split(":", 1) for line in text.splitlines() if ":" in line)
    active = fields.get("Active", "").strip().lower()
    if active not in {"true", "false"}:
        raise RuntimeError(tr('OBS status unavailable'))
    paused = fields.get("Paused", "false").strip().lower()
    if active == "true" and paused not in {"true", "false"}:
        raise RuntimeError(tr('OBS pause status unavailable'))
    return {"active": active == "true", "paused": paused == "true"}


def status(outputs=None):
    state = {"running": False, "ready": True, "recording": False, "paused": False, "streaming": False}
    if subprocess.run(["pgrep", "-x", "obs"], capture_output=True, timeout=2).returncode != 0:
        return state
    state.update(running=True, ready=False)
    try:
        command = websocket_command()
        for kind in ("recording", "streaming"):
            result = subprocess.run(command + [kind, "status"], capture_output=True, text=True, timeout=3)
            if result.returncode:
                raise RuntimeError(tr('Could not read OBS status'))
            if outputs is not None:
                outputs[kind] = result.stdout
            parsed = parse_status(result.stdout)
            state[kind] = parsed["active"]
            if kind == "recording":
                state["paused"] = parsed["paused"]
        state["ready"] = True
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        state["error"] = str(error) if isinstance(error, RuntimeError) else "Could not read OBS status"
    return state


DURATION_UNITS = {"d": 86400, "h": 3600, "m": 60, "s": 1, "ms": 0.001, "µs": 1e-6, "us": 1e-6, "ns": 1e-9}


def parse_duration(text):
    """Seconds in obs-cmd's timecode: Rust's 1h2m3s4ms form, or HH:MM:SS(.mmm)."""
    text = text.strip()
    if ":" in text:
        seconds = 0.0
        for part in text.split(":"):
            seconds = seconds * 60 + float(part)
        return seconds
    parts = re.findall(r"(\d+(?:\.\d+)?)(ms|µs|us|ns|d|h|m|s)", text)
    if not parts or "".join(number + unit for number, unit in parts) != text:
        raise ValueError('Unknown OBS timecode: {text}'.format(text=f'{text}'))
    return sum(float(number) * DURATION_UNITS[unit] for number, unit in parts)


def details():
    """Status plus what the recording popup shows: elapsed times, size, scenes, mic and camera."""
    outputs = {}
    state = status(outputs)
    if not state["ready"] or not (state["recording"] or state["streaming"]):
        return state
    try:
        command = websocket_command()
        if state["recording"]:
            recording = obs_options.fields(outputs["recording"])
            state["recordingSeconds"] = parse_duration(recording.get("Timecode", "0s"))
            state["recordingBytes"] = int(recording.get("Bytes", "0") or 0)
        if state["streaming"]:
            streaming = obs_options.fields(outputs["streaming"])
            state["streamingSeconds"] = int(streaming.get("Duration", "0ms").removesuffix("ms") or 0) / 1000
        state["scenes"] = obs_options.scenes(command)
        state["scene"] = obs_options.current_scene(command)
        options = obs_options.capture_options()
        microphones = options["mic"]["sources"]
        state["mic"] = {"available": bool(microphones),
                        "muted": bool(microphones) and all(obs_options.microphone_muted(command, name) for name in microphones)}
        state["webcam"] = {"available": options["webcam"]["available"], "enabled": options["webcam"]["enabled"]}
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        state["detailsError"] = str(error) if isinstance(error, RuntimeError) else "Could not read OBS details"
    return state


def record_directory(command):
    try:
        directory = obs_options.fields(obs_options.obs_output(command, ["record-directory", "get"], "")).get("Current record directory", "")
    except (RuntimeError, OSError, subprocess.TimeoutExpired):
        directory = ""
    return Path(directory) if directory else records_folder()


def announce_saved(command, stopped_at):
    """Offer Open folder / Copy path for the file the stop just finished, in the background."""
    directory = record_directory(command)
    try:
        files = [path for path in directory.iterdir() if path.is_file() and path.stat().st_mtime >= stopped_at - 5]
    except OSError:
        return
    if files:
        newest = max(files, key=lambda path: path.stat().st_mtime)
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "notify-saved", str(newest)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)


def notify_saved(path, screenshot=False, copied=False):
    """A saved screenshot offers Open, Edit, Beautify, Pin and its folder; a recording Open, its folder and its path."""
    path = Path(path)
    title = tr('Screenshot saved and copied') if copied else tr('Screenshot saved')
    actions = ([("open", tr('Open image')), ("edit", tr('Edit image')), ("beautify", tr('Beautify')), ("pin", tr('Pin on screen')),
                ("folder", tr('Open folder'))] if screenshot
               else [("open", tr('Play recording')), ("folder", tr('Open folder')), ("copy", tr('Copy path'))])
    chosen = subprocess.run(["notify-send", "--app-name=" + ("Screenshot" if screenshot else "OBS Studio"),
                             "--icon=" + (str(path) if screenshot else "com.obsproject.Studio"), "--wait",
                             *[f"--action={key}={label}" for key, label in actions],
                             title if screenshot else tr('Recording saved'), path.name],
                            capture_output=True, text=True).stdout.strip()
    if chosen in {"folder", "open"}:
        subprocess.Popen(app_command(["xdg-open", str(path.parent if chosen == "folder" else path)]),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    elif chosen == "edit":
        # The editor saves over the screenshot it opened, like editing right after capture.
        subprocess.Popen(app_command(["satty", "-f", str(path), "-o", str(path), "--early-exit",
                                      "--copy-command", "wl-copy --type image/png", "--actions-on-escape", "exit",
                                      "--app-id", "dev.local.ScreenshotEditor", "--title", "Screenshot",
                                      "--disable-notifications"]),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    elif chosen in {"beautify", "pin"}:
        call = ["beautify", "open"] if chosen == "beautify" else ["pins", "add"]
        subprocess.run(["eitr-shell", "desktop-bar", "ipc", "call", "--", *call, str(path)], capture_output=True, timeout=5)
    elif chosen == "copy":
        subprocess.run(["wl-copy", "--", str(path)], check=False)


def close_if_idle():
    state = status()
    for _ in range(10):
        if not state["ready"] or state["streaming"] or not state["recording"]:
            break
        time.sleep(0.25)
        state = status()
    if not state["ready"] or not state["running"] or state["recording"] or state["streaming"]:
        return False
    processes = subprocess.run(["pgrep", "-x", "obs"], capture_output=True, text=True)
    pids = processes.stdout.split()
    # WebSocket controls one instance; never close unrelated OBS instances.
    if processes.returncode or len(pids) != 1 or not pids[0].isdigit():
        return False
    pid = int(pids[0])
    clients = subprocess.run(["hyprctl", "-j", "clients"], capture_output=True, text=True, timeout=2)
    if clients.returncode == 0:
        for client in json.loads(clients.stdout):
            if client.get("pid") == pid and client.get("class") == "com.obsproject.Studio":
                target = json.dumps("address:" + client["address"])
                result = subprocess.run(["hyprctl", "eval", f"hl.dispatch(hl.dsp.window.close({{ window = {target} }}))"], capture_output=True, timeout=2)
                if result.returncode == 0:
                    return True
    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    return True


def control(action, argument=None):
    actions = {
        "record": ["recording", "start"], "stop": ["recording", "stop"],
        "pause": ["recording", "pause"], "resume": ["recording", "resume"],
        "stream": ["streaming", "start"], "stop-stream": ["streaming", "stop"],
    }
    if action == "folder":
        records_folder().mkdir(parents=True, exist_ok=True)
        subprocess.Popen(app_command(["xdg-open", str(records_folder())]), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return ""
    if action not in actions and action not in {"open", "prepare"} | obs_options.LIVE_ACTIONS:
        raise RuntimeError('Unknown OBS command')
    running = subprocess.run(["pgrep", "-x", "obs"], capture_output=True, timeout=2).returncode == 0
    if not running:
        try:
            obs_options.default_scene_collection()
            default_recording_folder()
        except (OSError, configparser.Error):
            pass  # An unreadable profile keeps its folder; recording still works.
        if action in ("record", "stream", "prepare"):
            try:
                obs_screen.follow_focus(obs_options.collection_file(), obs_options.profile_file(), obs_options.set_ini_value)
            except (OSError, configparser.Error, ValueError):
                pass  # OBS then records the display it captured last time.
    if action == "open":
        if running:
            reveal_window()
        else:
            subprocess.Popen(app_command(["obs"]), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
        return "Opened OBS"
    if not running and action not in ("record", "stream", "prepare"):
        raise RuntimeError(tr('OBS is not running'))
    command = websocket_command()
    if not running:
        launch_background()
        for _ in range(30):
            try:
                if subprocess.run(command + ["info"], capture_output=True, timeout=2).returncode == 0:
                    break
            except subprocess.TimeoutExpired:
                pass
            time.sleep(0.5)
        else:
            raise RuntimeError(tr('OBS did not become ready; check its startup window'))
    if action == "prepare":
        obs_options.apply_capture_options(command)
        return "OBS ready"
    if action in obs_options.LIVE_ACTIONS:
        return obs_options.live_control(command, action, argument)
    stopped_at = time.time()
    result = subprocess.run(command + actions[action], capture_output=True, timeout=30 if action in {"stop", "stop-stream"} else 8)
    if result.returncode:
        raise RuntimeError(tr('OBS could not apply that command; check its current state'))
    if action == "stop":
        try:
            announce_saved(command, stopped_at)
        except (OSError, RuntimeError, subprocess.SubprocessError, ValueError):
            pass  # The recording is saved; only the notification is lost.
    if action in {"stop", "stop-stream"}:
        close_if_idle()
    return "Command applied"


def capture_options():
    return obs_options.capture_options()


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        if action == "options":
            print(json.dumps(capture_options()))
        elif action == "set-option":
            print(json.dumps(obs_options.save_capture_option(sys.argv[2], sys.argv[3])))
        elif action == "notify-saved":
            notify_saved(sys.argv[2])
        elif action == "notify-screenshot":
            notify_saved(sys.argv[2], screenshot=True, copied=len(sys.argv) > 3 and sys.argv[3] == "both")
        elif action == "default-folder":
            if not obs_options.obs_running():
                obs_options.default_scene_collection()
                default_recording_folder()
        elif action == "details":
            print(json.dumps(details()))
        else:
            print(json.dumps(status()) if action == "status" else control(action, sys.argv[2] if len(sys.argv) > 2 else None))
    except Exception as error:
        message = str(error) if isinstance(error, RuntimeError) else "Could not control OBS"
        if os.environ.get("EITR_BAR_ACTION") == "1":
            print(json.dumps({"error": "outcome-unknown" if isinstance(error, subprocess.TimeoutExpired) else "action-failed",
                              "message": message}))
        else:
            print(message)
        sys.exit(1)
