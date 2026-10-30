#!/usr/bin/env python3
"""Whether theme switches recolour OpenRGB devices (fans, keyboard, RAM).

Off by default: lighting is a personal choice, so EITR changes it only after the
owner opts in under Settings > Devices & Input > Lighting. The preference is the
machine-local eitr/lighting.json.
"""
import argparse
from pathlib import Path
import subprocess
import sys

for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config, read_settings, write_settings
from eitr_i18n import tr


def settings_path():
    return config("eitr/lighting.json")


def follows_theme():
    try:
        return read_settings(settings_path()).get("follow_theme") is True
    except ValueError:
        return False


def main(arguments):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("enabled", help='exit 0 when theme switches recolour devices')
    get = commands.add_parser("get")
    get.add_argument("key", choices=["follow"])
    choose = commands.add_parser("set")
    choose.add_argument("key", choices=["follow"])
    choose.add_argument("value", choices=["on", "off"])
    args = parser.parse_args(arguments)
    if args.command == "enabled":
        return 0 if follows_theme() else 1
    if args.command == "get":
        print("on" if follows_theme() else "off")
        return 0
    write_settings(settings_path(), {"follow_theme": args.value == "on"})
    if args.value == "on":
        # Apply the current theme's colour now rather than at the next theme switch.
        subprocess.Popen(["bash", str(code("walker/scripts/themes/rgb.sh"))], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
