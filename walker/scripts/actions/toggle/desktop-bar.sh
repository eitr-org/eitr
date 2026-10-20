#!/usr/bin/env bash

set -euo pipefail

if quickshell list --all 2>/dev/null | grep -q 'Config path: .*/quickshell/desktop-bar/shell.qml'; then
  eitr-shell desktop-bar ipc call -- bar visibility
else
  eitr-shell desktop-bar --daemonize
fi
