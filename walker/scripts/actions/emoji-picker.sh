#!/usr/bin/env bash
set -euo pipefail
if quickshell list --all 2>/dev/null | grep -q 'Config path: .*/emoji-picker/shell.qml'; then
    eitr-shell emoji-picker kill
else
    eitr-shell emoji-picker --daemonize
fi
