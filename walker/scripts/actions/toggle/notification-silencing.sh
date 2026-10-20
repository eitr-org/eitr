#!/usr/bin/env bash

STATE="$(eitr-shell desktop-bar ipc call -- notifications dnd)" || exit 1

if [[ "$STATE" == "true" ]]; then
  MESSAGE="󰂛  Notifications muted"
else
  MESSAGE="󰂚  Notifications enabled"
fi

if command -v swayosd-client >/dev/null 2>&1; then
  if command -v hyprctl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
    MONITOR="$(hyprctl monitors -j | jq -r '.[] | select(.focused == true).name')"

    swayosd-client \
      --monitor "$MONITOR" \
      --custom-message "$MESSAGE"
  else
    swayosd-client \
      --custom-message "$MESSAGE"
  fi
else
  notify-send "Notifications" "$MESSAGE"
fi
