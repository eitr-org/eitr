#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_docdb_cluster() {
  local clusters chosen

  if ! clusters="$(aws_cli docdb describe-db-clusters | jq -r '.DBClusters[].DBClusterIdentifier')"; then
    notify-send "DocumentDB" "Failed to list clusters"
    return 1
  fi

  [ -z "$clusters" ] && notify-send "DocumentDB" "No clusters found" && return 1
  chosen="$(printf "%s\n" "$clusters" | walker_menu "DocumentDB Cluster")"
  [ -z "$chosen" ] && return 1
  echo "$chosen"
}

options="󰘦  Clusters
  Instances
󰅟  Cluster details
󰕢  Recent events"

chosen="$(printf '%s\n' "$options" | walker_menu "DocumentDB - $AWS_PROFILE")"

case "$chosen" in
  "󰘦  Clusters")
    run_in_kitty "DocumentDB Clusters - $AWS_PROFILE" "
cloud_header 'DocumentDB clusters'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) docdb describe-db-clusters \
| jq -r '.DBClusters[] | \"\u001b[36m\(.DBClusterIdentifier)\u001b[0m  status=\(.Status)  engine=\(.Engine)  endpoint=\(.Endpoint // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "  Instances")
    run_in_kitty "DocumentDB Instances - $AWS_PROFILE" "
cloud_header 'DocumentDB instances'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) docdb describe-db-instances \
| jq -r '.DBInstances[] | \"\u001b[36m\(.DBInstanceIdentifier)\u001b[0m  cluster=\(.DBClusterIdentifier // \"N/A\")  status=\(.DBInstanceStatus)  class=\(.DBInstanceClass)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰅟  Cluster details")
    cluster="$(choose_docdb_cluster)" || exit 0
    quoted_cluster="$(shell_quote "$cluster")"

    run_in_kitty "DocumentDB Cluster - $AWS_PROFILE" "
cloud_header 'DocumentDB cluster details'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Cluster' $quoted_cluster
echo

$(aws_base) docdb describe-db-clusters --db-cluster-identifier $quoted_cluster | cloud_json
" close-on-success toggle
    ;;
  "󰕢  Recent events")
    cluster="$(choose_docdb_cluster)" || exit 0
    quoted_cluster="$(shell_quote "$cluster")"

    run_in_kitty "DocumentDB Events - $AWS_PROFILE" "
cloud_header 'DocumentDB recent events'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Cluster' $quoted_cluster
echo

$(aws_base) docdb describe-events --source-identifier $quoted_cluster --duration 60 \
| jq -r '.Events[] | \"\u001b[90m\(.Date)\u001b[0m  \u001b[36m\(.SourceIdentifier // \"N/A\")\u001b[0m  \(.Message)\"' \
| cloud_fzf 'Events'
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
