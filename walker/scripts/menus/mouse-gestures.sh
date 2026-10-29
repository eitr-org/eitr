#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

options="Desktop: double left-click       Wallpaper carousel
Desktop: double right-click      Theme carousel
Bar: double left-click           Blur / Theme Color
Bar: double right-click          Full / Centered / Tabs / Islands
Bar: left-click and drag         Move to a screen edge
Workspace: right-click           Workspace style"

chosen=$(printf '%s\n' "$options" | "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --cache-file /dev/null --width 780 --prompt="Mouse Gestures")
case "$chosen" in
  "Desktop: double left-click"*)
    bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-picker.sh" wallpaper ;;
  "Desktop: double right-click"*)
    bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-picker.sh" theme ;;
  "Bar: double left-click"*)
    python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/bar-settings.py" toggle appearance ;;
  "Bar: double right-click"*)
    python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/bar-settings.py" toggle layout ;;
  "Bar: left-click and drag"*)
    "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:bar-position ;;
  "Workspace: right-click"*)
    "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:workspaces ;;
esac
