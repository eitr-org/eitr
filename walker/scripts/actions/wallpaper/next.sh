#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

WALLPAPER_DIR="$EITR_CODE_ROOT/walker/scripts/actions/wallpaper"
BACKGROUND_DIR="$HOME/.config/theme/current/backgrounds"
CACHE_PATH="$HOME/.cache/current-wallpaper"

mapfile -t WALLPAPERS < <(python3 "$WALLPAPER_DIR/transition.py" list "$BACKGROUND_DIR")
# The user's own wallpapers follow the theme's.
mapfile -t -O "${#WALLPAPERS[@]}" WALLPAPERS < <(python3 "$WALLPAPER_DIR/transition.py" list "$EITR_DATA_ROOT/eitr/wallpapers")

TOTAL="${#WALLPAPERS[@]}"

if (( TOTAL == 0 )); then
  notify-send "Wallpaper" "No wallpapers found in the current theme"
  exit 1
fi

CURRENT_WALLPAPER=""

if [[ -f "$CACHE_PATH" ]]; then
  CURRENT_WALLPAPER="$(cat "$CACHE_PATH")"
fi

CURRENT_INDEX=-1

for i in "${!WALLPAPERS[@]}"; do
  if [[ "${WALLPAPERS[$i]}" == "$CURRENT_WALLPAPER" ]]; then
    CURRENT_INDEX="$i"
    break
  fi
done

NEXT_INDEX=$(( (CURRENT_INDEX + 1) % TOTAL ))

exec bash "$EITR_CODE_ROOT/walker/scripts/actions/wallpaper/apply.sh" "${WALLPAPERS[$NEXT_INDEX]}"
