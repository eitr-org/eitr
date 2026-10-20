#!/usr/bin/env bash
# Pacman hook action: the boot splash is read from the initramfs, so a changed
# Eitr Plymouth theme only shows at boot once the images are rebuilt. The
# shutdown splash is rebuilt at every power-off and needs nothing.
set -euo pipefail

plymouth_config="${EITR_PLYMOUTH_CONFIG:-/etc/plymouth/plymouthd.conf}"
mkinitcpio_config="${EITR_MKINITCPIO_CONFIG:-/etc/mkinitcpio.conf}"

theme="$(sed -n 's/^[[:space:]]*Theme[[:space:]]*=[[:space:]]*//p' "$plymouth_config" 2>/dev/null | tail -n 1)"
if [[ "$theme" != eitr ]]; then
  echo 'The Eitr boot splash is not selected; the initramfs is left as it is.'
  exit 0
fi
hooks="$(sed -n 's/^[[:space:]]*HOOKS=(\(.*\))/\1/p' "$mkinitcpio_config" 2>/dev/null | tail -n 1)"
if [[ " $hooks " != *" plymouth "* && " $hooks " != *" sd-plymouth "* ]]; then
  echo 'Plymouth is not in the initramfs hooks; the initramfs is left as it is.'
  exit 0
fi
exec "${EITR_MKINITCPIO:-mkinitcpio}" -P
