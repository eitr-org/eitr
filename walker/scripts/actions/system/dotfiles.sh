#!/usr/bin/env bash
# Opens the configuration directory in VS Code, or in LazyVim when VS Code is absent.
set -euo pipefail

config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
if command -v code >/dev/null 2>&1; then
  exec "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/app-launch" code "$config_dir"
fi
exec "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/app-launch" --terminal --directory "$config_dir" nvim .
