#!/usr/bin/env bash
# Opens the configuration directory in VS Code, or in LazyVim when VS Code is absent.
set -euo pipefail

config_dir="${XDG_CONFIG_HOME:-$HOME/.config}"
if command -v code >/dev/null 2>&1; then
  exec code "$config_dir"
fi
exec kitty --directory "$config_dir" nvim .
