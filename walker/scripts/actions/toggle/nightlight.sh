#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

result="$(python3 "$EITR_CODE_ROOT/walker/scripts/actions/toggle/nightlight.py" toggle)"
if [[ "$(jq -r '.enabled' <<< "$result")" == "true" ]]; then
  notify-send -u low "  Night Light enabled"
else
  notify-send -u low "  Night Light disabled"
fi
