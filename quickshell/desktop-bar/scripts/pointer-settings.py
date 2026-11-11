#!/usr/bin/env python3
"""Mouse and touchpad settings for Settings > Input: pointer speed, acceleration, natural
scrolling, left-handed buttons and, with a touchpad, tap to click and typing protection.

Choices that differ from the defaults are saved machine-locally in hypr/pointer.lua, which
hyprland.lua reads over its own defaults; Reset removes the file. Each change reloads
Hyprland, as keyboard layouts do.

  pointer-settings.py summary          JSON: every setting and whether a touchpad exists
  pointer-settings.py set KEY VALUE    save one setting (see DEFAULTS for the keys)
  pointer-settings.py reset            back to the defaults
"""
import json
from pathlib import Path
import re
import subprocess
import sys

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import config as user_config

STATE = user_config("hypr/pointer.lua")
# Hyprland's own defaults, which hyprland.lua also falls back to.
DEFAULTS = {
    "sensitivity": 0.0,
    "acceleration": True,
    "natural_scroll": False,
    "left_handed": False,
    "touchpad_natural_scroll": False,
    "tap_to_click": True,
    "disable_while_typing": True,
}


LINE = re.compile(r"\s*([a-z_]+)\s*=\s*(true|false|-?[0-9]+(?:\.[0-9]+)?),?\s*")


def load():
    """The saved choices over the defaults. The file is the Lua table save() writes, one
    `key = value,` per line; anything else in it (a hand edit) is ignored."""
    settings = dict(DEFAULTS)
    try:
        lines = STATE.read_text().splitlines() if STATE.is_file() else []
    except OSError:
        lines = []
    for line in lines:
        match = LINE.fullmatch(line)
        if not match or match[1] not in DEFAULTS:
            continue
        key, text = match[1], match[2]
        if key == "sensitivity" and text not in ("true", "false"):
            settings[key] = max(-1.0, min(1.0, float(text)))
        elif key != "sensitivity" and text in ("true", "false"):
            settings[key] = text == "true"
    return settings


def save(settings):
    changed = {key: value for key, value in settings.items() if value != DEFAULTS[key]}
    if not changed:
        STATE.unlink(missing_ok=True)
        return
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_name(STATE.name + ".new")
    lines = ["\t%s = %s," % (key, ("true" if value else "false") if isinstance(value, bool) else repr(value))
             for key, value in sorted(changed.items())]
    temporary.write_text("-- Written by Settings > Input; Reset removes it.\nreturn {\n" + "\n".join(lines) + "\n}\n")
    temporary.replace(STATE)


def touchpad_present():
    try:
        devices = json.loads(subprocess.run(["hyprctl", "devices", "-j"], capture_output=True, text=True,
                                            timeout=5, check=True).stdout)
    except (OSError, ValueError, subprocess.SubprocessError):
        return False
    return any(word in str(mouse.get("name", "")).lower() for mouse in devices.get("mice", [])
               for word in ("touchpad", "trackpad"))


def reload():
    subprocess.run(["hyprctl", "reload"], capture_output=True, timeout=10, check=False)


def parse(key, text):
    if key not in DEFAULTS:
        raise ValueError("unknown setting: " + key)
    if key == "sensitivity":
        value = float(text)
        if not -1 <= value <= 1:
            raise ValueError("sensitivity is between -1 and 1")
        return round(value, 2)
    if text not in ("true", "false"):
        raise ValueError(key + " is true or false")
    return text == "true"


def main(arguments):
    if arguments == ["summary"]:
        print(json.dumps(dict(load(), touchpad=touchpad_present(), customized=STATE.is_file())))
    elif len(arguments) == 3 and arguments[0] == "set":
        settings = load()
        settings[arguments[1]] = parse(arguments[1], arguments[2])
        save(settings)
        reload()
    elif arguments == ["reset"]:
        STATE.unlink(missing_ok=True)
        reload()
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except ValueError as error:
        raise SystemExit(str(error))
