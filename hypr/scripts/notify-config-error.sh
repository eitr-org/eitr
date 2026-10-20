#!/usr/bin/env bash
# Show a Hyprland config error once the session's notification server is up.
# hyprland.lua runs this in the background. It waits for an already-owned
# notification name instead of using D-Bus activation, so a login-time error
# appears after Quickshell starts without launching another daemon.
set -u

message=${1:?Usage: notify-config-error.sh MESSAGE}

for _ in $(seq 30); do
  if busctl --user --acquired --no-legend list 2>/dev/null \
    | grep -q '^org\.freedesktop\.Notifications[[:space:]]'; then
    exec notify-send -u critical -a Hyprland "Machine config not applied" "$message"
  fi
  sleep 1
done
echo "notify-config-error: no notification server; $message" >&2
exit 1
