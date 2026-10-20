#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
set -euo pipefail

sleep 0.2
category="theme"
if [[ -n "${1:-}" ]]; then
  if [[ -f "$EITR_CONFIG_ROOT/themes/$1/light.mode" || ( ! -d "$EITR_CONFIG_ROOT/themes/$1" && -f "$EITR_CODE_ROOT/themes/$1/light.mode" ) ]]; then
    category="theme-light"
  else
    category="theme-dark"
  fi
fi
exec bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-picker.sh" "$category"
