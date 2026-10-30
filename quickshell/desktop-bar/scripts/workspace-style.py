#!/usr/bin/env python3
import json
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

STYLES = ('Dots', 'Glyph', 'Numbers', 'Runes')
STATE = user_config("quickshell/desktop-bar/workspace-style.json")

def current():
    style = read_settings(STATE).get('style', 'Runes')
    if style == 'Aurora':
        style = 'Dots'
    return style if style in STYLES else 'Runes'


if sys.argv[1:] == ['summary']:
    print(json.dumps({"current": current(), "available": True,
                      "choices": [{"value": value, "label": value, "available": True} for value in STYLES]}))
    raise SystemExit(0)

if sys.argv[1:] == ['current']:
    print(current())
    raise SystemExit(0)

if len(sys.argv) != 2 or sys.argv[1] not in STYLES:
    raise SystemExit('Unknown workspace style')
write_settings(STATE, {'style': sys.argv[1]})
