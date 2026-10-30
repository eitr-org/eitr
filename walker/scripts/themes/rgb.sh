#!/usr/bin/env bash
# Apply the theme's rgb.color to every OpenRGB device. Runs in the background
# during theme switches, so it only logs problems and never notifies. It does
# nothing unless the owner opted in (Settings > Devices & Input > Lighting).

set -euo pipefail

python3 "$(dirname -- "${BASH_SOURCE[0]}")/../actions/system/lighting.py" enabled || exit 0

CURRENT_DIR="${CURRENT_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/theme/current}"
RGB_FILE="$CURRENT_DIR/rgb.color"

[[ -f "$RGB_FILE" ]] || exit 0

if ! command -v openrgb >/dev/null 2>&1; then
  echo "rgb: openrgb is not installed; skipping" >&2
  exit 0
fi

RGB_COLOR="$(tr -d '#[:space:]' < "$RGB_FILE")"

if [[ ! "$RGB_COLOR" =~ ^[0-9A-Fa-f]{6}$ ]]; then
  echo "rgb: invalid color in $RGB_FILE: $RGB_COLOR" >&2
  exit 1
fi

# `openrgb --list-devices` prints one "N: Device Name" header per device.
mapfile -t devices < <(openrgb --list-devices 2>/dev/null | sed -nE 's/^([0-9]+): .*/\1/p')

if (( ${#devices[@]} == 0 )); then
  echo "rgb: no OpenRGB devices detected" >&2
  exit 0
fi

for device in "${devices[@]}"; do
  if ! openrgb --device "$device" --mode Static --color "$RGB_COLOR" >/dev/null 2>&1; then
    # Some controllers name their single-color mode "Direct" instead of "Static".
    openrgb --device "$device" --mode Direct --color "$RGB_COLOR" >/dev/null 2>&1 ||
      echo "rgb: device $device rejected Static and Direct modes" >&2
  fi
done
