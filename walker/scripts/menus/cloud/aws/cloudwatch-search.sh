#!/usr/bin/env bash
# Print CloudWatch log events for fzf. Modes:
#   (none)  print events for the saved query and range
#   search  prompt for a new filter, then print
#   time    prompt for a new range, then print
#   plain   print raw messages for AWS_CW_WORD without fzf state
# Uses AWS_PROFILE/AWS_REGION from the environment.

set -o pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

mode="${1:-}"

filter_events() {
  local word="$1"
  local minutes="$2"
  local args=(
    logs filter-log-events
    --log-group-name "$AWS_CW_LOG_GROUP"
    --start-time "$(date -d "$minutes minutes ago" +%s%3N)"
    --end-time "$(date +%s%3N)"
  )

  if [ -n "$word" ]; then
    args+=(--filter-pattern "$word")
  fi

  aws "${args[@]}"
}

if [ "$mode" = "plain" ]; then
  filter_events "${AWS_CW_WORD:-}" "$AWS_CW_MINUTES" | jq -r '.events[].message'
  exit
fi

if [ "$mode" = "search" ]; then
  if new_word="$(ask_search_word "CloudWatch search")"; then
    printf '%s' "$new_word" > "$AWS_CW_STATE_DIR/query"
  fi
elif [ "$mode" = "time" ]; then
  if new_minutes="$(choose_time_range_minutes)"; then
    printf '%s' "$new_minutes" > "$AWS_CW_STATE_DIR/minutes"
  fi
fi

word="$(cat "$AWS_CW_STATE_DIR/query" 2>/dev/null || true)"
minutes="$(cat "$AWS_CW_STATE_DIR/minutes" 2>/dev/null || printf '%s' "$AWS_CW_MINUTES")"

display_word="${word:-<all logs>}"
if [ "${#display_word}" -gt 32 ]; then
  display_word="${display_word:0:29}..."
fi

printf '\033[2mQ: %s | %sm\033[0m\n' "$display_word" "$minutes"

if ! response="$(filter_events "$word" "$minutes" 2>&1)"; then
  printf '\033[31mCloudWatch search failed:\033[0m %s\n' "$response"
  exit 0
fi

printf '%s\n' "$response" | jq -r '
  if (.events | length) == 0 then
    "No logs found."
  else
    .events[]
    | "\u001b[90m\(.timestamp / 1000 | todate)\u001b[0m  \u001b[36m\(.logStreamName)\u001b[0m  \(.message
        | gsub("ERROR"; "\u001b[31mERROR\u001b[0m")
        | gsub("WARN"; "\u001b[33mWARN\u001b[0m")
        | gsub("INFO"; "\u001b[36mINFO\u001b[0m")
        | gsub("Exception"; "\u001b[31mException\u001b[0m")
        | gsub("Traceback"; "\u001b[31mTraceback\u001b[0m")
        | gsub("failed"; "\u001b[31mfailed\u001b[0m")
        | gsub("Failed"; "\u001b[31mFailed\u001b[0m"))"
  end
'
