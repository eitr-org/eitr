#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
set -euo pipefail

# A manual lock blanks and suspends sooner than hypridle's idle listeners
# (15/30/60 minutes from last input); hypridle still covers unattended idling.
DISPLAY_OFF_AFTER=900
SUSPEND_AFTER=1800
launcher="$EITR_CODE_ROOT/quickshell/lockscreen/scripts/launch.sh"

# Covers Quickshell designs and Hyprlock, whether started here or by hypridle.
if bash "$launcher" active; then
  notify-send -u low "󱄄  Screensaver already running"
  exit 0
fi

bash "$launcher" lock &
lock_pid=$!

(
  sleep "$DISPLAY_OFF_AFTER"
  if kill -0 "$lock_pid" 2>/dev/null; then
    hyprctl dispatch dpms off
  fi
) &
display_timer_pid=$!

(
  sleep "$SUSPEND_AFTER"
  if kill -0 "$lock_pid" 2>/dev/null; then
    systemctl suspend
  fi
) &
suspend_timer_pid=$!

cleanup() {
  kill "$display_timer_pid" "$suspend_timer_pid" 2>/dev/null || true
  hyprctl dispatch dpms on >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM
wait "$lock_pid"
