#!/usr/bin/env bash
set -euo pipefail
# Keep in sync with the `panels` IpcHandler show() kinds in shell.qml;
# tests/test_show_panel_kinds.py enforces this.
case "${1:-}" in
  picture|wifi|bluetooth|brightness|display|volume|mic|streaming|keyboard|calendar|weather|hardware|ai|obs|workspace|recording|notifications|overview|center|media|battery|catalog|dashboard) ;;
  *) exit 2 ;;
esac
sleep 0.2
exec eitr-shell desktop-bar ipc call -- panels show "$1"
