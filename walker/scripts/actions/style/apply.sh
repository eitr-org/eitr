#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

if [[ -z "${1:-}" ]]; then
  echo "Usage: apply.sh <theme-name>" >&2
  exit 1
fi

THEME_ROOT="$EITR_CONFIG_ROOT/theme"
CURRENT_DIR="$THEME_ROOT/current"
THEME_SCRIPTS_DIR="$EITR_CODE_ROOT/walker/scripts/themes"
WALLPAPER_HELPER="$EITR_CODE_ROOT/walker/scripts/actions/wallpaper/transition.py"
LOG_DIR="${XDG_RUNTIME_DIR:-$HOME/.cache}"

# Accept display labels such as "Rose Pine" as well as folder names.
THEME_NAME="$(
  printf '%s\n' "$1" |
    sed -E 's/<[^>]+>//g' |
    tr '[:upper:]' '[:lower:]' |
    tr ' ' '-'
)"

[[ "$THEME_NAME" != norse ]] || THEME_NAME=eitr

if [[ ! "$THEME_NAME" =~ ^[a-z0-9-]+$ ]]; then
  notify-send "Theme" "Invalid theme name: $1"
  exit 1
fi

if ! THEME_DIR="$(eitr_theme_dir "$THEME_NAME")"; then
  notify-send "Theme" "Theme '$THEME_NAME' does not exist"
  exit 1
fi

previous_wallpaper=""
if [[ "${EITR_NO_SESSION:-}" != 1 ]]; then
  previous_wallpaper="$(python3 "$WALLPAPER_HELPER" snapshot)"
fi

# Build the new current theme beside the old one, then swap it in so readers
# never observe a half-copied directory.
mkdir -p "$THEME_ROOT"
staging_dir="$(mktemp -d "$THEME_ROOT/.current.XXXXXX")"
trap 'rm -rf -- "$staging_dir" "$THEME_ROOT/.current.old"' EXIT
cp -a "$THEME_DIR"/. "$staging_dir/"
chmod 755 "$staging_dir"

rm -rf -- "$THEME_ROOT/.current.old"
if [[ -e "$CURRENT_DIR" ]]; then
  mv -- "$CURRENT_DIR" "$THEME_ROOT/.current.old"
fi
mv -- "$staging_dir" "$CURRENT_DIR"

mkdir -p "$HOME/.cache"
echo "$THEME_NAME" > "$HOME/.cache/current-theme"
python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-state.py" theme "$THEME_NAME"

# RGB in background; it logs instead of notifying.
if [[ "${EITR_NO_SESSION:-}" != 1 ]]; then
  nohup "$THEME_SCRIPTS_DIR/rgb.sh" >"$LOG_DIR/eitr-rgb.log" 2>&1 &
fi

failed_modules=()
if ! failed="$("$THEME_SCRIPTS_DIR/generate.sh")"; then
  read -r -a failed_modules <<< "$failed"
fi

if [[ "${EITR_NO_SESSION:-}" != 1 ]]; then
# hyprland.lua reads the active palette for borders and other colors.
hyprctl reload || true

# Kvantum and KDE color schemes are read when a Qt app starts, so a running
# Dolphin keeps the previous theme until it is restarted.
if pgrep -x dolphin >/dev/null; then
  kquitapp6 dolphin 2>/dev/null || pkill -x dolphin || true
fi

# Rebuild KDE service cache for Dolphin/KDE apps
if command -v kbuildsycoca6 >/dev/null 2>&1; then
  kbuildsycoca6 >/dev/null 2>&1 || true
fi

fi

mapfile -t wallpapers < <(python3 "$WALLPAPER_HELPER" list "$CURRENT_DIR/backgrounds")
FIRST_WALLPAPER="${wallpapers[0]:-}"

if [[ -n "$FIRST_WALLPAPER" ]]; then
  python3 "$WALLPAPER_HELPER" apply "$FIRST_WALLPAPER" --previous "$previous_wallpaper"
fi

if [[ "${EITR_NO_SESSION:-}" == 1 ]]; then
  (( ${#failed_modules[@]} == 0 ))
  exit
fi

if (( ${#failed_modules[@]} )); then
  notify-send "Theme applied with warnings" "$THEME_NAME: failed modules: ${failed_modules[*]}"
fi

# The user's theme-set hook (distro/lib/run-hook.sh) runs without delaying the switch.
hook_runner="$EITR_LIBRARY_ROOT/run-hook.sh"
[[ -f "$hook_runner" ]] || hook_runner="$EITR_CODE_ROOT/distro/lib/run-hook.sh"
[[ -f "$hook_runner" ]] && setsid bash "$hook_runner" theme-set "$THEME_NAME" >/dev/null 2>&1 < /dev/null &

EITR_THEME="$THEME_NAME" setsid python3 "$EITR_CODE_ROOT/walker/scripts/actions/install/plugins.py" hooks theme-changed >/dev/null 2>&1 < /dev/null &
