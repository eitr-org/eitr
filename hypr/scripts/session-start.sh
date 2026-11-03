#!/usr/bin/env bash
# Give visible surfaces the first turn at login; optional work follows them.
set -uo pipefail

# Without a GPU, hyprpaper crashes at start (hyprwm/hyprtoolkit#144); the bar then
# draws the still wallpaper itself, so do not start it there.
if eitr-run quickshell/desktop-bar/scripts/rendering.py 2>/dev/null | grep -q '"software": false'; then
  eitr-hyprpaper &
  # Hyprpaper's configured still frame precedes construction of the bar.
  for ((attempt = 0; attempt < 5; attempt++)); do
    if hyprctl hyprpaper listactive >/dev/null 2>&1; then break; fi
    sleep 0.1
  done
fi
eitr-shell desktop-bar --daemonize
# Walker cannot open before its Elephant backend is ready (about 3 s of menu loading),
# so it starts with the bar; the rest is optional and waits.
systemctl --user start --no-block elephant.service
sleep 4
systemctl --user start --no-block eitr-crash-help.service
(eitr-session && eitr-walker --gapplication-service) &
python3 /usr/share/eitr/walker/scripts/actions/style/cursor.py sync &
hyprsunset &
/usr/share/eitr/walker/scripts/actions/toggle/nightlight-auto.sh &
swayosd-server --style ~/.config/swayosd/style.css &
rm -f ~/.cache/cliphist/db
wl-paste --type text --watch cliphist store &
wl-paste --type image --watch cliphist store &
wait
