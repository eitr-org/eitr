#!/usr/bin/env bash
# Announce pending updates; the Update button runs System Update.
set -euo pipefail
count="${1:?Missing update count}"
size="${2:-}"
[[ "$count" =~ ^[1-9][0-9]*$ ]] || exit 2
summary="$count update"
(( count == 1 )) || summary+="s"
summary+=" available"
body="Run System Update to install them."
[[ -n "$size" ]] && body="$size to download. $body"
root="${EITR_CODE_ROOT:-/usr/share/eitr}"
# Eitr's own logo: icon themes do not reliably carry system-software-update.
choice="$(notify-send --app-name=Updates --icon="$root/fastfetch/assets/eitr-logo.png" --wait \
  --action=default=Update --action=update=Update --action=later=Later "$summary" "$body" || true)"
if [[ "$choice" == update || "$choice" == default ]]; then
  # Floating, with the theme's solid background, like terminals that menus open.
  exec "$root/walker/bin/menu-path/kitty" -e python3 "$root/walker/scripts/actions/task-terminal.py" \
    bash "$root/walker/scripts/actions/system/update.sh" system
fi
