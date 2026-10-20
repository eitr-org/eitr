#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/azure/common.sh"

subscription="$(choose_azure_subscription)" || exit 0
if ! minutes="$(choose_time_range_minutes)"; then
  back_to_azure_menu
  exit 0
fi

start_time="$(date -u -d "$minutes minutes ago" '+%Y-%m-%dT%H:%M:%SZ')"

run_in_kitty "Azure Activity Logs" "
cloud_header 'Azure activity logs'
cloud_kv 'Subscription' '$subscription'
cloud_kv 'Since' '$start_time'
echo

az monitor activity-log list --subscription '$subscription' --start-time '$start_time' -o json \
| jq -r '.[] | \"\u001b[90m\(.eventTimestamp)\u001b[0m  \u001b[36m\(.resourceGroupName // \"N/A\")\u001b[0m  status=\(.status.value // \"N/A\")  \(.operationName.localizedValue // .operationName.value // \"\")\"' \
| cloud_fzf 'Activity'
" close-on-success toggle
