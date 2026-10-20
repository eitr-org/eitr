#!/usr/bin/env bash
# Print the bar's WiFi glyph as {"text": ...}. The panel (wifi-popup.py) owns
# network details; this poll stays local and makes no network requests.

set -euo pipefail

icon=""

if rfkill -J 2>/dev/null | jq -e '.rfkilldevices[]? | select(.type == "wlan" and (.soft == "blocked" or .hard == "blocked"))' >/dev/null; then
  icon="󰤮"
else
  if systemctl is-active --quiet NetworkManager.service; then
    strength="$(timeout 2 nmcli -t -f ACTIVE,SIGNAL device wifi list --rescan no 2>/dev/null | awk -F: '$1 == "yes" { print $2; exit }' || true)"
    if [[ "$strength" =~ ^[0-9]+$ ]]; then
      if ((strength >= 75)); then icon="󰤨"
      elif ((strength >= 55)); then icon="󰤥"
      elif ((strength >= 35)); then icon="󰤢"
      elif ((strength >= 15)); then icon="󰤟"
      else icon="󰤯"; fi
    fi
    jq -cn --arg text "$icon" '{text: $text}'
    exit 0
  fi
  station="$(
    timeout 1 iwctl station list 2>/dev/null |
      sed -r 's/\x1B\[[0-9;]*[mK]//g' |
      awk '$2 == "connected" { print $1; exit }' || true
  )"

  if [[ -n "$station" ]]; then
    rssi="$(
      timeout 1 iwctl station "$station" show 2>/dev/null |
        sed -r 's/\x1B\[[0-9;]*[mK]//g' |
        awk '$1 == "RSSI" { print $2; exit }' || true
    )"

    icon="󰤨"
    if [[ "$rssi" =~ ^-?[0-9]+$ ]]; then
      if ((rssi >= -50)); then
        icon="󰤨"
      elif ((rssi >= -60)); then
        icon="󰤥"
      elif ((rssi >= -70)); then
        icon="󰤢"
      elif ((rssi >= -80)); then
        icon="󰤟"
      else
        icon="󰤯"
      fi
    fi
  fi
fi

jq -cn --arg text "$icon" '{text: $text}'
