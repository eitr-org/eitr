#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE" aws-grafana
fi

[ -z "$AWS_PROFILE" ] && exit 0

chosen="${EITR_CLOUD_ACTION:-}"

choose_workspace() {
  printf '%s\n' "${EITR_PICK_choose_workspace:?Missing resource selection}"
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
    "$EITR_CODE_ROOT/walker/bin/app-launch" xdg-open "https://$endpoint" >/dev/null 2>&1 &
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
