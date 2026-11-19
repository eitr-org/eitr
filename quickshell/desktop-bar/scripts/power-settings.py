#!/usr/bin/env python3
"""Battery warning level settings helper for Settings and bar controls."""
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

from eitr_power import settings, set_levels, DEFAULTS


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    action = args[0] if args else "summary"
    if action == "summary":
        print(json.dumps(settings()))
        return 0
    if action == "set" and len(args) == 3:
        try:
            low = int(args[1])
            critical = int(args[2])
            print(json.dumps(set_levels(low, critical)))
            return 0
        except (ValueError, TypeError) as error:
            if os.environ.get("EITR_BAR_ACTION") == "1":
                print(json.dumps({"error": True, "code": "action-failed", "message": str(error)}))
            else:
                print(str(error), file=sys.stderr)
            return 1
    if action == "set-low" and len(args) == 2:
        try:
            low = int(args[1])
            print(json.dumps(set_levels(low=low)))
            return 0
        except (ValueError, TypeError) as error:
            if os.environ.get("EITR_BAR_ACTION") == "1":
                print(json.dumps({"error": True, "code": "action-failed", "message": str(error)}))
            else:
                print(str(error), file=sys.stderr)
            return 1
    if action == "set-critical" and len(args) == 2:
        try:
            critical = int(args[1])
            print(json.dumps(set_levels(critical=critical)))
            return 0
        except (ValueError, TypeError) as error:
            if os.environ.get("EITR_BAR_ACTION") == "1":
                print(json.dumps({"error": True, "code": "action-failed", "message": str(error)}))
            else:
                print(str(error), file=sys.stderr)
            return 1
    if action == "reset":
        print(json.dumps(set_levels(DEFAULTS["low"], DEFAULTS["critical"])))
        return 0
    print("Usage: power-settings.py [summary | set <low> <critical> | set-low <low> | set-critical <critical> | reset]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
