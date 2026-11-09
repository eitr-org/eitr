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

# The folder step is its own Walker menu; it runs this script again with the folder.
if [ -z "${EITR_CHOSEN_FOLDER:-}" ]; then
  exec python3 "$EITR_CODE_ROOT/walker/scripts/menus/choose-folder.py" start --icon "$app_icon" \
    --back menus:development -- "$0" "$@"
fi
folder="$EITR_CHOSEN_FOLDER"
unset EITR_CHOSEN_FOLDER

if [ "$tool" = "nvim" ]; then
  EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$folder" -e nvim . >/dev/null 2>&1 &
else
  "$EITR_CODE_ROOT/walker/bin/app-launch" "$command_name" "$folder" >/dev/null 2>&1 &
fi
