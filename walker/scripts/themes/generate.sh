#!/usr/bin/env bash
# Writes every application style for ~/.config/theme/current and prints the
# names of failed modules. With EITR_NO_SESSION=1 (installation, before the
# first login) modules skip running-session effects: signals, service restarts
# and extension downloads.
set -uo pipefail

THEME_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# The modules write separate files, so they run at the same time; failures are
# still reported per module, in this order.
names=()
pids=()
start_module() {
  local name=$1
  shift
  "$@" &
  names+=("$name")
  pids+=("$!")
}
for module in system walker btop cava kitty vscode swayosd; do
  start_module "$module" "$THEME_SCRIPTS_DIR/$module.sh"
done
start_module hyprtoolkit python3 "$THEME_SCRIPTS_DIR/hyprtoolkit.py"
start_module assistants python3 "$THEME_SCRIPTS_DIR/../actions/ai-assistant.py" theme
# Fonts belong to the desktop preference, not to the selected color theme.
# Font sync also regenerates Ghostty configuration from the current palette.
start_module fonts python3 "$THEME_SCRIPTS_DIR/../actions/style/fonts.py" sync
cursor_sync() { python3 "$THEME_SCRIPTS_DIR/../actions/style/cursor.py" sync >/dev/null; }
start_module cursor cursor_sync
start_module window-gaps python3 "$THEME_SCRIPTS_DIR/../../../quickshell/desktop-bar/scripts/desktop-style.py" generate

failed_modules=()
for index in "${!pids[@]}"; do
  if ! wait "${pids[index]}"; then
    failed_modules+=("${names[index]}")
    printf 'Theme module failed: %s\n' "${names[index]}" >&2
  fi
done

if (( ${#failed_modules[@]} )); then
  printf '%s\n' "${failed_modules[*]}"
  exit 1
fi
