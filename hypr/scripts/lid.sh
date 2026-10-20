#!/usr/bin/env bash
# Laptop lid with an external monitor (experimental until confirmed on a laptop):
# closing turns the laptop screen off so the desktop moves to the monitor;
# opening reloads Hyprland's config, which brings the laptop screen back with
# its saved settings. Without an external monitor, logind suspends as usual.
set -euo pipefail
action="${1:-}"
monitors="$(hyprctl monitors -j)"
internal="$(python3 -c 'import json, sys; print(next((m["name"] for m in json.load(sys.stdin) if m["name"].startswith(("eDP", "LVDS", "DSI"))), ""))' <<<"$monitors")"
external="$(python3 -c 'import json, sys; print(sum(1 for m in json.load(sys.stdin) if not m["name"].startswith(("eDP", "LVDS", "DSI"))))' <<<"$monitors")"
case "$action" in
  close)
    [[ -n "$internal" && "$external" -gt 0 ]] || exit 0
    hyprctl eval "hl.monitor({ output = \"$internal\", disabled = true })" >/dev/null
    ;;
  open) hyprctl reload >/dev/null ;;
  *) echo "Usage: lid.sh close|open" >&2; exit 2 ;;
esac
