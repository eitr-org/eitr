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
from eitr_paths import code, config as user_config, read_settings, write_settings
from eitr_app import app_command
from eitr_i18n import tr
import secrets
import shlex
import signal
import subprocess
import tempfile
import time
import uuid
from urllib.parse import quote


OPTIONS_FILE = user_config("quickshell/desktop-bar/obs-recording.json")


def scene_collection():
    config = configparser.ConfigParser(interpolation=None)
    config.read(user_config("obs-studio/user.ini"))
    collection = Path(config.get("Basic", "SceneCollectionFile", fallback="Untitled.json")).name
    if not collection.endswith(".json"):
        collection += ".json"
    try:
        return json.loads((user_config("obs-studio/basic/scenes") / collection).read_text())
    except (OSError, ValueError):
        return {}


def capture_options():
    scene = scene_collection()
    sources = list(scene.get("sources", [])) + [value for value in scene.values() if isinstance(value, dict) and value.get("id")]
    roles = {
        "audio": [source for source in sources if source.get("id") in {"pulse_output_capture", "wasapi_output_capture"}],
        "mic": [source for source in sources if source.get("id") in {"pulse_input_capture", "wasapi_input_capture"}],
        "webcam": [source for source in sources if source.get("id") in {"v4l2_input", "av_capture_input", "dshow_input"}],
    }
    saved = read_settings(OPTIONS_FILE)
    if not isinstance(saved, dict):
        saved = {}
    result = {}
    for key, inputs in roles.items():
        default = any(not source.get("muted", False) for source in inputs) if key != "webcam" else False
        enabled = saved.get(key) if isinstance(saved.get(key), bool) else default
        result[key] = {"enabled": enabled, "available": bool(inputs), "sources": [source["name"] for source in inputs]}
    return result


def save_capture_option(key, value):
    if key not in {"audio", "mic", "webcam"} or value not in {"true", "false"}:
        raise RuntimeError('Invalid recording option')
    options = capture_options()
    if value == "true" and not options[key]["available"]:
        raise RuntimeError(tr('Configure this source in OBS first'))
    saved = {name: option["enabled"] for name, option in options.items()}
    saved[key] = value == "true"
    write_settings(OPTIONS_FILE, saved)
    return capture_options()


def apply_capture_options(command):
    scene = scene_collection()
    sources = {source.get("name"): source for source in scene.get("sources", [])}
    active_scene = sources.get(scene.get("current_scene"), {})
    visible = {item.get("name") for item in active_scene.get("settings", {}).get("items", []) if item.get("visible", True)}
    if not any(source.get("id") == "pipewire-screen-capture-source" and name in visible for name, source in sources.items()):
        raise RuntimeError(tr('Set up full-screen monitor capture in OBS first'))
    options = capture_options()
    for key in ("audio", "mic"):
        for name in options[key]["sources"]:
            result = subprocess.run(command + ["audio", "unmute" if options[key]["enabled"] else "mute", name], capture_output=True, timeout=3)
            if result.returncode:
                raise RuntimeError(tr('Could not apply recording audio settings'))
    cameras = options["webcam"]
    if cameras["sources"]:
        current = subprocess.run(command + ["scene", "current"], capture_output=True, text=True, timeout=3)
        if current.returncode:
            raise RuntimeError(tr('Could not read the current OBS scene'))
        scene = next((line.removeprefix("Current scene:").strip()
                      for line in current.stdout.splitlines()
                      if line.startswith("Current scene:")), "")
        if not scene:
            raise RuntimeError(tr('Could not read the current OBS scene'))
        for name in cameras["sources"]:
            result = subprocess.run(command + ["scene-item", "enable" if cameras["enabled"] else "disable", scene, name], capture_output=True, timeout=3)
            if result.returncode:
                raise RuntimeError(tr('Could not apply recording webcam settings'))


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


def set_ini_value(text, section, key, value):
    """TEXT with KEY in [SECTION] set to VALUE, keeping every other line as OBS wrote it."""
    lines = text.splitlines()
    header = f"[{section}]"
    if header not in lines:
        return "\n".join(lines + ([""] if lines else []) + [header, f"{key}={value}"]) + "\n"
    start = lines.index(header) + 1
    end = next((index for index in range(start, len(lines)) if lines[index].startswith("[")), len(lines))
    for index in range(start, end):
        if lines[index].split("=", 1)[0] == key:
            lines[index] = f"{key}={value}"
            break
    else:
        lines.insert(end, f"{key}={value}")
    return "\n".join(lines) + "\n"


