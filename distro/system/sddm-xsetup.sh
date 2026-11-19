#!/bin/sh
# SDDM runs this as root before the login screen appears (X11 DisplayCommand).
# SDDM reads the keyboard layouts once, when the greeter starts, and found only the
# first layout of the system keyboard settings, so the login screen could not switch
# layouts. Apply every layout from those settings (written by localectl) to the
# login screen's X server first, then run SDDM's own setup script.
conf=${EITR_KEYBOARD_CONF:-/etc/X11/xorg.conf.d/00-keyboard.conf}
sddm_setup=${EITR_SDDM_XSETUP:-/usr/share/sddm/scripts/Xsetup}

value() {
  sed -n "s/^[[:space:]]*Option[[:space:]]*\"$1\"[[:space:]]*\"\([^\"]*\)\".*/\1/p" "$conf" | head -n 1
}

if [ -r "$conf" ] && command -v setxkbmap >/dev/null 2>&1; then
  layout=$(value XkbLayout)
  if [ -n "$layout" ]; then
    set -- -layout "$layout"
    variant=$(value XkbVariant)
    [ -n "$variant" ] && set -- "$@" -variant "$variant"
    model=$(value XkbModel)
    [ -n "$model" ] && set -- "$@" -model "$model"
    options=$(value XkbOptions)
    [ -n "$options" ] && set -- "$@" -option "" -option "$options"
    setxkbmap "$@" || true
  fi
fi

if [ -x "$sddm_setup" ]; then
  exec "$sddm_setup"
fi
exit 0
