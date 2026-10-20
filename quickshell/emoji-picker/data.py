#!/usr/bin/env python3
import json
from pathlib import Path
import tomllib

home = Path.home()
emojis = json.loads(Path(__file__).with_name("emojis.json").read_text())
try:
    palette = tomllib.loads((home / ".config/theme/current/colors.toml").read_text())
except (OSError, ValueError):
    palette = {}
print(json.dumps({"emojis": emojis, "background": palette.get("background", "#181824"),
                  "foreground": palette.get("foreground", "#cdd6f4"),
                  "accent": palette.get("accent", "#cdd6f4")}))
