#!/usr/bin/env bash
# Offline dictation: hold SUPER + D and speak, release to type the words where
# the cursor is. Recording also ends after 120 seconds. Speech stays on this
# computer (whisper.cpp). The speech model downloads once on first use and is
# checked against its published checksum.
#
#   dictate.sh start|stop     (the key binding runs these on press and release)
set -euo pipefail
umask 077

data="${XDG_DATA_HOME:-$HOME/.local/share}"
[[ "$data" == /* ]] || data="$HOME/.local/share"
model="$data/eitr/whisper/ggml-base.bin"
model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
model_sha256="60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"
mode="${2:-dictation}"
[[ "$mode" == dictation || "$mode" == voice ]] || exit 2
runtime="${XDG_RUNTIME_DIR:-/tmp}"
audio="$runtime/eitr-$mode.wav"
pidfile="$runtime/eitr-$mode.pid"
# A quick tap sends press and release together, and the release can take the lock
# first. The press records when it happened (before waiting for the lock); a stop
# that finds nothing to stop shortly after a press leaves "tapped", and that start
# then records nothing. Plain typing of "d" (the release binding sees every D) has
# no recent press, so it never leaves the marker.
pressed="$runtime/eitr-$mode.pressed"
tapped="$runtime/eitr-$mode.tapped"
root="${EITR_CODE_ROOT:-/usr/share/eitr}"

notify() {
  notify-send --app-name=Dictation --icon="$root/fastfetch/assets/eitr-logo.png" \
    --hint=string:x-canonical-private-synchronous:eitr-dictation "$@" >/dev/null 2>&1 || true
}

# The bar shows a live waveform while the microphone listens and a pulse while
# the speech is transcribed (start, transcribe, stop).
bar_dot() {
  eitr-shell desktop-bar ipc call dictation "$1" >/dev/null 2>&1 || true
}

transcriber() {
  command -v whisper-cli 2>/dev/null || command -v whisper-cpp 2>/dev/null || true
}

ensure_ready() {
  if [[ -z "$(transcriber)" ]] || ! command -v wtype >/dev/null 2>&1; then
    notify "Dictation is not installed" "It comes with Eitr: run Main > System > Maintenance > Update > System Update."
    return 1
  fi
  [[ -f "$model" ]] && return 0
  notify "Preparing dictation" "Downloading the speech model once (148 MB)…"
  mkdir -p "${model%/*}"
  if ! curl -fsSL --retry 3 -o "$model.part" "$model_url" ||
      [[ "$(sha256sum "$model.part" | cut -d' ' -f1)" != "$model_sha256" ]]; then
    rm -f "$model.part"
    notify "Dictation unavailable" "The speech model could not be downloaded; check the connection and try again."
    return 1
  fi
  mv "$model.part" "$model"
  # The key was most likely released during the download.
  notify "Dictation is ready" "Hold SUPER + D and speak."
  return 1
}

start() {
  if [[ -f "$tapped" && "$(cat "$tapped")" == "$(cat "$pressed" 2>/dev/null)" ]]; then
    rm -f "$tapped"
    return 0
  fi
  rm -f "$tapped"
  ensure_ready || exit 0
  if [[ -f "$pidfile" ]] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
    return 0
  fi
  # The supervisor inherits the lock until the pid and indicator are published.
  # Neither the recorder nor later transcription may keep that lock open.
  (
    timeout --signal=INT --kill-after=2 120 \
      pw-record --rate 16000 --channels 1 --format s16 "$audio" 9>&- &
    recorder=$!
    echo "$recorder" > "$pidfile"
    bar_dot start
    flock -u 9
    exec 9>&-
    wait "$recorder" || true
    # An old supervisor must never stop a newer recording.
    bash "${BASH_SOURCE[0]}" finish "$mode" "$recorder"
  ) >/dev/null 2>&1 &
}

stop() {
  if [[ ! -f "$pidfile" ]]; then
    if [[ -z "${1:-}" && -f "$pressed" ]] && (( $(date +%s%N) - $(cat "$pressed") < 1500000000 )); then
      cp "$pressed" "$tapped"
    fi
    exit 0
  fi
  if [[ "${1:-}" != "" && "$(cat "$pidfile")" != "$1" ]]; then
    return 0
  fi
  # Install cleanup before IPC or recorder shutdown can fail.
  trap 'bar_dot stop; rm -f "$audio" "$pidfile" "$pressed"' EXIT
  bar_dot transcribe
  # Whatever happens next (nothing heard, an error, typing), the indicator ends.
  kill -TERM "$(cat "$pidfile")" 2>/dev/null || true
  rm -f "$pidfile"
  sleep 0.2
  [[ -s "$audio" ]] || exit 0
  if ! text="$("$(transcriber)" -m "$model" -f "$audio" -l auto -nt -np 2>/dev/null | tr '\n' ' ' | sed -E 's/^ +| +$//g; s/  +/ /g')"; then
    if [[ "$mode" == voice ]]; then
      python3 "$root/walker/scripts/actions/tools/voice-command.py" transcription-error
    else
      notify "Nothing heard" "Hold SUPER + D while you speak."
    fi
    return 1
  fi
  rm -f "$audio"
  if [[ -z "$text" || "$text" == "[BLANK_AUDIO]" ]]; then
    if [[ "$mode" == voice ]]; then
      notify "Nothing heard" "Hold SUPER + SHIFT + D while you speak."
    else
      notify "Nothing heard" "Hold SUPER + D while you speak."
    fi
    exit 0
  fi
  if [[ "$mode" == voice ]]; then
    printf '%s' "$text" | python3 "$root/walker/scripts/actions/tools/voice-command.py" stdin
  else
    wtype -- "$text"
  fi
}

[[ "${1:-}" == start ]] && date +%s%N > "$pressed"
# Keep the lock inode: unlinking it would let concurrent callers lock different files.
exec 9>"$runtime/eitr-$mode.lock"
flock 9

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  finish) stop "${3:?missing recorder pid}" ;;
  *) echo "Usage: dictate.sh start|stop" >&2; exit 2 ;;
esac
