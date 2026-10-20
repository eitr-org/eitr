#!/usr/bin/env python3
"""Shared corner preference for Eitr UI and compositor window decorations.
The styles and their sizes are defined once, in ../corner-styles.json."""
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
from eitr_paths import code, config as user_config, read_settings, write_settings
from eitr_i18n import tr
import subprocess
import tempfile

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


def select(value):
    if value not in definitions()[1]:
        raise ValueError('Unknown corner style')
    SETTINGS.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".style-", dir=SETTINGS.parent)
    try:
        with os.fdopen(fd, "w") as file:
            json.dump({**read_settings(SETTINGS), "corners": value, "version": 1}, file)
            file.write("\n")
        os.replace(name, SETTINGS)
    finally:
        if os.path.exists(name):
            os.unlink(name)
    generator = code("walker/scripts/themes/walker.sh")
    # The bar reads the preference only when told to, instead of polling for it.
    for command in (["hyprctl", "reload"], ["bash", str(generator)],
                    ["eitr-shell", "desktop-bar", "ipc", "call", "--", "style", "reload"]):
        try:
            subprocess.run(command, check=True, timeout=20,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (OSError, subprocess.SubprocessError) as error:
            print(tr('Saved corner style, but refresh failed: {error}', error=f'{error}'), file=sys.stderr)


def main():
    # "get corners" and "set corners STYLE" are the forms Walker's choice menus use.
    arguments = [argument for index, argument in enumerate(sys.argv[1:]) if not (index == 1 and argument == "corners")]
    if len(arguments) == 2 and arguments[0] == "set":
        select(arguments[1])
        print(current())
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
