#!/usr/bin/env python3
"""The current theme's colors and the desktop font for the calculator, as JSON."""
import importlib.util
import json
import os
from pathlib import Path
import tomllib

configured = os.environ.get("XDG_CONFIG_HOME", "")
config = Path(configured) if configured.startswith("/") else Path.home() / ".config"
try:
    palette = tomllib.loads((config / "theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
try:
    family = json.loads((config / "eitr/font.json").read_text()).get("family") or ""
except (OSError, ValueError, AttributeError):
    family = ""
# The shared corner preference (Square, Rounded, Extra Rounded) scales the radii like the bar's.
try:
    spec = importlib.util.spec_from_file_location(
        "desktop_style", Path(__file__).resolve().parents[1] / "desktop-bar/scripts/desktop-style.py")
    style = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(style)
    corner_scale = float(style.current_style()["scale"])
except (OSError, ValueError, KeyError, ImportError):
    corner_scale = 1.0
print(json.dumps({"cornerScale": corner_scale, "background": palette.get("background", "#0a0b12"), "foreground": palette.get("foreground", "#e4dcd2"),
                  "accent": palette.get("accent", "#2bb87a"), "font": family or "JetBrainsMono Nerd Font"}))
