#!/usr/bin/env bash

set -euo pipefail

missing=()
for cmd in grim slurp hyprpicker wl-copy zbarimg; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done

if ((${#missing[@]})); then
  notify-send -u critical "QR capture unavailable" "Missing: ${missing[*]}"
  exit 1
fi

cleanup_freeze() {
  [[ -n "${freeze_pid:-}" ]] && kill "$freeze_pid" 2>/dev/null || true
}
trap cleanup_freeze EXIT

hyprpicker -r -z >/dev/null 2>&1 &
freeze_pid=$!
sleep 0.1

selection="$(slurp 2>/dev/null || true)"
[[ -n "$selection" ]] || exit 0

result="$(grim -g "$selection" - | zbarimg -q --raw -Sdisable -Sqrcode.enable - 2>/dev/null || true)"

if [[ -z "$result" ]]; then
  notify-send -u critical "No QR code found" "Select a region containing a QR code."
  exit 1
fi

printf "%s" "$result" | wl-copy --sensitive
notify-send "QR copied" "Decoded value copied to clipboard."