def default_recording_folder():
    """Point OBS's recording folder at ~/Videos/Records while it is still OBS's default.

    OBS rewrites its profile when it exits, so callers run this only while OBS is
    closed; a folder anyone chose is never replaced. Returns whether the profile changed.
    """
    user = configparser.ConfigParser(interpolation=None)
    user.read(user_config("obs-studio/user.ini"))
    profile = user_config("obs-studio/basic/profiles") / Path(user.get("Basic", "ProfileDir", fallback="Untitled")).name / "basic.ini"
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
            updated = set_ini_value(updated, section, key, str(records_folder()))
    records_folder().mkdir(parents=True, exist_ok=True)
    if updated == text:
        return False
    profile.parent.mkdir(parents=True, exist_ok=True)
    temporary = profile.with_name(".basic.ini.eitr")
    temporary.write_text(updated)
    os.replace(temporary, profile)
    return True


def first_capture_device():
    """Only select video nodes advertising video capture, never metadata nodes."""
    import fcntl
    import struct
    for device in sorted(Path("/dev").glob("video*")):
        try:
            with device.open("rb", buffering=0) as stream:
                capabilities = bytearray(104)
                fcntl.ioctl(stream.fileno(), 0x80685600, capabilities)
            flags, device_flags = struct.unpack_from("II", capabilities, 84)
            if flags & 0x80000000:
                flags = device_flags
            if flags & (0x1 | 0x1000):
                return str(device)
        except OSError:
            continue
    return None


