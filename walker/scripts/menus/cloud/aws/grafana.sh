#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

options="󰨇  Workspaces
󰈹  Open workspace
󰅟  Workspace details"

chosen="$(printf '%s\n' "$options" | walker_menu "Amazon Grafana - $AWS_PROFILE")"

choose_workspace() {
  local workspaces chosen

  if ! workspaces="$(aws_cli grafana list-workspaces | jq -r '.workspaces[] | "\(.name)  \(.id)"')"; then
    notify-send "Amazon Grafana" "Failed to list workspaces"
    return 1
  fi

  [ -z "$workspaces" ] && notify-send "Amazon Grafana" "No workspaces found" && return 1
  chosen="$(printf "%s\n" "$workspaces" | walker_menu "Grafana Workspace")"
  [ -z "$chosen" ] && return 1
  echo "$chosen" | awk '{ print $NF }'
}

case "$chosen" in
  "󰨇  Workspaces")
    run_in_kitty "Grafana Workspaces - $AWS_PROFILE" "
cloud_header 'Amazon Grafana workspaces'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) grafana list-workspaces \
| jq -r '.workspaces[] | \"\u001b[36m\(.name)\u001b[0m  id=\(.id)  status=\(.status)  endpoint=\(.endpoint // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰈹  Open workspace")
    workspace_id="$(choose_workspace)" || exit 0

    if ! endpoint="$(aws_cli grafana describe-workspace --workspace-id "$workspace_id" | jq -r '.workspace.endpoint // empty')"; then
      notify-send "Amazon Grafana" "Failed to get workspace endpoint"
      exit 1
    fi

    [ -z "$endpoint" ] && notify-send "Amazon Grafana" "Workspace has no endpoint" && exit 0
    xdg-open "https://$endpoint" >/dev/null 2>&1 &
    ;;
  "󰅟  Workspace details")
    workspace_id="$(choose_workspace)" || exit 0
    quoted_workspace_id="$(shell_quote "$workspace_id")"

    run_in_kitty "Grafana Workspace - $AWS_PROFILE" "
cloud_header 'Amazon Grafana workspace'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Workspace' $quoted_workspace_id
echo

$(aws_base) grafana describe-workspace --workspace-id $quoted_workspace_id | cloud_json
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
