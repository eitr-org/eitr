#!/usr/bin/env bash
# Start independent session owners while preparing the wallpaper and bar.
set -uo pipefail

source "${BASH_SOURCE[0]%/*}/login-timing.sh"
mkdir -p "${EITR_LOGIN_TIMING_FILE%/*}"
: > "$EITR_LOGIN_TIMING_FILE"
login_mark session-start
# Elephant and its menu helpers need the compositor variables. Hyprland has them
# now; uwsm would publish them to systemd only after its own polling and settle.
systemctl --user import-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE
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
# The renderer probe and Hyprpaper run beside the bar: on a cold boot the EGL probe
# alone can take seconds. Only confirmed software rendering skips Hyprpaper (it
# crashes without a GPU, hyprwm/hyprtoolkit#144). This session's probe result is
# shared with the wallpaper component; a failed or timed-out probe writes none, so
# the component probes again later instead of treating unknown as software.
runtime_dir="${XDG_RUNTIME_DIR:-/run/user/$UID}"
wallpaper_settled="$runtime_dir/eitr-wallpaper-settled"
rm -f "$wallpaper_settled" "$runtime_dir/eitr-rendering.json"
(rendering=$(timeout -s KILL 4s eitr-run quickshell/desktop-bar/scripts/rendering.py 2>/dev/null) || rendering=""
 if grep -q '"detected": true' <<< "$rendering"; then
   printf '%s\n' "$rendering" > "$runtime_dir/eitr-rendering.json.tmp"
   mv -f "$runtime_dir/eitr-rendering.json.tmp" "$runtime_dir/eitr-rendering.json"
   login_mark renderer-detected
 fi
 if ! { grep -q '"software": true' <<< "$rendering" && grep -q '"detected": true' <<< "$rendering"; }; then
   eitr-hyprpaper &
   if timeout -s KILL 3s bash -c 'until hyprctl hyprpaper listactive >/dev/null 2>&1; do sleep 0.05; done'; then
     login_mark wallpaper-ready
   fi
 fi
 : > "$wallpaper_settled"
 wait) &
# Hyprpaper's still frame normally precedes the bar. The bar waits at most one
# second for it; after that the bar draws the same still image itself until
# Hyprpaper answers.
timeout -s KILL 1s bash -c 'until [[ -e "$1" ]]; do sleep 0.05; done' bash "$wallpaper_settled"
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
