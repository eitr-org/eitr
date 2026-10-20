#!/usr/bin/env bash
# After the boot guard restored the system (distro/system/boot-guard.py), say so
# once at the next login.
set -euo pipefail
helper="${EITR_BOOT_GUARD:-/usr/lib/eitr/eitr-boot-guard}"
[[ -x "$helper" ]] || exit 0
restored="$("$helper" notice | python3 -c 'import json, sys; print(json.load(sys.stdin).get("restored", ""))')"
[[ -n "$restored" ]] || exit 0
seen="${XDG_STATE_HOME:-$HOME/.local/state}/eitr/boot-guard-seen"
[[ "$(cat "$seen" 2>/dev/null || true)" != "$restored" ]] || exit 0
mkdir -p "${seen%/*}"
printf '%s\n' "$restored" > "$seen"
root="${EITR_CODE_ROOT:-/usr/share/eitr}"
notify-send --app-name=Eitr --icon="$root/fastfetch/assets/eitr-logo.png" --urgency=critical \
  "Eitr undid the last update" \
  "The computer failed to start twice after it, so Eitr restored the system from just before the update. Your files were not touched. Check Arch news before updating again."
