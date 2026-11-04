#!/usr/bin/env bash

set -euo pipefail

# Without an argument: show or hide the bar. With "autohide" (SUPER + Shift + Space):
# bring a hidden bar back, otherwise switch auto-hide on or off.
if quickshell list --all 2>/dev/null | grep -q 'Config path: .*/quickshell/desktop-bar/shell.qml'; then
  if [[ "${1:-}" == autohide ]]; then
    eitr-shell desktop-bar ipc call -- bar toggle autohide
  else
    eitr-shell desktop-bar ipc call -- bar visibility
  fi
else
  eitr-shell desktop-bar --daemonize
fi
