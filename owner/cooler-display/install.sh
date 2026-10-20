#!/usr/bin/env bash
# Install the cooler display on the owner's machine: the udev rule (sudo), the
# script and a user service that starts with the desktop session. Rerun after
# changing the script.
set -euo pipefail

here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
sudo install -Dm644 "$here/70-cooler-display.rules" /etc/udev/rules.d/70-cooler-display.rules
sudo rm -f /etc/udev/rules.d/70-eitr-cooler-display.rules
sudo udevadm control --reload
sudo udevadm trigger --subsystem-match=hidraw
install -Dm755 "$here/cooler-display.py" "$HOME/.local/bin/cooler-display"
install -Dm644 "$here/cooler-display.service" "${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user/cooler-display.service"
systemctl --user daemon-reload
systemctl --user enable cooler-display.service
systemctl --user restart cooler-display.service
"$HOME/.local/bin/cooler-display" status
