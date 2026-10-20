#!/usr/bin/env bash
# Offline dictation: hold SUPER + D and speak, release to type the words where
# the cursor is. Speech stays on this computer (whisper.cpp). The speech model
# downloads once on first use and is checked against its published checksum.
#
#   dictate.sh start|stop     (the key binding runs these on press and release)
set -euo pipefail

data="${XDG_DATA_HOME:-$HOME/.local/share}"
[[ "$data" == /* ]] || data="$HOME/.local/share"
model="$data/eitr/whisper/ggml-base.bin"
model_url="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin"
model_sha256="60ed5bc3dd14eea856493d334349b405782ddcaf0028d4b5df4088345fba2efe"
runtime="${XDG_RUNTIME_DIR:-/tmp}"
audio="$runtime/eitr-dictation.wav"
pidfile="$runtime/eitr-dictation.pid"
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
  ensure_ready || exit 0
  [[ -f "$pidfile" ]] && kill "$(cat "$pidfile")" 2>/dev/null || true
  pw-record --rate 16000 --channels 1 --format s16 "$audio" >/dev/null 2>&1 &
  echo $! > "$pidfile"
  bar_dot start
}

stop() {
  [[ -f "$pidfile" ]] || exit 0
  bar_dot transcribe
  # Whatever happens next (nothing heard, an error, typing), the indicator ends.
  trap 'bar_dot stop' EXIT
  kill -INT "$(cat "$pidfile")" 2>/dev/null || true
  rm -f "$pidfile"
  sleep 0.2
  [[ -s "$audio" ]] || exit 0
  text="$("$(transcriber)" -m "$model" -f "$audio" -l auto -nt -np 2>/dev/null | tr '\n' ' ' | sed -E 's/^ +| +$//g; s/  +/ /g')"
  rm -f "$audio"
  if [[ -z "$text" || "$text" == "[BLANK_AUDIO]" ]]; then
    notify "Nothing heard" "Hold SUPER + D while you speak."
    exit 0
  fi
  wtype -- "$text"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  *) echo "Usage: dictate.sh start|stop" >&2; exit 2 ;;
esac
