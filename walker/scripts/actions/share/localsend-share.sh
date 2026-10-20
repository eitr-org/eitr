#!/bin/bash

set -euo pipefail

if (($# == 0)); then
  echo "Usage: localsend-share.sh clipboard|file|folder [PATH...]" >&2
  exit 1
fi

MODE="$1"
shift

pick_from_home() {
  local type="$1"
  shift
  find "$HOME" \( -name .cache -o -name node_modules -o -name .git \) -prune \
    -o -type "$type" -print 2>/dev/null | fzf "$@"
}

case "$MODE" in
  clipboard)
    TEMP_FILE="$(mktemp --tmpdir="${XDG_RUNTIME_DIR:-/tmp}" --suffix=.txt localsend-clipboard.XXXXXX)"
    trap 'rm -f -- "$TEMP_FILE"' EXIT
    wl-paste >"$TEMP_FILE"
    # The transient unit outlives this script, so it removes the file after sending.
    systemd-run --user --quiet --collect bash -c 'localsend --headless send "$1"; status=$?; rm -f -- "$1"; exit "$status"' localsend-share "$TEMP_FILE"
    trap - EXIT
    ;;
  file | folder)
    FILES=("$@")
    if ((${#FILES[@]} == 0)); then
      if [[ $MODE == "folder" ]]; then
        mapfile -t FILES < <(pick_from_home d || true)
      else
        mapfile -t FILES < <(pick_from_home f --multi || true)
      fi
    fi
    ((${#FILES[@]} > 0)) || exit 0
    systemd-run --user --quiet --collect localsend --headless send "${FILES[@]}"
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    exit 1
    ;;
esac
