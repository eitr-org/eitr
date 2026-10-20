#!/usr/bin/env bash
set -euo pipefail
emoji="${1:-}"
[[ -n "$emoji" ]] || exit 0
# Wait for the overlay to release focus before typing into the original app.
sleep 0.2
wtype -- "$emoji"
