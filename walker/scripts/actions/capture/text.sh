#!/usr/bin/env bash

set -euo pipefail

missing=()
for cmd in grim slurp hyprpicker wl-copy tesseract; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done

if ((${#missing[@]})); then
  notify-send -u critical "OCR capture unavailable" "Missing: ${missing[*]}"
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

text="$(
  grim -g "$selection" - |
    tesseract stdin stdout --oem 1 --psm 6 -l "${OCR_LANGS:-eng}" --dpi 300 -c preserve_interword_spaces=1 2>/dev/null
)"

if [[ -z "$text" ]]; then
  notify-send -u critical "No text found" "Select a clearer region and try again."
  exit 1
fi

printf "%s" "$text" | wl-copy
notify-send "Text copied" "OCR result copied to clipboard."
