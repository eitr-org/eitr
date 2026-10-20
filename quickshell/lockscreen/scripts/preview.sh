#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
set -euo pipefail
sleep 0.2
bash "$EITR_CODE_ROOT/quickshell/lockscreen/scripts/launch.sh" preview "${1:?Missing lockscreen}"
exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:lockscreen
