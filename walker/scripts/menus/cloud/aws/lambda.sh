#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_lambda_function() {
  local functions chosen

  if ! functions="$(aws_cli lambda list-functions | jq -r '.Functions[].FunctionName')"; then
    notify-send "Lambda" "Failed to list functions"
    return 1
  fi

  [ -z "$functions" ] && notify-send "Lambda" "No functions found" && return 1
  chosen="$(printf "%s\n" "$functions" | walker_menu "Lambda Function")"
  [ -z "$chosen" ] && return 1
  echo "$chosen"
}

options="󰡱  Functions
󰅟  Function config
󰢬  Recent logs
  Recent errors"

chosen="$(printf '%s\n' "$options" | walker_menu "Lambda - $AWS_PROFILE")"

lambda_logs_command() {
  local function_name="$1"
  local minutes="$2"
  local filter_pattern="$3"
  local quoted_function_name quoted_log_group quoted_filter_pattern filter_option filter_label

  quoted_function_name="$(shell_quote "$function_name")"
  quoted_log_group="$(shell_quote "/aws/lambda/$function_name")"
  quoted_filter_pattern="$(shell_quote "$filter_pattern")"

  if [ -n "$filter_pattern" ]; then
    filter_option="--filter-pattern $quoted_filter_pattern"
    filter_label="$quoted_filter_pattern"
  else
    filter_label="All"
  fi

  cat <<EOF
cloud_header 'Lambda logs'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Function' $quoted_function_name
cloud_kv 'Filter' $filter_label
cloud_kv 'Minutes' '$minutes'
echo

$(aws_base) logs filter-log-events \\
  --log-group-name $quoted_log_group \\
  $filter_option \\
  --start-time $(minutes_ago_ms "$minutes") \\
  --end-time $(now_ms) \\
| jq -r '
  if (.events | length) == 0 then
    "No logs found."
  else
    .events[]
    | "\u001b[90m\(.timestamp / 1000 | todate)\u001b[0m  \u001b[36m\(.logStreamName)\u001b[0m  \(.message
        | gsub("ERROR"; "\u001b[31mERROR\u001b[0m")
        | gsub("WARN"; "\u001b[33mWARN\u001b[0m")
        | gsub("Exception"; "\u001b[31mException\u001b[0m")
        | gsub("Task timed out"; "\u001b[31mTask timed out\u001b[0m"))"
  end
' | cloud_fzf 'Lambda logs'
EOF
}

case "$chosen" in
  "󰡱  Functions")
    run_in_kitty "Lambda Functions - $AWS_PROFILE" "
cloud_header 'Lambda functions'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) lambda list-functions \
| jq -r '.Functions[] | \"\u001b[36m\(.FunctionName)\u001b[0m  runtime=\(.Runtime // \"N/A\")  memory=\(.MemorySize)MB  timeout=\(.Timeout)s  updated=\(.LastModified)\"' \
| cloud_fzf 'Functions' plain
" close-on-success toggle
    ;;
  "󰅟  Function config")
    function_name="$(choose_lambda_function)" || exit 0
    quoted_function_name="$(shell_quote "$function_name")"

    run_in_kitty "Lambda Config - $AWS_PROFILE" "
cloud_header 'Lambda function config'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Function' $quoted_function_name
echo

$(aws_base) lambda get-function-configuration --function-name $quoted_function_name | cloud_json | cloud_report
" close-on-success toggle
    ;;
  "󰢬  Recent logs")
    function_name="$(choose_lambda_function)" || exit 0
    minutes="$(choose_time_range_minutes)" || exec "$0" "$AWS_PROFILE"
    run_in_kitty "Lambda Logs - $AWS_PROFILE" "$(lambda_logs_command "$function_name" "$minutes" "")" close-on-success toggle
    ;;
  "  Recent errors")
    function_name="$(choose_lambda_function)" || exit 0
    minutes="$(choose_time_range_minutes)" || exec "$0" "$AWS_PROFILE"
    run_in_kitty "Lambda Errors - $AWS_PROFILE" "$(lambda_logs_command "$function_name" "$minutes" "ERROR ?Exception ?Timeout")" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
