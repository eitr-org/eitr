#!/usr/bin/env bash
# Folder picker under DEV_DIR (default: the home folder), shared by the AI and
# project menus. Usage: choose-folder.sh TITLE ICON
# Prints the chosen folder and exits 0; exits 1 when dismissed and 2 when Back
# is chosen at the top, so the caller can reopen the menu it came from.

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

title="${1:?title}"
icon="${2:?icon}"
DEV_DIR="${DEV_DIR:-$HOME}"
DEV_DIR="${DEV_DIR%/}"
WALKER_DMENU="${WALKER_DMENU:-$EITR_CODE_ROOT/walker/bin/walker-dmenu}"
back_label="󰁍  Back"

if [ ! -d "$DEV_DIR" ]; then
  notify-send "$title" "$DEV_DIR does not exist"
  exit 1
fi

current="$DEV_DIR"

while true; do
  rel="${current#"$DEV_DIR"}"
  rel="${rel#/}"

  if [ -z "$rel" ]; then
    prompt="$title"
    if [ "$DEV_DIR" = "${HOME%/}" ]; then open_label="$icon  Open Home"; else open_label="$icon  Open ${DEV_DIR##*/}"; fi
  else
    prompt="$title: $rel"
    open_label="$icon  Open $rel"
  fi

  options=("$open_label" "$back_label")
  while IFS= read -r folder; do
    options+=("󰉋  $folder")
  done < <(
    find "$current" -mindepth 1 -maxdepth 1 -type d \
      ! -name ".*" \
      ! -name "node_modules" \
      ! -name ".idea" \
      ! -name ".gradle" \
      ! -name "target" \
      ! -name "build" \
      -printf "%f\n" |
      sort
  )

  chosen="$(printf "%s\n" "${options[@]}" | "$WALKER_DMENU" --dmenu --no-sort --matching=contains --cache-file /dev/null --prompt="$prompt")" || exit 1

  case "$chosen" in
    "")
      exit 1
      ;;
    "$open_label")
      printf "%s\n" "$current"
      exit 0
      ;;
    "$back_label")
      [ "$current" = "$DEV_DIR" ] && exit 2
      current="$(dirname "$current")"
      ;;
    󰉋\ *)
      next="${chosen#󰉋  }"
      if [ -d "$current/$next" ]; then
        current="$current/$next"
      fi
      ;;
  esac
done
