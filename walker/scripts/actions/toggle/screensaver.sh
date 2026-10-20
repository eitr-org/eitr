#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

if pgrep -x hyprlock >/dev/null; then
  notify-send -u low "󱄄  Screensaver already running"
  exit 0
fi

if command -v uwsm >/dev/null 2>&1; then
  uwsm app -- bash "$EITR_CODE_ROOT/quickshell/lockscreen/scripts/launch.sh" lock >/dev/null 2>&1 &
else
  setsid bash "$EITR_CODE_ROOT/quickshell/lockscreen/scripts/launch.sh" lock >/dev/null 2>&1 &
fi
