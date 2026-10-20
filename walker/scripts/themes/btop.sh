#!/usr/bin/env bash

set -euo pipefail

CURRENT_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/theme/current"
BTOP_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/btop"
BTOP_THEMES_DIR="$BTOP_DIR/themes"
BTOP_CONFIG="$BTOP_DIR/btop.conf"
BTOP_THEME="$BTOP_THEMES_DIR/current.theme"

mkdir -p "$BTOP_THEMES_DIR"

if [[ ! -f "$CURRENT_DIR/btop.theme" ]]; then
  exit 0
fi

cp "$CURRENT_DIR/btop.theme" "$BTOP_THEME"

if [[ ! -f "$BTOP_CONFIG" ]]; then
  btop --default-config > "$BTOP_CONFIG"
fi

python3 - "$BTOP_CONFIG" <<'PY'
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
config = path.read_text()

replacements = {
    "color_theme": '"current"',
    "theme_background": "true",
    "truecolor": "true",
}

for key, value in replacements.items():
    pattern = re.compile(rf'^(#?\s*{re.escape(key)}\s*=\s*).*$' , re.MULTILINE)
    line = f"{key} = {value}"

    if pattern.search(config):
      config = pattern.sub(line, config, count=1)
    else:
      config += f"\n{line}\n"

path.write_text(config)
PY
