"""OBS recording options, scene collections, and input devices."""
import configparser
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import config as user_config, read_settings, write_settings
from eitr_i18n import tr


OPTIONS_FILE = user_config("quickshell/desktop-bar/obs-recording.json")


def collection_file():
    config = configparser.ConfigParser(interpolation=None)
    config.read(user_config("obs-studio/user.ini"))
    collection = Path(config.get("Basic", "SceneCollectionFile", fallback="Untitled.json")).name
    if not collection.endswith(".json"):
        collection += ".json"
    return user_config("obs-studio/basic/scenes") / collection


def profile_file():
    user = configparser.ConfigParser(interpolation=None)
    user.read(user_config("obs-studio/user.ini"))
    return user_config("obs-studio/basic/profiles") / Path(user.get("Basic", "ProfileDir", fallback="Untitled")).name / "basic.ini"


def scene_collection():
    try:
        return json.loads(collection_file().read_text())
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


def obs_running():
    return subprocess.run(["pgrep", "-x", "obs"], capture_output=True, timeout=2).returncode == 0


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


def fields(text):
    """`Key: value` lines from obs-cmd output, keys without their indentation."""
    return {key.strip(): value.strip() for key, separator, value in
            (line.partition(":") for line in text.splitlines()) if separator}


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
