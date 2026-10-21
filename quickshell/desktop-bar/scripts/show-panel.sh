#!/usr/bin/env bash
set -euo pipefail
# Keep in sync with the `panels` IpcHandler show() kinds in shell.qml;
# tests/test_show_panel_kinds.py enforces this.
case "${1:-}" in
  wifi|bluetooth|brightness|display|volume|mic|tailscale|streaming|keyboard|idle|calendar|weather|hardware|ai|obs|workspace|recording|notifications|overview|center|media|battery) ;;
  *) exit 2 ;;
esac
sleep 0.2
exec eitr-shell desktop-bar ipc call -- panels show "$1"
