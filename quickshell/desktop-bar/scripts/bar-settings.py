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
import eitr_appearance
from eitr_choice_lists import BAR_APPEARANCES, BAR_LAYOUTS, ids, next_choice
import tempfile
import subprocess


SETTINGS = user_config("quickshell/desktop-bar/bar-settings.json")
ICON_ORDER_ZONES = ("left", "clockStart", "clockEnd", "right")
DEFAULTS = {"appearance": "solid", "layout": "unified", "edge": "top", "pinned": "no", "screens": "main", "autohide": "no", "reduceMotion": "no", "mediaStyle": "bars", "dock": "yes", "clock": "12h", "moments": True, "blur-strength": "medium", "lyrics": "no", "islandStyle": "floating", "sideStyle": "slopes", "dockPreviews": "yes"}
OPTIONS = {
    "moments": {False, True},
    "blur-strength": {"light", "medium", "strong"},
    "appearance": set(ids(BAR_APPEARANCES)),
    "layout": set(ids(BAR_LAYOUTS)),
    "edge": {"top", "bottom", "left", "right"},
    "pinned": {"yes", "no"},
    # The bar on the main display only, or one bar on every display.
    "screens": {"main", "all"},
    "autohide": {"yes", "no"},
    "dock": {"yes", "no"},
    "dockPreviews": {"yes", "no"},
    "reduceMotion": {"yes", "no"},
    "mediaStyle": {"bars", "line"},
    # 12-hour time with AM/PM, or 24-hour time.
    "clock": {"12h", "24h"},
    # Look up song lyrics on LRCLIB for Drop (sends each song's title, artist and album).
    "lyrics": {"yes", "no"},
    # Islands, Dynamic and Drop: pills floating off the screen edge, or attached to it.
    "islandStyle": {"floating", "attached"},
    # Tabs and Centered: 45° slopes into the screen edge, or straight sides.
    "sideStyle": {"slopes", "straight"},
}


def _sanitize_icon_order(raw):
    if not isinstance(raw, dict) or not any(isinstance(raw.get(zone), list) for zone in ICON_ORDER_ZONES):
        return None
    cleaned = {zone: [] for zone in ICON_ORDER_ZONES}
    seen = set()
    for zone in ICON_ORDER_ZONES:
        entries = raw.get(zone)
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, str) and entry and entry not in seen:
                seen.add(entry)
                cleaned[zone].append(entry)
    return cleaned


def _validate_icon_order(value):
    if value is None or value in ("null", "reset", ""):
        return None
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid iconOrder: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"Invalid iconOrder: {value}")
    unknown = set(value) - set(ICON_ORDER_ZONES)
    if unknown:
        raise ValueError(f"Invalid iconOrder zones: {', '.join(sorted(unknown))}")
    cleaned = {zone: [] for zone in ICON_ORDER_ZONES}
    seen = set()
    for zone in ICON_ORDER_ZONES:
        if zone not in value:
            continue
        entries = value[zone]
        if not isinstance(entries, list):
            raise ValueError(f"Invalid iconOrder list for {zone}")
        for entry in entries:
            if not isinstance(entry, str) or not entry:
                raise ValueError(f"Invalid iconOrder id in {zone}: {entry}")
            if entry in seen:
                raise ValueError(f"Duplicate iconOrder id: {entry}")
            seen.add(entry)
            cleaned[zone].append(entry)
    return cleaned


def read_settings():
    data = read_json(SETTINGS)
    if data.get("layout") == "split":
        data["layout"] = "centered"
    result = {**data, **{
        key: data.get(key) if type(data.get(key)) is type(DEFAULTS[key]) and data[key] in choices else DEFAULTS[key]
        for key, choices in OPTIONS.items()
    }}
    if "iconOrder" in result:
        sanitized = _sanitize_icon_order(result["iconOrder"])
        if sanitized is None:
            result.pop("iconOrder", None)
        else:
            result["iconOrder"] = sanitized
    return result


def save_settings(data):
    settings = read_settings()
    previous_appearance = settings["appearance"]
    remove_icon_order = False
    for key, value in data.items():
        if key == "iconOrder":
            validated = _validate_icon_order(value)
            if validated is None:
                settings.pop("iconOrder", None)
                remove_icon_order = True
            else:
                settings["iconOrder"] = validated
            continue
        if key == "moments" and value in ("true", "false"):
            value = value == "true"
        if key not in OPTIONS or type(value) is not type(DEFAULTS[key]) or value not in OPTIONS[key]:
            raise ValueError('Invalid {key}: {value}'.format(key=f'{key}', value=f'{value}'))
        settings[key] = value
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".bar-settings-", dir=SETTINGS.parent)
    try:
        payload = {**read_json(SETTINGS), **settings, "version": 1}
        if remove_icon_order:
            payload.pop("iconOrder", None)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
            handle.write("\n")
        os.replace(temp_name, SETTINGS)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    if settings["appearance"] != previous_appearance:
        refresh_walker_appearance()
    if 'blur-strength' in data:
        eitr_appearance.generate_blur()
        eitr_appearance.reload_compositor()
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
        if sys.argv[1:] == ["summary"]:
            result = {"current": read_settings(), "available": True,
                      "choices": {key: [{"value": value, "label": value, "available": True}
                                        for value in sorted(values)] for key, values in OPTIONS.items()}}
        elif sys.argv[1:] == ["status"]:
            result = read_settings()
        elif len(sys.argv) == 3 and sys.argv[1] == "get" and (sys.argv[2] in OPTIONS or sys.argv[2] == "iconOrder"):
            value = read_settings().get(sys.argv[2])
            print(json.dumps(value) if isinstance(value, (bool, dict)) or value is None else value)
            return 0
        elif len(sys.argv) in {5, 6, 7, 8, 9, 10, 11, 12, 13} and sys.argv[1] == "set-all":
            result = save_settings(dict(zip(DEFAULTS, sys.argv[2:])))
        elif len(sys.argv) == 4 and sys.argv[1] == "set":
            result = save_settings({sys.argv[2]: sys.argv[3]})
            live_value = (json.dumps(result["iconOrder"], separators=(",", ":")) if "iconOrder" in result else "null") if sys.argv[2] == "iconOrder" else sys.argv[3]
            apply_live(sys.argv[2], live_value)
        elif len(sys.argv) == 3 and sys.argv[1] == "toggle" and sys.argv[2] in {"appearance", "layout"}:
            key = sys.argv[2]
            current = read_settings()[key]
            value = next_choice(BAR_APPEARANCES if key == "appearance" else BAR_LAYOUTS, current)
            result = save_settings({key: value})
            apply_live(key, value)
        else:
            raise ValueError("Usage: bar-settings.py status|set KEY VALUE|set-all APPEARANCE LAYOUT EDGE [PINNED [SCREENS [AUTOHIDE [REDUCE_MOTION [MEDIA_STYLE [DOCK [CLOCK [MOMENTS]]]]]]]]")
        print(json.dumps(result))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
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
