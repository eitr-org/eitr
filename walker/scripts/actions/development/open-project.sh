#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

tool="${1:-}"

if [ -z "$tool" ]; then
  exit 1
fi

case "$tool" in
  vscode)
    command_name="code"
    title="VS Code"
    app_icon=""
    ;;
  nvim)
    command_name="nvim"
    title="Neovim"
    app_icon=""
    ;;
  *)
    notify-send "Development" "Unknown editor: $tool"
    exit 1
    ;;
esac

if ! command -v "$command_name" >/dev/null 2>&1; then
  notify-send "$title" "$command_name is not installed. Install it from Walker > Install."
  exit 0
fi

status=0
folder="$("$EITR_CODE_ROOT/walker/scripts/menus/choose-folder.sh" "Open project" "$app_icon")" || status=$?
if [ "$status" -eq 2 ]; then
  exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:development
fi
[ "$status" -eq 0 ] || exit 0

if [ "$tool" = "nvim" ]; then
  EITR_TERMINAL_STYLE=window kitty --directory "$folder" -e nvim . >/dev/null 2>&1 &
else
  "$command_name" "$folder" >/dev/null 2>&1 &
fi
