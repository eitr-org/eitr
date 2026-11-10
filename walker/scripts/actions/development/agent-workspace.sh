#!/usr/bin/env bash
# Opens an agent workspace (herdr or cmux) in a terminal. herdr is installed per user in
# ~/.local/bin, which Walker's own PATH does not include.
EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

tool="${1:-}"
case "$tool" in
  herdr | cmux) ;;
  *) echo "Usage: agent-workspace.sh herdr|cmux" >&2; exit 2 ;;
esac

program="$(PATH="$HOME/.local/bin:$PATH" command -v "$tool" || true)"
if [[ -z "$program" ]]; then
  notify-send "Agent Workspaces" "$tool is not installed yet."
  exit 1
fi
exec "$EITR_CODE_ROOT/walker/bin/app-launch" --terminal -e "$program"
