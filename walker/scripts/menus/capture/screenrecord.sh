#!/usr/bin/env bash
# Capture > Screen Recording: the bar's OBS controls from Walker. Each mode saves the
# same recording options as the OBS panel (desktop sound, webcam), then prepares OBS
# and starts recording through obs-control.py, which reads the WebSocket password
# from OBS's own settings. No scene names are assumed; OBS's current scene is used.

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

CONTROL="$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/obs-control.py"

obs_control() {
  local message
  if ! message="$(python3 "$CONTROL" "$@" 2>&1)"; then
    notify-send "OBS" "${message:-OBS could not do that}" -u critical
    exit 1
  fi
}

# record AUDIO WEBCAM: "true" or "false" for desktop sound and the webcam.
record() {
  obs_control set-option audio "$1"
  # The microphone follows desktop sound here; the OBS panel can set it separately.
  obs_control set-option mic "$1"
  obs_control set-option webcam "$2"
  obs_control prepare
  obs_control record
}

case "${1:-}" in
  open) obs_control open ;;
  record) record false false ;;
  audio) record true false ;;
  webcam) record false true ;;
  audio-webcam) record true true ;;
  stop) obs_control stop ;;
  *) echo "Usage: screenrecord.sh open|record|audio|webcam|audio-webcam|stop" >&2; exit 2 ;;
esac
