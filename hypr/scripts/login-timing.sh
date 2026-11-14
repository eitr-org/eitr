#!/usr/bin/env bash
# Linux /proc/uptime uses CLOCK_BOOTTIME, monotonic including suspended time.
EITR_LOGIN_TIMING_FILE="${XDG_STATE_HOME:-$HOME/.local/state}/eitr/login-timing.jsonl"
login_mark() {
  local uptime unused
  read -r uptime unused < /proc/uptime
  (flock -x 9; printf '{"event":"%s","monotonic":%s,"wall":%(%s)T}\n' "$1" "$uptime" -1 >&9) 9>>"$EITR_LOGIN_TIMING_FILE"
}
