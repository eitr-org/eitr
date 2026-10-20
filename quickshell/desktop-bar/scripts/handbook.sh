#!/usr/bin/env bash
set -euo pipefail
case "${1:-toggle}" in
  toggle|close) action="${1:-toggle}" ;;
  open) [[ "${2:-}" =~ ^[a-z0-9-]+$ ]] || exit 2; action=open ;;
  *) exit 2 ;;
esac
sleep 0.2
if [[ "$action" == open ]]; then
  exec eitr-shell desktop-bar ipc call -- handbook open "$2"
fi
exec eitr-shell desktop-bar ipc call -- handbook "$action"
