#!/usr/bin/env bash
set -euo pipefail
root="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ ${1:-} != --inside ]]; then
    exec "$root/walker/bin/menu-path/kitty" -o 'map=escape send_text all q' -e bash "$0" --inside
fi
if ! command -v cava >/dev/null 2>&1; then
    python3 "$root/walker/scripts/actions/task-terminal.py" \
        python3 "$root/walker/scripts/actions/install/software.py" install pacman cava
fi
bash "$root/walker/scripts/themes/cava.sh"
exec cava
