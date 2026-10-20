#!/usr/bin/env bash
# Output helpers sourced by the terminal scripts that run_in_kitty generates.

i18n_library="${EITR_LIBRARY_ROOT:-${EITR_CODE_ROOT:-/usr/share/eitr}/lib}/i18n.sh"
[[ -f "$i18n_library" ]] || i18n_library="${EITR_CODE_ROOT:-/usr/share/eitr}/distro/lib/i18n.sh"
# shellcheck source=distro/lib/i18n.sh
source "$i18n_library"

CLOUD_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLOUD_PALETTE="$CLOUD_HELPERS_DIR/../../themes/palette.py"

cloud_reset=$'\033[0m'
cloud_bold=$'\033[1m'
cloud_dim=$'\033[2m'
cloud_red=$'\033[31m'
cloud_green=$'\033[32m'
cloud_yellow=$'\033[33m'
cloud_blue=$'\033[34m'
cloud_cyan=$'\033[36m'

cloud_header() {
  printf '\n%s%s%s\n' "$cloud_bold$cloud_cyan" "$1" "$cloud_reset"
  printf '%s\n' "${cloud_dim}────────────────────────────────────────${cloud_reset}"
}

cloud_kv() {
  printf '%s%-12s%s %s\n' "$cloud_blue" "$1:" "$cloud_reset" "$2"
}

cloud_success() {
  printf '%s%s%s\n' "$cloud_green" "$1" "$cloud_reset"
}

cloud_warn() {
  printf '%s%s%s\n' "$cloud_yellow" "$1" "$cloud_reset"
}

cloud_error() {
  printf '%s%s%s\n' "$cloud_red" "$1" "$cloud_reset"
}

cloud_json() {
  if [ -t 1 ] && command -v bat >/dev/null 2>&1; then
    bat --language=json --style=plain --color=always
  else
    jq -C .
  fi
}

cloud_wait_for_key() {
  printf '\nPress any key to close.' > /dev/tty
  IFS= read -rsn1 < /dev/tty
  printf '\n' > /dev/tty
}

cloud_report() {
  if command -v bat >/dev/null 2>&1 && command -v less >/dev/null 2>&1; then
    bat --language=log --style=plain --color=always --paging=always
  elif command -v less >/dev/null 2>&1; then
    less -R
  elif command -v bat >/dev/null 2>&1; then
    bat --language=log --style=plain --color=always --paging=never
    cloud_wait_for_key
  else
    cat
    cloud_wait_for_key
  fi
}

# Common fzf arguments: theme-derived colors when a palette is available.
cloud_fzf_base_args() {
  local colors

  colors="$(python3 "$CLOUD_PALETTE" fzf-colors 2>/dev/null || true)"
  CLOUD_FZF_ARGS=(--ansi --no-sort --cycle --height=100% --layout=reverse --border)
  if [ -n "$colors" ]; then
    CLOUD_FZF_ARGS+=(--color="$colors")
  fi
}

cloud_fzf_preview_args() {
  CLOUD_FZF_PREVIEW_ARGS=(
    --preview "bash $(printf '%q' "$CLOUD_HELPERS_DIR/fzf-preview.sh") {}"
    --preview-window 'right,50%,wrap'
  )
}

# Interpret fzf's exit status and --expect key: 130 cancels the terminal
# script, Esc closes quietly, otherwise print the selection.
cloud_fzf_result() {
  local status="$1"
  local output="$2"
  local key

  if [ "$status" -ne 0 ]; then
    [ "$status" -eq 130 ] && return 130
    return 0
  fi

  key="${output%%$'\n'*}"
  [ "$key" = "ctrl-c" ] && return 130
  [ "$key" = "esc" ] && return 0

  printf '%s\n' "$output"
}

cloud_fzf() {
  local prompt="${1:-Filter}"
  local mode="${2:-preview}"
  local output
  local status

  if ! command -v fzf >/dev/null 2>&1; then
    cat
    return
  fi

  cloud_fzf_base_args
  CLOUD_FZF_PREVIEW_ARGS=()
  if [ "$mode" != "plain" ]; then
    cloud_fzf_preview_args
  fi

  output="$(fzf \
    "${CLOUD_FZF_ARGS[@]}" \
    --prompt="$prompt > " \
    --header="$(eitr_gettext 'C-y copy  Enter print  Esc close')" \
    "${CLOUD_FZF_PREVIEW_ARGS[@]}" \
    --bind 'ctrl-y:execute-silent(printf "%b\n" {} | sed "s/\x1b\[[0-9;]*m//g" | wl-copy)' \
    --expect=ctrl-c,esc)"
  status=$?

  cloud_fzf_result "$status" "$output"
}
