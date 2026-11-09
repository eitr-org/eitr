#!/usr/bin/env python3
"""Shared corner, gap and window-layout preferences for Eitr and Hyprland."""
import json
import os
import tempfile
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
from eitr_workspaces import preferences as workspace_preferences, DEFAULTS as WORKSPACE_DEFAULTS
from eitr_choice_lists import (WINDOW_GAPS, WINDOW_LAYOUTS, SCROLLING_DIRECTIONS,
                               SCROLLING_WIDTHS, SCROLLING_FOCUS_FIT, WORKSPACE_MODES)
import subprocess

SETTINGS = user_config("eitr/style.json")
DEFINITIONS = Path(__file__).resolve().parent.parent / "corner-styles.json"


def definitions():
    data = json.loads(DEFINITIONS.read_text())
    return data["default"], data["styles"]


def current():
    default, styles = definitions()
    data = read_settings(SETTINGS)
    try:
        value = data.get("corners")
        return value if value in styles else default
    except (OSError, ValueError, AttributeError, TypeError):
        return default


def current_gaps():
    value = read_settings(SETTINGS).get("gaps", "default")
    return value if any(choice["id"] == value for choice in WINDOW_GAPS) else "default"


def generate_gaps():
    choice = next(choice for choice in WINDOW_GAPS if choice["id"] == current_gaps())
    write_generated("window-gaps.lua", f'return {{inner = {int(choice["inner"])}, outer = {int(choice["outer"])}}}\n')


