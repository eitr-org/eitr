#!/usr/bin/env bash

set -euo pipefail

CURRENT_DIR="${CURRENT_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/theme/current}"
KITTY_THEME="${KITTY_THEME:-${XDG_CONFIG_HOME:-$HOME/.config}/kitty/theme.conf}"
THEME_SCRIPTS_DIR="$(dirname "${BASH_SOURCE[0]}")"

if [[ ! -f "$CURRENT_DIR/colors.toml" ]]; then
  exit 0
fi

mkdir -p "$(dirname "$KITTY_THEME")"

python3 - "$THEME_SCRIPTS_DIR" "$CURRENT_DIR" "$KITTY_THEME" <<'PY'
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from palette import load

colors = load(sys.argv[2])
missing = [key for key in ("background", "foreground") if key not in colors]
if missing:
    raise SystemExit(f"colors.toml is missing: {', '.join(missing)}")

bg = colors["background"]
fg = colors["foreground"]
# Fall back within the theme's own palette rather than to another theme.
palette = []
for index in range(16):
    fallback = palette[index - 8] if index >= 8 else (bg if index == 0 else fg)
    palette.append(colors.get(f"color{index}", fallback))

lines = [
    "# Auto-generated from ~/.config/theme/current/colors.toml",
    "",
    f"background {bg}",
    f"foreground {fg}",
    "",
    f"cursor {colors.get('cursor', fg)}",
    f"cursor_text_color {bg}",
    "",
    f"selection_background {colors.get('selection_background', palette[8])}",
    f"selection_foreground {colors.get('selection_foreground', fg)}",
    "",
]
lines += [f"color{index} {color}" for index, color in enumerate(palette)]
Path(sys.argv[3]).write_text("\n".join(lines) + "\n")
PY

[[ "${EITR_NO_SESSION:-}" != 1 ]] || exit 0

if command -v hyprctl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  clients_json="$(hyprctl clients -j 2>/dev/null || true)"

  if printf '%s\n' "$clients_json" | jq -e type >/dev/null 2>&1; then
    printf '%s\n' "$clients_json" |
      jq -r '.[] | select(.class == "kitty" or .initialClass == "kitty") | .pid' |
      sort -u |
      xargs -r kill -USR1 2>/dev/null || true
  fi
fi

pkill -USR1 -x kitty >/dev/null 2>&1 || true
