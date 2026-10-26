#!/usr/bin/env bash
# Open Eitr's calculator, or close it when it is already open.
set -euo pipefail
if quickshell list --all 2>/dev/null | grep -q 'Config path: .*/calculator/shell.qml'; then
  eitr-shell calculator kill
else
  "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/app-launch" eitr-shell calculator --daemonize
fi
