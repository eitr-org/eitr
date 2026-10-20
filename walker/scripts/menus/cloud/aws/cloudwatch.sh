#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE" aws-cloudwatch
fi

if [ -z "$AWS_PROFILE" ]; then
  exit 0
fi

choose_log_group() {
  printf '%s\n' "${EITR_PICK_choose_log_group:?Missing resource selection}"
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

chosen="${EITR_CLOUD_ACTION:-}"

case "$chosen" in
  "󰁫  All logs")
    minutes="$(choose_time_range_minutes)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }
    run_in_kitty "CloudWatch Logs - $AWS_PROFILE" "$(all_logs_command "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  ERROR logs")
    minutes="$(choose_time_range_minutes)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }
    run_in_kitty "CloudWatch ERROR - $AWS_PROFILE" "$(cloudwatch_logs_command "ERROR" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  WARN logs")
    minutes="$(choose_time_range_minutes)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }
    run_in_kitty "CloudWatch WARN - $AWS_PROFILE" "$(cloudwatch_logs_command "WARN" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  INFO logs")
    minutes="$(choose_time_range_minutes)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }
    run_in_kitty "CloudWatch INFO - $AWS_PROFILE" "$(cloudwatch_logs_command "INFO" "$minutes")" close-on-success toggle
    exit 0
    ;;
  "  Search word")
    word="$(ask_search_word)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }

    minutes="$(choose_time_range_minutes)" || { bash -c "$CLOUD_MENU_RETURN_COMMAND"; exit 0; }
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
