#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
# Shared Walker helpers for the AWS, GCP and Azure menus. Provider common.sh
# files source this and may define:
#   cloud_terminal_env      print extra lines for the generated terminal script
#   CLOUD_PROVIDER_HELPERS  path of an extra helper file the terminal sources
#
# Machine-local values (profile labels, default region) live in
# ${XDG_CONFIG_HOME:-$HOME/.config}/eitr/cloud.env; see cloud.env.example.

CLOUD_MENUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLOUD_CONFIG_FILE="${EITR_CLOUD_CONFIG:-${XDG_CONFIG_HOME:-$HOME/.config}/eitr/cloud.env}"
WALKER_DMENU="$EITR_CODE_ROOT/walker/bin/walker-dmenu"
DEFAULT_TIME_RANGE_MINUTES="30"
CLOUD_TIME_RANGES=(1 2 3 5 10 15 30 60 120 360 1440)

if [ -f "$CLOUD_CONFIG_FILE" ]; then
  # shellcheck source=/dev/null
  source "$CLOUD_CONFIG_FILE"
fi

walker_menu() {
  local prompt="$1"
  shift

  if [ "$#" -gt 0 ]; then
    printf "%s\n" "$@"
  else
    cat
  fi | "$WALKER_DMENU" \
      --dmenu \
      --no-sort \
      --matching=contains \
      --cache-file /dev/null \
      --prompt "$prompt"
}

# Free-text prompt. Prints the entered text; returns 1 when cancelled.
ask_search_word() {
  local prompt="${1:-Search word}"
  local value

  value="$(printf "" | "$WALKER_DMENU" \
    --dmenu \
    --exec-search \
    --hide-scroll \
    --no-sort \
    --matching=contains \
    --cache-file /dev/null \
    --height 82 \
    --prompt "$prompt")"

  [ -n "$value" ] || return 1
  printf '%s\n' "$value"
}

# Prints the chosen minutes; returns 1 when cancelled so callers can go back.
# Non-numeric input falls back to DEFAULT_TIME_RANGE_MINUTES.
choose_time_range_minutes() {
  local value

  value="$(walker_menu "Minutes" "${CLOUD_TIME_RANGES[@]}")"
  [ -n "$value" ] || return 1

  if ! [[ "$value" =~ ^[0-9]+$ ]]; then
    value="$DEFAULT_TIME_RANGE_MINUTES"
  fi

  printf '%s\n' "$value"
}

shell_quote() {
  printf "%q" "$1"
}

cloud_menu_return_command() {
  local command
  local arg

  printf -v command "%q" "$0"

  for arg in "$@"; do
    printf -v command "%s %q" "$command" "$arg"
  done

  printf '%s' "$command"
}

CLOUD_DEFAULT_RETURN_COMMAND="$(cloud_menu_return_command "$@")"

# run_in_kitty TITLE COMMAND [CLOSE_MODE] [WINDOW_MODE] [RETURN_COMMAND]
#   CLOSE_MODE: close-on-success | return-on-success | close-on-key | (stay open)
#   WINDOW_MODE: toggle opens the floating cloud-terminal class
run_in_kitty() {
  local title="$1"
  local command="$2"
  local close_mode="${3:-close-on-success}"
  local window_mode="${4:-normal}"
  local return_command="${5:-}"
  local effective_return_command
  local provider_env=""
  local provider_helpers=""
  local temp_script

  effective_return_command="${return_command:-${CLOUD_MENU_RETURN_COMMAND:-$CLOUD_DEFAULT_RETURN_COMMAND}}"

  if declare -F cloud_terminal_env >/dev/null; then
    provider_env="$(cloud_terminal_env)"
  fi

  if [ -n "${CLOUD_PROVIDER_HELPERS:-}" ]; then
    provider_helpers="source $(printf '%q' "$CLOUD_PROVIDER_HELPERS")"
  fi

  temp_script="$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/eitr-cloud.XXXXXX")"

  cat > "$temp_script" <<EOF
#!/usr/bin/env bash

# This script is generated per launch; remove it once bash has opened it.
rm -f -- "\$0"

set -o pipefail

$provider_env

source $(printf '%q' "$CLOUD_MENUS_DIR/terminal-helpers.sh")
$provider_helpers

clear

python3 "$EITR_CODE_ROOT/walker/scripts/actions/task-terminal.py" --banner-only

if [ -n "\${EITR_CLOUD_CONTEXT:-}" ]; then
  cloud_kv Context "\$EITR_CLOUD_CONTEXT"
fi

trap 'exit 130' INT

$command

status=\$?

if [ "\$status" -eq 130 ]; then
  exit 130
fi

if [ "\$status" -eq 0 ] && { [ "$close_mode" = "close-on-success" ] || [ "$close_mode" = "return-on-success" ]; }; then
  if [ -n $(printf '%q' "$effective_return_command") ]; then
    nohup bash -lc $(printf "%q" "$effective_return_command") >/dev/null 2>&1 < /dev/null &
  fi
  exit 0
fi

if [ "$close_mode" = "close-on-key" ]; then
  echo
  echo "────────────────────────────────────────"
  echo "Exit code: \$status"
  echo "────────────────────────────────────────"
  cloud_wait_for_key
  exit "\$status"
fi

echo
echo "────────────────────────────────────────"
echo "Exit code: \$status"
eitr_gettext 'Terminal will stay open.'; printf '\\n'
eitr_gettext 'You can run more commands here manually.'; printf '\\n'
echo "────────────────────────────────────────"
echo

exec "\${SHELL:-/bin/bash}" -l
EOF

  chmod 700 "$temp_script"

  if [ "$window_mode" = "toggle" ]; then
    kitty --class cloud-terminal --title "$title" "$temp_script"
  else
    kitty --title "$title" "$temp_script"
  fi
}
