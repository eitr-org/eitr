#!/usr/bin/env python3
"""Select the screen that hosts the desktop bar."""

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
from eitr_paths import code, config as user_config
from eitr_i18n import tr
import subprocess
import tempfile


CONFIG_DIR = user_config("hypr")
PREFERENCE = CONFIG_DIR / "primary-display"
PREFERRED_OUTPUTS = CONFIG_DIR / "preferred-outputs"


def active_monitors():
    result = subprocess.run(
        ["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def saved_primary():
    try:
        return PREFERENCE.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return ""


def preferred_outputs():
    """Read the machine-local output order: one name per line, # comments."""
    try:
        text = PREFERRED_OUTPUTS.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    names = []
    for line in text.splitlines():
        name = line.split("#", 1)[0].strip()
        if name and name not in names:
            names.append(name)
    return names


# shell.qml's targetScreens() mirrors this order for the moment before the
# first status query returns; keep both in sync (tests/test_display_primary.py).
def choose_primary(monitors, saved="", preferred=()):
    """Saved choice, then the first connected preferred output, then the largest."""
    connected = {monitor["name"] for monitor in monitors}
    if saved in connected:
        return saved
    if not connected:
        return ""
    for name in preferred:
        if name in connected:
            return name
    # Largest area; ties keep compositor order, as QML can match it.
    return max(monitors, key=lambda monitor: monitor["width"] * monitor["height"])["name"]


def status():
    monitors = active_monitors()
    preferred = preferred_outputs()
    primary = choose_primary(monitors, saved_primary(), preferred)
    return {"monitors": monitors, "primary": primary, "preferred": preferred}


def set_primary(name):
    if name not in {monitor["name"] for monitor in active_monitors()}:
        raise ValueError(tr('Display is not connected'))
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".primary-display-", dir=CONFIG_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(name + "\n")
        os.replace(temp_name, PREFERENCE)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
    return status()


def main():
    try:
        if sys.argv[1:] == ["status"]:
            result = status()
        elif len(sys.argv) == 3 and sys.argv[1] == "set":
            result = set_primary(sys.argv[2])
        else:
            raise ValueError('Usage: display-primary.py status|set DISPLAY')
        print(json.dumps(result))
    except (OSError, subprocess.CalledProcessError, ValueError, KeyError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
