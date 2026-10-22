#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
set -euo pipefail

root="$EITR_CODE_ROOT/quickshell/lockscreen"
mode="${1:-lock}"

lock_file() {
  printf '%s/desktop-lockscreen.lock\n' "${XDG_RUNTIME_DIR:?Missing runtime directory}"
}

# True while a lock started here (any design) or a standalone Hyprlock is held.
lock_active() {
  pgrep -x hyprlock >/dev/null && return 0
  local file
  file="$(lock_file)"
  [[ -e "$file" ]] || return 1
  ! flock -n "$file" true
}

case "$mode" in
  select)
    if ! python3 "$root/scripts/settings.py" select "${2:?Missing lockscreen}"; then
      notify-send -u critical "Selection failed" "The login screen could not be updated. Run the login installer again."
      exit 1
    fi
    if [[ -x /usr/lib/eitr/desktop-login-select || -x /usr/local/bin/desktop-login-select ]]; then
      notify-send -u low "Lockscreen and login selected" "Applies to your next lock and login."
    else
      notify-send -u low "Lockscreen selected" "${2} will be used the next time you lock."
    fi
    exit 0
    ;;
  active)
    lock_active
    exit
    ;;
  lock|preview) ;;
  *) exit 2 ;;
esac

if [[ "$mode" == lock ]]; then
  exec 9>"$(lock_file)"
  flock -n 9 || exit 0
  pgrep -x hyprlock >/dev/null && exit 0
  # Any failure while resolving the design must still leave the session locked.
  choice="${2:-$(python3 "$root/scripts/settings.py" current 2>/dev/null || echo hyprlock)}"
  [[ "$choice" != hyprlock ]] || exec eitr-hyprlock
  # Only shipped designs draw a lock (own lockscreens name one); no arbitrary QML paths.
  design="$(python3 "$root/scripts/settings.py" design "$choice")" || exec eitr-hyprlock
  [[ -f "$root/themes/$design/Main.qml" ]] || exec eitr-hyprlock
  config="$(python3 "$root/scripts/settings.py" config "$choice")" || exec eitr-hyprlock
else
  choice="${2:-$(python3 "$root/scripts/settings.py" current)}"
  if [[ "$choice" == hyprlock ]]; then
    notify-send -u low "Hyprlock preview" "Use the lock shortcut to view your existing Hyprlock."
    exit 0
  fi
  design="$(python3 "$root/scripts/settings.py" design "$choice")"
  config="$(python3 "$root/scripts/settings.py" config "$choice")"
fi

export DESKTOP_LOCK_CONFIG="$config"
export DESKTOP_LOCK_THEME="$root/themes/$design"
export QML_IMPORT_PATH="$root/imports:$EITR_CODE_ROOT/quickshell${QML_IMPORT_PATH:+:$QML_IMPORT_PATH}"
export QML2_IMPORT_PATH="$QML_IMPORT_PATH"
if [[ "$mode" == preview ]]; then
  exec quickshell -n -p "$root/preview.qml"
fi

# shell.qml quits with status 0 only after PAM succeeds. Any other exit (start
# failure, crash) leaves the session unprotected or showing Hyprland's crash
# screen, so hand over to Hyprlock unless another lockscreen instance holds it.
status=0
eitr-shell lockscreen || status=$?
if (( status != 0 )) && ! pgrep -f -- "quickshell.* -p .*/quickshell/lockscreen" >/dev/null; then
  exec eitr-hyprlock
fi
exit "$status"
