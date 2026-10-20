#!/usr/bin/env bash

set -euo pipefail

CLASS="about-terminal"
ABOUT_COMMAND='eitr-run fastfetch/eitr.py; read -n 1 -s -r'

if command -v hyprctl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  if clients_json="$(hyprctl clients -j 2>/dev/null)"; then
    address="$(printf '%s\n' "$clients_json" | jq -r --arg class "$CLASS" '[.[] | select(.class == $class)][0].address // empty')"
    if [[ "$address" =~ ^0x[[:xdigit:]]+$ ]]; then
      hyprctl dispatch "hl.dsp.focus({ window = $address })" >/dev/null
      exit 0
    fi
  fi
fi

setsid -f kitty --class "$CLASS" --title "About Eitr" -o initial_window_width=1000 -o initial_window_height=600 -e bash -lc "$ABOUT_COMMAND" >/tmp/about-terminal.log 2>&1 < /dev/null
