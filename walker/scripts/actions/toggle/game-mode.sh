#!/usr/bin/env bash
# Game mode: window animations, blur and shadows off, notification popups held
# (do not disturb) and the performance power profile while it is on. Turning it
# off restores only what turning it on changed: Hyprland reloads its own config,
# and do not disturb and the power profile return to what they were.
#
#   game-mode.sh [toggle|on|off|status]
set -euo pipefail

state="${XDG_RUNTIME_DIR:-/tmp}/eitr-game-mode.json"
root="${EITR_CODE_ROOT:-/usr/share/eitr}"

notify() {
  notify-send --app-name=Eitr --icon="$root/fastfetch/assets/eitr-logo.png" "$1" "$2" >/dev/null 2>&1 || true
}

dnd_on() {
  eitr-shell desktop-bar ipc call -- notifications status 2>/dev/null |
    python3 -c 'import json, sys; print(json.load(sys.stdin).get("doNotDisturb", False))' 2>/dev/null || echo False
}

turn_on() {
  local changed_dnd=false previous_profile=''
  hyprctl eval 'hl.config({ animations = { enabled = false }, decoration = { blur = { enabled = false }, shadow = { enabled = false } } })' >/dev/null
  if [[ "$(dnd_on)" == False ]]; then
    eitr-shell desktop-bar ipc call -- notifications dnd >/dev/null 2>&1 && changed_dnd=true
  fi
  if command -v powerprofilesctl >/dev/null 2>&1; then
    previous_profile="$(powerprofilesctl get 2>/dev/null || true)"
    if [[ -n "$previous_profile" && "$previous_profile" != performance ]]; then
      powerprofilesctl set performance 2>/dev/null || previous_profile=''
    else
      previous_profile=''
    fi
  fi
  printf '{"dnd": %s, "profile": "%s"}\n' "$changed_dnd" "$previous_profile" > "$state"
  notify "Game mode on" "Animations, blur and notification popups are off until you turn it off."
}

turn_off() {
  local changed_dnd previous_profile
  changed_dnd="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("dnd", False))' "$state" 2>/dev/null || echo False)"
  previous_profile="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1])).get("profile", ""))' "$state" 2>/dev/null || true)"
  rm -f "$state"
  hyprctl reload >/dev/null
  if [[ "$changed_dnd" == True && "$(dnd_on)" == True ]]; then
    eitr-shell desktop-bar ipc call -- notifications dnd >/dev/null 2>&1 || true
  fi
  if [[ -n "$previous_profile" ]] && command -v powerprofilesctl >/dev/null 2>&1; then
    powerprofilesctl set "$previous_profile" 2>/dev/null || true
  fi
  notify "Game mode off" "Your usual effects and notifications are back."
}

case "${1:-toggle}" in
  on) [[ -f "$state" ]] || turn_on ;;
  off) [[ ! -f "$state" ]] || turn_off ;;
  toggle) if [[ -f "$state" ]]; then turn_off; else turn_on; fi ;;
  status) if [[ -f "$state" ]]; then echo on; else echo off; fi ;;
  *) echo "Usage: game-mode.sh [toggle|on|off|status]" >&2; exit 2 ;;
esac