def write_generated(name, content):
    target = SETTINGS.with_name(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="." + name + "-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(content)
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


LAYOUT_CHOICES = {"layout": WINDOW_LAYOUTS, "scrollDirection": SCROLLING_DIRECTIONS,
                  "scrollWidth": SCROLLING_WIDTHS, "scrollFocusFit": SCROLLING_FOCUS_FIT}
LAYOUT_DEFAULTS = {"layout": "dwindle", "scrollDirection": "right", "scrollWidth": "half",
                   "scrollFocusFit": "fit", "scrollFollowFocus": "yes", "scrollFullscreen": "yes"}


def current_layout():
    data = read_settings(SETTINGS)
    result = {}
    for key, default in LAYOUT_DEFAULTS.items():
        options = [choice["id"] for choice in LAYOUT_CHOICES[key]] if key in LAYOUT_CHOICES else ["yes", "no"]
        result[key] = data.get(key) if data.get(key) in options else default
    return result


def generate_layout():
    preference = current_layout()
    def value(key):
        return next(choice["value"] for choice in LAYOUT_CHOICES[key] if choice["id"] == preference[key])
    fields = {"layout": json.dumps(preference["layout"]), "direction": json.dumps(preference["scrollDirection"]),
              "column_width": value("scrollWidth"), "focus_fit_method": value("scrollFocusFit"),
              "follow_focus": "1" if preference["scrollFollowFocus"] == "yes" else "0",
              "fullscreen_on_one_column": "true" if preference["scrollFullscreen"] == "yes" else "false",
              "explicit_column_widths": json.dumps(", ".join(choice["value"] for choice in SCROLLING_WIDTHS))}
    write_generated("window-layout.lua", "return {" + ", ".join(key + " = " + item for key, item in fields.items()) + "}\n")


def scroll_action(arguments):
    allowed = {"focus l", "focus r", "focus u", "focus d", "swapcol l", "swapcol r", "colresize +conf", "colresize -conf"}
    message = " ".join(arguments)
    if message not in allowed:
        raise ValueError("Unknown scrolling action")
    result = subprocess.run(["hyprctl", "-j", "getoption", "general:layout"],
                            capture_output=True, text=True, check=True, timeout=5)
    if json.loads(result.stdout).get("str") == "scrolling":
        subprocess.run(["hyprctl", "dispatch", "layoutmsg", message], check=True, timeout=5)


def select(value, key="corners"):
    options = definitions()[1] if key == "corners" else {choice["id"] for choice in WINDOW_GAPS}
    if key in LAYOUT_DEFAULTS:
        options = {choice["id"] for choice in LAYOUT_CHOICES[key]} if key in LAYOUT_CHOICES else {"yes", "no"}
    if key in WORKSPACE_DEFAULTS:
        if key == "workspaceMode":
            options = {choice["id"] for choice in WORKSPACE_MODES}
        else:
            value = int(value)
            options = range(5, 11) if key == "workspaceCount" else range(2, workspace_preferences(read_settings(SETTINGS))["workspaceCount"] + 1)
    if key not in ("corners", "gaps", *LAYOUT_DEFAULTS, *WORKSPACE_DEFAULTS) or value not in options:
        raise ValueError('Unknown desktop style')
    updated = {**read_settings(SETTINGS), key: value, "version": 1}
    if key == "workspaceCount":
        updated["workspaceAlwaysShow"] = min(workspace_preferences(read_settings(SETTINGS))["workspaceAlwaysShow"], value)
    write_settings(SETTINGS, updated)
    generate_gaps()
    generate_layout()
    commands = [["hyprctl", "reload"],
                ["eitr-shell", "desktop-bar", "ipc", "call", "--", "style", "reload"]]
    if key == "corners":
        commands.insert(1, ["bash", str(code("walker/scripts/themes/walker.sh"))])
    for command in commands:
        try:
            subprocess.run(command, check=True, timeout=20,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as error:
            print(tr('Saved desktop style, but refresh failed: {error}', error=f'{error}'), file=sys.stderr)


def main():
    if len(sys.argv) >= 3 and sys.argv[2] in WORKSPACE_DEFAULTS:
        key = sys.argv[2]
        if len(sys.argv) == 4 and sys.argv[1] == "set":
            select(sys.argv[3], key)
        elif sys.argv[1:] != ["get", key]:
            raise ValueError("Usage: desktop-style.py get KEY | set KEY VALUE")
        print(workspace_preferences(read_settings(SETTINGS))[key])
        return
    if sys.argv[1:2] == ["scroll"]:
        scroll_action(sys.argv[2:])
        return
    if len(sys.argv) >= 3 and sys.argv[2] in LAYOUT_DEFAULTS:
        key = sys.argv[2]
        if len(sys.argv) == 4 and sys.argv[1] == "set":
            select(sys.argv[3], key)
        elif sys.argv[1] != "get" or len(sys.argv) != 3:
            raise ValueError("Usage: desktop-style.py get KEY | set KEY VALUE")
        print(current_layout()[key])
        return
    if sys.argv[1:] == ["generate"]:
        generate_gaps()
        generate_layout()
        return
    if len(sys.argv) >= 3 and sys.argv[2] == "gaps":
        if sys.argv[1:] == ["get", "gaps"]:
            print(current_gaps())
        elif len(sys.argv) == 4 and sys.argv[1] == "set":
            select(sys.argv[3], "gaps")
            print(current_gaps())
        else:
            raise ValueError("Usage: desktop-style.py get gaps | set gaps STYLE")
        return
    # "get corners" and "set corners STYLE" are the forms Walker's choice menus use.
    arguments = [argument for index, argument in enumerate(sys.argv[1:]) if not (index == 1 and argument == "corners")]
    if len(arguments) == 2 and arguments[0] == "set":
        select(arguments[1])
        print(current())
    elif arguments == ["summary"]:
        print(json.dumps({"current": current(), "gaps": current_gaps(), "gapChoices": WINDOW_GAPS, **current_layout(), **workspace_preferences(read_settings(SETTINGS)), "available": True,
                          "choices": [{"value": value, "label": details["label"], "available": True}
                                      for value, details in definitions()[1].items()]}))
    elif arguments == ["get"]:
        print(current())
    elif len(arguments) == 2 and arguments[0] == "get" and arguments[1] in ("scale", "windowRounding"):
        print(definitions()[1][current()][arguments[1]])
    else:
        raise ValueError('Usage: desktop-style.py get [scale|windowRounding] | set STYLE')


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
