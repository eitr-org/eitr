#!/usr/bin/env python3
"""Store ordered dock desktop-entry IDs in machine-local preferences."""
import json
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    library = parent / "distro/lib"
    if not library.is_dir():
        library = parent / "lib"
    if (library / "eitr_paths.py").is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import config, read_settings, write_settings


def validate(pins):
    if not isinstance(pins, list) or any(not isinstance(pin, str) or not pin.strip()
                                         or '/' in pin or '\\' in pin for pin in pins):
        raise ValueError("Expected a list of desktop-entry IDs")
    result = []
    seen = set()
    for pin in pins:
        key = pin.removesuffix('.desktop').casefold()
        if key not in seen:
            result.append(pin)
            seen.add(key)
    return result


def main():
    path = config('quickshell/desktop-bar/dock-pins.json')
    try:
        if sys.argv[1:] == ['status']:
            pins = validate(read_settings(path).get('pins', []))
        elif len(sys.argv) == 3 and sys.argv[1] == 'set':
            pins = validate(json.loads(sys.argv[2]))
            write_settings(path, {'pins': pins})
        else:
            raise ValueError('Usage: dock-pins.py status|set JSON_LIST')
        print(json.dumps({'version': 1, 'pins': pins}))
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
