#!/usr/bin/env python3
"""Persistent appearance and placement settings for the desktop bar."""

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
from eitr_paths import code, config as user_config, read_settings as read_json, write_settings
from eitr_i18n import tr
import tempfile
import subprocess


SETTINGS = user_config("quickshell/desktop-bar/bar-settings.json")
DEFAULTS = {"appearance": "solid", "layout": "unified", "edge": "top", "pinned": "no", "screens": "main", "autohide": "no", "reduceMotion": "no", "mediaStyle": "bars"}
OPTIONS = {
    "appearance": {"transparent", "solid"},
    "layout": {"unified", "centered", "notch"},
    "edge": {"top", "bottom", "left", "right"},
    "pinned": {"yes", "no"},
    # The bar on the main display only, or one bar on every display.
    "screens": {"main", "all"},
    "autohide": {"yes", "no"},
    "reduceMotion": {"yes", "no"},
    "mediaStyle": {"bars", "line"},
}


def read_settings():
    data = read_json(SETTINGS)
    if data.get("layout") == "split":
        data["layout"] = "centered"
    return {**data, **{
        key: data.get(key) if isinstance(data.get(key), str) and data[key] in choices else DEFAULTS[key]
        for key, choices in OPTIONS.items()
    }}


def save_settings(data):
    settings = read_settings()
    previous_appearance = settings["appearance"]
    for key, value in data.items():
        if key not in OPTIONS or value not in OPTIONS[key]:
            raise ValueError('Invalid {key}: {value}'.format(key=f'{key}', value=f'{value}'))
        settings[key] = value
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".bar-settings-", dir=SETTINGS.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump({**read_json(SETTINGS), **settings, "version": 1}, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, SETTINGS)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    if settings["appearance"] != previous_appearance:
        refresh_walker_appearance()
    return settings


def refresh_walker_appearance():
    generator = code("walker/scripts/themes/walker.sh")
    if not generator.is_file():
        return
    try:
        subprocess.run(["bash", str(generator)], check=False, timeout=15,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.TimeoutExpired):
        pass


def main():
    try:
        if sys.argv[1:] == ["status"]:
            result = read_settings()
        elif len(sys.argv) == 3 and sys.argv[1] == "get" and sys.argv[2] in OPTIONS:
            print(read_settings()[sys.argv[2]])
            return 0
        elif len(sys.argv) in {5, 6, 7, 8, 9, 10} and sys.argv[1] == "set-all":
            result = save_settings(dict(zip(DEFAULTS, sys.argv[2:])))
        elif len(sys.argv) == 4 and sys.argv[1] == "set":
            result = save_settings({sys.argv[2]: sys.argv[3]})
            apply_live(sys.argv[2], sys.argv[3])
        elif len(sys.argv) == 3 and sys.argv[1] == "toggle" and sys.argv[2] in {"appearance", "layout"}:
            key = sys.argv[2]
            current = read_settings()[key]
            value = ("transparent" if current == "solid" else "solid") if key == "appearance" else ({"unified": "centered", "centered": "notch", "notch": "unified"}[current])
            result = save_settings({key: value})
            apply_live(key, value)
        else:
            raise ValueError("Usage: bar-settings.py status|set KEY VALUE|set-all APPEARANCE LAYOUT EDGE [PINNED [SCREENS [AUTOHIDE [REDUCE_MOTION [MEDIA_STYLE]]]]]")
        print(json.dumps(result))
    except (OSError, ValueError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


def apply_live(key, value):
    try:
        subprocess.run(
            ["eitr-shell", "desktop-bar", "ipc", "call", "--", "bar", "update", key, value],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=3, check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        pass


if __name__ == "__main__":
    sys.exit(main())
