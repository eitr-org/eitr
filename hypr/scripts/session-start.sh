#!/usr/bin/env bash
# Start independent session owners while preparing the wallpaper and bar.
set -uo pipefail

source "${BASH_SOURCE[0]%/*}/login-timing.sh"
mkdir -p "${EITR_LOGIN_TIMING_FILE%/*}"
: > "$EITR_LOGIN_TIMING_FILE"
login_mark session-start
systemctl --user start --no-block elephant.service
bash "${BASH_SOURCE[0]%/*}/polkit-fallback.sh" &
rm -f ~/.cache/cliphist/db
wl-paste --type text --watch cliphist store &
wl-paste --type image --watch cliphist store &
# Walker reads generated GTK styles, so settings/theme preparation must finish first.
(if ! eitr-session; then login_mark session-tasks-failed; exit 1; fi
 login_mark session-tasks-done
 eitr-walker --gapplication-service &
 login_mark walker-service-started
 wait) &
# A failed or timed-out probe is unknown: only certain software rendering skips
# Hyprpaper. Bound both the probe and the complete readiness poll.
rendering=$(timeout -s KILL 2s eitr-run quickshell/desktop-bar/scripts/rendering.py 2>/dev/null) || rendering=""
# Reuse this session's probe in the wallpaper component; unknown keeps animation off.
rendering_cache="${XDG_RUNTIME_DIR:-/run/user/$UID}/eitr-rendering.json"
if [[ -z "$rendering" ]]; then rendering='{"software": true, "detected": false}'; fi
printf '%s\n' "$rendering" > "$rendering_cache.tmp"
mv -f "$rendering_cache.tmp" "$rendering_cache"
if ! { grep -q '"software": true' <<< "$rendering" && grep -q '"detected": true' <<< "$rendering"; }; then
  eitr-hyprpaper &
  if timeout -s KILL 1s bash -c 'until hyprctl hyprpaper listactive >/dev/null 2>&1; do sleep 0.05; done'; then
    login_mark wallpaper-ready
  fi
fi
eitr-shell desktop-bar --daemonize
login_mark bar-launched
# IPC readiness says nothing about presentation of the first frame. The complete
# poll, including slow IPC calls, has an eight-second deadline.
if timeout -s KILL 8s bash -c 'until eitr-shell desktop-bar ipc call -- bar workspaces >/dev/null 2>&1; do sleep 0.1; done'; then
  login_mark bar-ipc-ready
fi
systemctl --user start --no-block eitr-crash-help.service
python3 /usr/share/eitr/walker/scripts/actions/style/cursor.py sync &
hyprsunset &
/usr/share/eitr/walker/scripts/actions/toggle/nightlight-auto.sh &
swayosd-server --style ~/.config/swayosd/style.css &
wait
