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

if len(sys.argv) == 2 and sys.argv[1] == 'current':
    style = read_settings(STATE).get('style', 'Runes')
    if style == 'Aurora':
        style = 'Dots'
    print(style if style in STYLES else 'Runes')
    raise SystemExit(0)

if len(sys.argv) != 2 or sys.argv[1] not in STYLES:
    raise SystemExit('Unknown workspace style')
write_settings(STATE, {'style': sys.argv[1]})
