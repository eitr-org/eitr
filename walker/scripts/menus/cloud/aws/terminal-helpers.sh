#!/usr/bin/env bash
# AWS-only helpers sourced by generated terminal scripts after terminal-helpers.sh.

AWS_HELPERS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Interactive CloudWatch log search: Ctrl-S changes the filter, Ctrl-T the range.
aws_cloudwatch_search_fzf() {
  local log_group="$1"
  local initial_word="$2"
  local minutes="$3"
  local search="$AWS_HELPERS_DIR/cloudwatch-search.sh"
  local state_dir
  local reload_command
  local output
  local status

  if ! command -v fzf >/dev/null 2>&1; then
    AWS_CW_LOG_GROUP="$log_group" AWS_CW_MINUTES="$minutes" AWS_CW_WORD="$initial_word" \
      bash "$search" plain
    return
  fi

  state_dir="$(mktemp -d "${XDG_RUNTIME_DIR:-/tmp}/eitr-cloudwatch.XXXXXX")"
  trap 'rm -rf -- "$state_dir"; exit 130' INT HUP TERM
  printf '%s' "$initial_word" > "$state_dir/query"
  printf '%s' "$minutes" > "$state_dir/minutes"

  export AWS_CW_STATE_DIR="$state_dir" AWS_CW_LOG_GROUP="$log_group" AWS_CW_MINUTES="$minutes"
  reload_command="bash $(printf '%q' "$search")"

  cloud_fzf_base_args
  cloud_fzf_preview_args

  output="$(bash "$search" \
    | fzf \
      "${CLOUD_FZF_ARGS[@]}" \
      --prompt="Logs > " \
      --header="C-s search  C-t time  C-y copy  Esc close" \
      --header-lines=1 \
      "${CLOUD_FZF_PREVIEW_ARGS[@]}" \
      --bind "ctrl-s:reload($reload_command search)+clear-query" \
      --bind "ctrl-t:reload($reload_command time)+clear-query" \
      --bind 'ctrl-y:execute-silent(printf "%b\n" {} | sed "s/\x1b\[[0-9;]*m//g" | wl-copy)' \
      --expect=ctrl-c,esc)"
  status=$?
  rm -rf -- "$state_dir"
  trap - HUP TERM
  trap 'exit 130' INT

  cloud_fzf_result "$status" "$output"
}
