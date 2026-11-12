#!/usr/bin/env python3
import importlib.util
import json
from pathlib import Path
import tomllib

home = Path.home()
emojis = json.loads(Path(__file__).with_name("emojis.json").read_text())
try:
    palette = tomllib.loads((home / ".config/theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
# The shared corner preference (Square, Rounded, Extra Rounded) scales the radii like the bar's.
try:
    spec = importlib.util.spec_from_file_location(
        "desktop_style", Path(__file__).resolve().parents[1] / "desktop-bar/scripts/desktop-style.py")
    style = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(style)
    corner_scale = float(style.current_style()["scale"])
except (OSError, ValueError, KeyError, ImportError):
    corner_scale = 1.0
print(json.dumps({"emojis": emojis, "cornerScale": corner_scale, "background": palette.get("background", "#181824"),
                  "foreground": palette.get("foreground", "#cdd6f4"),
                  "accent": palette.get("accent", "#cdd6f4")}))
