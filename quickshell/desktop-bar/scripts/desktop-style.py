#!/usr/bin/env python3
"""Shared corner and window-gap preferences for Eitr surfaces and Hyprland."""
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
from eitr_choice_lists import WINDOW_GAPS
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
    target = SETTINGS.with_name("window-gaps.lua")
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".window-gaps-", dir=target.parent)
    try:
        with os.fdopen(descriptor, "w") as output:
            output.write(f'return {{inner = {int(choice["inner"])}, outer = {int(choice["outer"])}}}\n')
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def select(value, key="corners"):
    options = definitions()[1] if key == "corners" else {choice["id"] for choice in WINDOW_GAPS}
    if key not in ("corners", "gaps") or value not in options:
        raise ValueError('Unknown desktop style')
    write_settings(SETTINGS, {**read_settings(SETTINGS), key: value, "version": 1})
    generate_gaps()
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
    if sys.argv[1:] == ["generate"]:
        generate_gaps()
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
        print(json.dumps({"current": current(), "gaps": current_gaps(), "gapChoices": WINDOW_GAPS, "available": True,
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
