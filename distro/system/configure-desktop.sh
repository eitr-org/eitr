#!/usr/bin/env bash
# System side of the Eitr desktop for one user: networking, the SDDM login
# design and default session, the login shell and services. Run as root after
# `install.sh --seed-user` (or the full install.sh): the login designs come from
# the root-owned eitr-desktop package. Works in the installer's chroot too,
# since it only writes files and enables units.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
die() { printf '%s\n' "$*" >&2; exit 1; }

[[ ${EUID} -eq 0 ]] || die 'Run as root.'
[[ $# -eq 1 ]] || die "Usage: $0 USER"
user="$1"
IFS=: read -r _ _ uid _ _ home _ < <(getent passwd -- "$user") || die "Unknown user: $user"

install -Dm644 "$repo_root/distro/network/20-ethernet.network" /etc/systemd/network/20-ethernet.network
install -Dm644 "$repo_root/distro/network/20-wifi.network" /etc/systemd/network/20-wifi.network
if [[ ! -e /etc/resolv.conf && ! -L /etc/resolv.conf ]]; then
  ln -s /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
elif [[ ! -L /etc/resolv.conf ]]; then
  printf 'WARNING: /etc/resolv.conf is a regular file, so systemd-resolved DNS will not be used.\n' >&2
  printf 'Review it, then run: sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf\n' >&2
fi

SUDO_UID="$uid" /usr/bin/python3 -I /usr/share/eitr/quickshell/lockscreen/scripts/install-login.py
# SDDM preselects its last session, or the first one alphabetically. Seed the
# Hyprland session for a new system only; an existing choice is kept.
sddm_state=/var/lib/sddm/state.conf
if [[ ! -e "$sddm_state" ]]; then
  [[ -f /usr/share/wayland-sessions/hyprland-uwsm.desktop ]] || die 'The Hyprland UWSM session is missing.'
  install -d -m 755 -o sddm -g sddm /var/lib/sddm
  printf '[Last]\nSession=/usr/share/wayland-sessions/hyprland-uwsm.desktop\nUser=%s\n' "$user" > "$sddm_state"
  chown sddm:sddm "$sddm_state"
fi
usermod -s /usr/bin/zsh "$user"
systemctl enable iwd systemd-networkd systemd-resolved bluetooth sddm
# Incoming connections are refused except replies and the sharing apps (distro/system/firewall.nft).
systemctl enable eitr-firewall.service
# Restores the system when an update leaves it unable to start (distro/system/boot-guard.py).
systemctl enable eitr-boot-guard.service eitr-boot-guard-healthy.service
systemctl disable NetworkManager.service
# Laptop-only: hardware/detect.sh adds power-profiles-daemon when it finds a battery.
if pacman -Q power-profiles-daemon >/dev/null 2>&1; then
  systemctl enable power-profiles-daemon.service
fi
# Intel laptops only: hardware/detect.sh adds thermald (intel-laptop.txt).
if pacman -Q thermald >/dev/null 2>&1; then
  systemctl enable thermald.service
fi
