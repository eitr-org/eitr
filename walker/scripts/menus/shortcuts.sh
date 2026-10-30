#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

MENUS_DIR="$EITR_CODE_ROOT/walker/scripts/menus"
ACTIONS_DIR="$EITR_CODE_ROOT/walker/scripts/actions"

if [[ "$(python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/focus-mode.py" status)" == on ]]; then
  exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:shortcuts
fi

options="$(python3 "$MENUS_DIR/shortcut-reference.py" options)"

chosen="$(
  echo -e "$options" |
    "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --cache-file /dev/null --width 820 --height 720 --prompt="Shortcuts"
)"

# Normalize Walker's output so actions also match when indentation is trimmed.
chosen="${chosen#"${chosen%%[![:space:]]*}"}"
[[ -n "$chosen" ]] || exit 0
chosen="  $chosen"
# Let the launcher release keyboard focus before acting on the previous window.
sleep 0.15

command="$(python3 "$MENUS_DIR/shortcut-reference.py" command "$chosen")"
[[ -n "$command" ]] || exit 0
export MENUS_DIR ACTIONS_DIR EITR_CODE_ROOT
bash -c "$command"
