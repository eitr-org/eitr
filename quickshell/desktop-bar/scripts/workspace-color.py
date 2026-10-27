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
from eitr_paths import code, config as user_config
import re
import tomllib

palette = {}
try:
    palette = tomllib.loads((user_config("theme/current/colors.toml")).read_text())
    accent = palette.get('accent', '#cdd6f4')
    if not isinstance(accent, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', accent):
        accent = '#cdd6f4'
except (OSError, ValueError):
    accent = '#cdd6f4'

channels = [int(accent[index:index + 2], 16) / 255 for index in (1, 3, 5)]
linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
          for value in channels]
luminance = sum(value * weight for value, weight in zip(linear, (0.2126, 0.7152, 0.0722)))
try:
    style = json.loads((user_config("quickshell/desktop-bar/workspace-style.json")).read_text()).get('style', 'Runes')
except (OSError, ValueError, AttributeError):
    style = 'Runes'
if style == 'Aurora':
    style = 'Dots'
if style not in ('Dots', 'Glyph', 'Numbers', 'Runes'):
    style = 'Runes'
critical = palette.get('alert', palette.get('color1', '#e05c68'))
if not isinstance(critical, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', critical):
    critical = '#e05c68'
print(json.dumps({'background': accent, 'foreground': '#000000' if luminance > 0.179 else '#ffffff',
                  'style': style, 'menuBackground': palette.get('surface', palette.get('background', '#181824')),
                  'menuForeground': palette.get('foreground', '#cdd6f4'), 'critical': critical, 'palette': palette}))
