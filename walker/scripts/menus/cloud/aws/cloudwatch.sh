#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "$AWS_PROFILE" ]; then
  exit 0
fi

choose_log_group() {
  local log_groups
  local chosen

  if ! log_groups="$(aws_cli logs describe-log-groups | jq -r '.logGroups[].logGroupName')"; then
    notify-send "CloudWatch" "Failed to list log groups for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$log_groups" ]; then
    notify-send "CloudWatch" "No log groups found for $AWS_PROFILE"
    return 1
  fi

  chosen="$(printf "%s\n" "$log_groups" | walker_menu "Log Group")"

  if [ -z "$chosen" ]; then
    return 1
  fi

  echo "$chosen"
}

LOG_GROUP="$(choose_log_group)" || exit 0

cloudwatch_logs_command() {
  local filter_pattern="$1"
  local minutes="$2"
  local quoted_filter_pattern
  local quoted_log_group

  quoted_filter_pattern="$(shell_quote "$filter_pattern")"
  quoted_log_group="$(shell_quote "$LOG_GROUP")"

  cat <<EOF
cloud_header "CloudWatch logs"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Log group" "$LOG_GROUP"
cloud_kv "Filter" $quoted_filter_pattern
cloud_kv "Minutes" "$minutes"
echo

aws_cloudwatch_search_fzf $quoted_log_group $quoted_filter_pattern "$minutes"
EOF
}

all_logs_command() {
  local minutes="$1"
  local quoted_log_group

  quoted_log_group="$(shell_quote "$LOG_GROUP")"

  cat <<EOF
cloud_header "CloudWatch all logs"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Log group" "$LOG_GROUP"
cloud_kv "Minutes" "$minutes"
echo

aws_cloudwatch_search_fzf $quoted_log_group "" "$minutes"
EOF
}

search_word_logs_command() {
  local word="$1"
  local minutes="$2"
  local quoted_word
  local quoted_log_group

  quoted_word="$(shell_quote "$word")"
  quoted_log_group="$(shell_quote "$LOG_GROUP")"

  cat <<EOF
cloud_header "CloudWatch search"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Log group" "$LOG_GROUP"
cloud_kv "Word" $quoted_word
cloud_kv "Minutes" "$minutes"
echo

aws_cloudwatch_search_fzf $quoted_log_group $quoted_word "$minutes"
EOF
}

latest_streams_command() {
  cat <<EOF
cloud_header "Latest CloudWatch log streams"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Log group" "$LOG_GROUP"
echo

$(aws_base) logs describe-log-streams \\
  --log-group-name "$LOG_GROUP" \\
  --order-by LastEventTime \\
  --descending \\
  --max-items 20 \\
| jq -r '
  if (.logStreams | length) == 0 then
    "No log streams found."
  else
    .logStreams[]
    | "\u001b[90m\(.lastEventTimestamp / 1000 | todate)\u001b[0m  \u001b[36m\(.logStreamName)\u001b[0m"
  end
' | cloud_fzf "Streams"
EOF
}

while true; do
options="󰁫  All logs
  ERROR logs
  WARN logs
  INFO logs
  Search word
󰁫  Latest log streams"

chosen="$(printf '%s\n' "$options" | walker_menu "CloudWatch - $AWS_PROFILE")"

case "$chosen" in
  "󰁫  All logs")
    minutes="$(choose_time_range_minutes)" || continue
    run_in_kitty "CloudWatch Logs - $AWS_PROFILE" "$(all_logs_command "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  ERROR logs")
    minutes="$(choose_time_range_minutes)" || continue
    run_in_kitty "CloudWatch ERROR - $AWS_PROFILE" "$(cloudwatch_logs_command "ERROR" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  WARN logs")
    minutes="$(choose_time_range_minutes)" || continue
    run_in_kitty "CloudWatch WARN - $AWS_PROFILE" "$(cloudwatch_logs_command "WARN" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  INFO logs")
    minutes="$(choose_time_range_minutes)" || continue
    run_in_kitty "CloudWatch INFO - $AWS_PROFILE" "$(cloudwatch_logs_command "INFO" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  Search word")
    word="$(ask_search_word)" || continue

    minutes="$(choose_time_range_minutes)" || continue
    run_in_kitty "CloudWatch Search - $AWS_PROFILE" "$(search_word_logs_command "$word" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "󰁫  Latest log streams")
    run_in_kitty "CloudWatch Streams - $AWS_PROFILE" "$(latest_streams_command)" close-on-success toggle
    exit 0
    ;;
  "")
    exit 0
    ;;
esac
done
