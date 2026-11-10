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
# The rest starts as soon as the bar answers on its IPC socket (it has loaded and
# draws its first frame), not after a fixed pause; at most 8 s if it never answers.
for ((attempt = 0; attempt < 80; attempt++)); do
  if eitr-shell desktop-bar ipc call -- bar workspaces >/dev/null 2>&1; then break; fi
  sleep 0.1
done
systemctl --user start --no-block eitr-crash-help.service
# The bar draws administrator password prompts; KDE's agent steps in if it cannot.
bash "${BASH_SOURCE[0]%/*}/polkit-fallback.sh" &
(eitr-session && eitr-walker --gapplication-service) &
python3 /usr/share/eitr/walker/scripts/actions/style/cursor.py sync &
hyprsunset &
/usr/share/eitr/walker/scripts/actions/toggle/nightlight-auto.sh &
swayosd-server --style ~/.config/swayosd/style.css &
rm -f ~/.cache/cliphist/db
wl-paste --type text --watch cliphist store &
wl-paste --type image --watch cliphist store &
wait