def default_scene_collection():
    """Seed a collection only for an unused, closed OBS configuration."""
    directory = user_config("obs-studio/basic/scenes")
    if obs_running() or any(directory.glob("*.json")):
        return False
    settings_path = user_config("obs-studio/user.ini")
    try:
        original = settings_path.read_text()
    except FileNotFoundError:
        original = ""
    settings = configparser.ConfigParser(interpolation=None)
    settings.read_string(original)

    def source(name, source_id, values):
        return {"name": name, "uuid": str(uuid.uuid4()), "id": source_id,
                "versioned_id": source_id, "settings": values, "muted": False,
                "volume": 1.0, "mixers": 255, "sync": 0, "flags": 0}

    screen = source(tr("Screen"), "pipewire-screen-capture-source", {})
    device = first_capture_device()
    camera = source(tr("Camera"), "v4l2_input", {"device_id": device} if device else {})
    items = []
    for index, capture in enumerate((screen, camera), start=1):
        items.append({"name": capture["name"], "source_uuid": capture["uuid"],
                      "uuid": str(uuid.uuid4()), "id": index, "visible": index == 1,
                      "locked": False, "pos": {"x": 0.0, "y": 0.0},
                      "scale": {"x": 1.0, "y": 1.0}, "rot": 0.0,
                      "align": 5, "bounds_type": 0, "bounds_align": 0,
                      "bounds": {"x": 0.0, "y": 0.0}})
    scene = source("Scene", "scene", {"items": items, "id_counter": 2})
    collection = {"name": "Untitled", "current_scene": "Scene", "current_program_scene": "Scene",
                  "scene_order": [{"name": "Scene"}], "sources": [screen, camera, scene],
                  "DesktopAudioDevice1": source(tr("Desktop Audio"), "pulse_output_capture", {"device_id": "default"}),
                  "AuxAudioDevice1": source("Mic/Aux", "pulse_input_capture", {"device_id": "default"})}
    updated = original
    for key, value in (("SceneCollection", "Untitled"), ("SceneCollectionFile", "Untitled.json")):
        if not settings.get("Basic", key, fallback=""):
            updated = set_ini_value(updated, "Basic", key, value)
    directory.mkdir(parents=True, exist_ok=True)
    # Exclusive creation also protects a collection created since the initial check.
    with (directory / "Untitled.json").open("x") as output:
        json.dump(collection, output, indent=4)
    if updated != original:
        descriptor, temporary = tempfile.mkstemp(prefix=".user-", dir=settings_path.parent)
        try:
            with os.fdopen(descriptor, "w") as output:
                output.write(updated)
            os.replace(temporary, settings_path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return True


def obs_running():
    return subprocess.run(["pgrep", "-x", "obs"], capture_output=True, timeout=2).returncode == 0


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
    if obs_running():
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


def fields(text):
    """`Key: value` lines from obs-cmd output, keys without their indentation."""
    return {key.strip(): value.strip() for key, separator, value in
            (line.partition(":") for line in text.splitlines()) if separator}


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


def obs_output(command, arguments, error):
    result = subprocess.run(command + arguments, capture_output=True, text=True, timeout=3)
    if result.returncode:
        raise RuntimeError(error)
    return result.stdout


def current_scene(command):
    scene = fields(obs_output(command, ["scene", "current"], "Could not read the current OBS scene")).get("Current scene", "")
    if not scene:
        raise RuntimeError(tr('Could not read the current OBS scene'))
    return scene


def scenes(command):
    listing = obs_output(command, ["scene", "list"], "Could not list OBS scenes")
    return [line.strip()[2:] for line in listing.splitlines() if line.strip().startswith("- ")]


def microphone_muted(command, name):
    """obs-cmd answers `Audio device 'NAME' is: muted` (or `unmuted`)."""
    answer = obs_output(command, ["audio", "status", name], "Could not read the OBS microphone")
    return answer.strip().rsplit(":", 1)[-1].strip() == "muted"


def details():
    """Status plus what the recording popup shows: elapsed times, size, scenes, mic and camera."""
    outputs = {}
    state = status(outputs)
    if not state["ready"] or not (state["recording"] or state["streaming"]):
        return state
    try:
        command = websocket_command()
        if state["recording"]:
            recording = fields(outputs["recording"])
            state["recordingSeconds"] = parse_duration(recording.get("Timecode", "0s"))
            state["recordingBytes"] = int(recording.get("Bytes", "0") or 0)
        if state["streaming"]:
            streaming = fields(outputs["streaming"])
            state["streamingSeconds"] = int(streaming.get("Duration", "0ms").removesuffix("ms") or 0) / 1000
        state["scenes"] = scenes(command)
        state["scene"] = current_scene(command)
        options = capture_options()
        microphones = options["mic"]["sources"]
        state["mic"] = {"available": bool(microphones),
                        "muted": bool(microphones) and all(microphone_muted(command, name) for name in microphones)}
        state["webcam"] = {"available": options["webcam"]["available"], "enabled": options["webcam"]["enabled"]}
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
        state["detailsError"] = str(error) if isinstance(error, RuntimeError) else "Could not read OBS details"
    return state


def record_directory(command):
    try:
        directory = fields(obs_output(command, ["record-directory", "get"], "")).get("Current record directory", "")
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
    path = Path(path)
    title = tr('Screenshot saved and copied') if copied else tr('Screenshot saved')
    actions = (["--action=open=" + tr('Open image'), "--action=folder=" + tr('Open folder')]
               if screenshot else ["--action=folder=Open folder", "--action=copy=Copy path"])
    chosen = subprocess.run(["notify-send", "--app-name=" + ("Screenshot" if screenshot else "OBS Studio"),
                             "--icon=" + (str(path) if screenshot else "com.obsproject.Studio"), "--wait",
                             *actions, title if screenshot else tr('Recording saved'), path.name],
                            capture_output=True, text=True).stdout.strip()
    if chosen in {"folder", "open"}:
        subprocess.Popen(app_command(["xdg-open", str(path.parent if chosen == "folder" else path)]),
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
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


def live_control(command, action, argument):
    """Actions on an active recording or stream that are not plain obs-cmd calls."""
    if action == "chapter":
        result = subprocess.run(command + ["recording", "create-chapter"], capture_output=True, timeout=8)
        if result.returncode:
            raise RuntimeError(tr('Chapters need the Hybrid MP4 recording format (OBS Settings > Output)'))
        return "Chapter added"
    if action in {"mic-mute", "mic-unmute"}:
        microphones = capture_options()["mic"]["sources"]
        if not microphones:
            raise RuntimeError(tr('Add a microphone source in OBS first'))
        for name in microphones:
            obs_output(command, ["audio", "mute" if action == "mic-mute" else "unmute", name],
                       "Could not change the OBS microphone")
        return "Microphone updated"
    if action in {"camera-on", "camera-off"}:
        cameras = capture_options()["webcam"]["sources"]
        if not cameras:
            raise RuntimeError(tr('Add a camera source in OBS first'))
        scene = current_scene(command)
        for name in cameras:
            obs_output(command, ["scene-item", "enable" if action == "camera-on" else "disable", scene, name],
                       "Could not change the OBS camera")
        save_capture_option("webcam", "true" if action == "camera-on" else "false")
        return "Camera updated"
    if action == "scene":
        if argument not in scenes(command):
            raise RuntimeError(tr('That OBS scene no longer exists'))
        obs_output(command, ["scene", "switch", argument], "Could not switch the OBS scene")
        return "Scene switched"
    return None


LIVE_ACTIONS = {"chapter", "mic-mute", "mic-unmute", "camera-on", "camera-off", "scene"}


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
    if action not in actions and action not in {"open", "prepare"} | LIVE_ACTIONS:
        raise RuntimeError('Unknown OBS command')
    running = subprocess.run(["pgrep", "-x", "obs"], capture_output=True, timeout=2).returncode == 0
    if not running:
        try:
            default_scene_collection()
            default_recording_folder()
        except (OSError, configparser.Error):
            pass  # An unreadable profile keeps its folder; recording still works.
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
        apply_capture_options(command)
        return "OBS ready"
    if action in LIVE_ACTIONS:
        return live_control(command, action, argument)
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


if __name__ == "__main__":
    try:
        action = sys.argv[1]
        if action == "options":
            print(json.dumps(capture_options()))
        elif action == "set-option":
            print(json.dumps(save_capture_option(sys.argv[2], sys.argv[3])))
        elif action == "notify-saved":
            notify_saved(sys.argv[2])
        elif action == "notify-screenshot":
            notify_saved(sys.argv[2], screenshot=True, copied=len(sys.argv) > 3 and sys.argv[3] == "both")
        elif action == "default-folder":
            if not obs_running():
                default_scene_collection()
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
