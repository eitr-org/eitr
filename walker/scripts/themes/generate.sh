#!/usr/bin/env bash
# Writes every application style for ~/.config/theme/current and prints the
# names of failed modules. With EITR_NO_SESSION=1 (installation, before the
# first login) modules skip running-session effects: signals, service restarts
# and extension downloads.
set -uo pipefail

THEME_SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
failed_modules=()
for module in system walker btop cava kitty vscode swayosd; do
  if ! "$THEME_SCRIPTS_DIR/$module.sh"; then
    failed_modules+=("$module")
    printf 'Theme module failed: %s\n' "$module" >&2
  fi
done

if ! python3 "$THEME_SCRIPTS_DIR/../actions/ai-assistant.py" theme; then
  failed_modules+=(assistants)
fi

# Fonts belong to the desktop preference, not to the selected color theme.
if ! python3 "$THEME_SCRIPTS_DIR/../actions/style/fonts.py" sync; then
  failed_modules+=(fonts)
fi
if ! python3 "$THEME_SCRIPTS_DIR/../actions/style/cursor.py" sync >/dev/null; then
    failed_modules+=(cursor)
fi

if (( ${#failed_modules[@]} )); then
  printf '%s\n' "${failed_modules[*]}"
  exit 1
fi
