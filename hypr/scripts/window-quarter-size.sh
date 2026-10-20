#!/usr/bin/env bash

set -euo pipefail

active="$(hyprctl activewindow -j)"

if [ -z "$active" ] || [ "$active" = "null" ]; then
  exit 0
fi

floating="$(jq -r '.floating // false' <<<"$active")"
fullscreen="$(jq -r '.fullscreen // 0' <<<"$active")"

if [ "$floating" = "true" ] || [ "$fullscreen" != "0" ]; then
  exit 0
fi

monitor_id="$(jq -r '.monitor' <<<"$active")"
window_x="$(jq -r '.at[0]' <<<"$active")"
window_y="$(jq -r '.at[1]' <<<"$active")"
window_width="$(jq -r '.size[0]' <<<"$active")"
window_height="$(jq -r '.size[1]' <<<"$active")"

monitor="$(hyprctl monitors -j | jq -r --argjson id "$monitor_id" '.[] | select(.id == $id)')"

if [ -z "$monitor" ]; then
  exit 0
fi

monitor_width="$(jq -r '.width' <<<"$monitor")"
monitor_height="$(jq -r '.height' <<<"$monitor")"
monitor_x="$(jq -r '.x' <<<"$monitor")"
monitor_y="$(jq -r '.y' <<<"$monitor")"

target_width=$((monitor_width / 3))
target_height=$((monitor_height / 3))

window_center_x=$((window_x + window_width / 2))
window_center_y=$((window_y + window_height / 2))
monitor_center_x=$((monitor_x + monitor_width / 2))
monitor_center_y=$((monitor_y + monitor_height / 2))

shrink_width_delta=$((target_width - window_width))
shrink_height_delta=$((target_height - window_height))

if [ "$window_center_x" -gt "$monitor_center_x" ]; then
  shrink_width_delta=$((window_width - target_width))
fi

if [ "$window_center_y" -gt "$monitor_center_y" ]; then
  shrink_height_delta=$((window_height - target_height))
fi

if [ "$window_width" -lt "$monitor_width" ] && [ "$window_height" -ge $((monitor_height * 70 / 100)) ]; then
  hyprctl eval "return hl.dispatch(hl.dsp.window.resize({ x = $shrink_width_delta, y = 0, relative = true }))"
elif [ "$window_height" -lt "$monitor_height" ] && [ "$window_width" -ge $((monitor_width * 70 / 100)) ]; then
  hyprctl eval "return hl.dispatch(hl.dsp.window.resize({ x = 0, y = $shrink_height_delta, relative = true }))"
elif [ "$window_width" -ge "$window_height" ]; then
  hyprctl eval "return hl.dispatch(hl.dsp.window.resize({ x = $shrink_width_delta, y = 0, relative = true }))"
else
  hyprctl eval "return hl.dispatch(hl.dsp.window.resize({ x = 0, y = $shrink_height_delta, relative = true }))"
fi
