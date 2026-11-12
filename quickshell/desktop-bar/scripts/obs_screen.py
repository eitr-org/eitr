"""OBS records the display that has focus when Eitr starts it.

OBS's screen sources remember the display they were given (a portal restore token) and
OBS only asks the portal again when it starts, so this runs while OBS is closed: it forgets
that choice for the visible screen sources of the current scene, leaves a short-lived
request that Eitr's share picker (hypr/scripts/share-picker.py) answers with the focused
display, and sizes OBS's canvas to that display. An OBS that is already open keeps what it
captures."""
import json
import os
from pathlib import Path
import subprocess
import time

SCREEN_SOURCE = "pipewire-screen-capture-source"
# Long enough for OBS to start and ask; the picker also stops after one answer per source.
REQUEST_SECONDS = 30


def request_path():
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return Path(runtime) / "eitr/share-request.json"


def focused_output():
    """Name and pixel size of the focused display, or None outside Hyprland."""
    try:
        result = subprocess.run(["hyprctl", "-j", "monitors"], capture_output=True, text=True, timeout=2)
        monitors = json.loads(result.stdout) if result.returncode == 0 else []
    except (OSError, subprocess.SubprocessError, ValueError):
        return None
    monitor = next((monitor for monitor in monitors if monitor.get("focused")), None)
    if not monitor or not monitor.get("name"):
        return None
    width, height = int(monitor["width"]), int(monitor["height"])
    # Odd transforms are rotated a quarter turn: the captured image is taller than wide.
    if int(monitor.get("transform", 0)) % 2:
        width, height = height, width
    return {"name": monitor["name"], "width": width, "height": height}


def forget_screens(collection):
    """Drop the remembered display of the current scene's visible screen sources; returns how many."""
    sources = collection.get("sources", [])
    by_name = {source.get("name"): source for source in sources}
    scene = by_name.get(collection.get("current_scene"), {})
    visible = {item.get("name") for item in scene.get("settings", {}).get("items", []) if item.get("visible", True)}
    count = 0
    for source in sources:
        if source.get("id") == SCREEN_SOURCE and source.get("name") in visible:
            source.setdefault("settings", {}).pop("RestoreToken", None)
            count += 1
    return count


def canvas_text(text, width, height, set_ini_value):
    """Profile TEXT with the canvas at the display's size. A scaled output keeps its ratio to the canvas."""
    import configparser
    profile = configparser.ConfigParser(interpolation=None, strict=False)
    profile.optionxform = str
    profile.read_string(text)
    base = (profile.getint("Video", "BaseCX", fallback=0), profile.getint("Video", "BaseCY", fallback=0))
    output = (profile.getint("Video", "OutputCX", fallback=0), profile.getint("Video", "OutputCY", fallback=0))
    scale = output[1] / base[1] if base[1] and output[1] and output != base else 1
    # Encoders want even sizes.
    scaled = (int(width * scale) // 2 * 2, int(height * scale) // 2 * 2)
    for key, value in (("BaseCX", width), ("BaseCY", height), ("OutputCX", scaled[0]), ("OutputCY", scaled[1])):
        text = set_ini_value(text, "Video", key, str(value))
    return text


def write_atomically(path, text, mode=0o600):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = path.with_name("." + path.name + ".eitr")
    temporary.write_text(text)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def follow_focus(collection_path, profile_path, set_ini_value):
    """Prepare a closed OBS to capture the focused display; returns its name, or None."""
    output = focused_output()
    if output is None:
        return None
    try:
        collection = json.loads(collection_path.read_text())
    except (OSError, ValueError):
        return None
    count = forget_screens(collection)
    if not count:
        return None
    write_atomically(request_path(), json.dumps({"output": output["name"], "remaining": count,
                                                 "expires": time.time() + REQUEST_SECONDS}))
    write_atomically(collection_path, json.dumps(collection, indent=4), 0o644)
    try:
        text = profile_path.read_text()
    except FileNotFoundError:
        text = ""
    updated = canvas_text(text, output["width"], output["height"], set_ini_value)
    if updated != text:
        write_atomically(profile_path, updated, 0o644)
    return output["name"]
