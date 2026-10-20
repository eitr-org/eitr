#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

wallpaper="${1:-}"

if [ -z "$wallpaper" ] || [ ! -f "$wallpaper" ]; then
  notify-send "Wallpaper" "Wallpaper file not found"
  exit 1
fi

exec python3 "$EITR_CODE_ROOT/walker/scripts/actions/wallpaper/transition.py" apply "$wallpaper"
