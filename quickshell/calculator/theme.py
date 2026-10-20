#!/usr/bin/env python3
"""The current theme's colors and the desktop font for the calculator, as JSON."""
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
print(json.dumps({"background": palette.get("background", "#0a0b12"), "foreground": palette.get("foreground", "#e4dcd2"),
                  "accent": palette.get("accent", "#2bb87a"), "font": family or "JetBrainsMono Nerd Font"}))
