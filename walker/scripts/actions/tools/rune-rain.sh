#!/usr/bin/env bash
set -euo pipefail
root="${EITR_CODE_ROOT:-/usr/share/eitr}"
exec "$root/walker/bin/menu-path/kitty" --start-as=fullscreen -o window_padding_width=0 \
    -e python3 "$root/lib/eitr_matrix.py"
