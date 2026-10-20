#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="${1:-}"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE" aws-ecs
fi

if [ -z "$AWS_PROFILE" ]; then
  exit 0
fi

choose_ecs_cluster() {
  printf '%s\n' "${EITR_PICK_choose_ecs_cluster:?Missing resource selection}"
}

choose_ecs_service() {
  printf '%s\n' "${EITR_PICK_choose_ecs_service:?Missing resource selection}"
}

ECS_CLUSTER="$(choose_ecs_cluster)" || exit 0
ECS_SERVICE="$(choose_ecs_service "$ECS_CLUSTER")" || exit 0
RETURN_TO_ECS_COMMAND="$CLOUD_MENU_RETURN_COMMAND"

service_status_command() {
  cat <<EOF
cloud_header "ECS service status"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
echo

$(aws_base) ecs describe-services \\
  --cluster "$ECS_CLUSTER" \\
  --services "$ECS_SERVICE" \\
| jq -r '
  if (.services | length) == 0 then
    "No ECS service found."
  else
    .services[] |
    "\u001b[36mService:\u001b[0m \(.serviceName)
\u001b[34mStatus:\u001b[0m \(.status)
\u001b[34mDesired:\u001b[0m \(.desiredCount)
\u001b[34mRunning:\u001b[0m \(.runningCount)
\u001b[34mPending:\u001b[0m \(.pendingCount)

\u001b[35mDeployments:\u001b[0m
" +
    (
      [.deployments[]
        | "- \u001b[36m\(.status)\u001b[0m | desired=\(.desiredCount) running=\(.runningCount) pending=\(.pendingCount) rollout=\(.rolloutState // "N/A") reason=\(.rolloutStateReason // "N/A")"
      ] | join("\n")
    )
  end
' | cloud_report
EOF
}

service_events_command() {
  cat <<EOF
cloud_header "ECS service events"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
echo

$(aws_base) ecs describe-services \\
  --cluster "$ECS_CLUSTER" \\
  --services "$ECS_SERVICE" \\
| jq -r '
  if (.services | length) == 0 then
    "No ECS service found."
  elif (.services[0].events | length) == 0 then
    "No ECS service events found."
  else
    .services[0].events[:30][]
    | "\u001b[90m\(.createdAt)\u001b[0m  \(.message)"
  end
' | cloud_report
EOF
}

running_tasks_command() {
  cat <<EOF
cloud_header "Running ECS tasks"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
echo

TASKS=\$($(aws_base) ecs list-tasks \\
  --cluster "$ECS_CLUSTER" \\
  --service-name "$ECS_SERVICE" \\
  --desired-status RUNNING \\
  | jq -r '.taskArns[]')

if [ -z "\$TASKS" ]; then
  echo "No running tasks found."
  exit 0
fi

$(aws_base) ecs describe-tasks \\
  --cluster "$ECS_CLUSTER" \\
  --tasks \$TASKS \\
| jq -r '
  .tasks[]
  | "\u001b[36m\(.taskArn | split("/")[-1])\u001b[0m  last=\(.lastStatus) desired=\(.desiredStatus) health=\(.healthStatus // "N/A") started=\(.startedAt // "N/A") cpu=\(.cpu // "N/A") memory=\(.memory // "N/A")"
' | cloud_report
EOF
}

stopped_tasks_command() {
  cat <<EOF
cloud_header "Recently stopped ECS tasks"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
echo

TASKS=\$($(aws_base) ecs list-tasks \\
  --cluster "$ECS_CLUSTER" \\
  --service-name "$ECS_SERVICE" \\
  --desired-status STOPPED \\
  --max-results 10 \\
  | jq -r '.taskArns[]')

if [ -z "\$TASKS" ]; then
  echo "No recently stopped tasks found."
  exit 0
fi

$(aws_base) ecs describe-tasks \\
  --cluster "$ECS_CLUSTER" \\
  --tasks \$TASKS \\
| jq -r '
  .tasks[]
  | "\u001b[36m\(.taskArn | split("/")[-1])\u001b[0m  code=\(.stopCode // "N/A") stopped=\(.stoppedAt // "N/A") reason=\(.stoppedReason // "N/A") containers=\([.containers[] | "\(.name):exit=\(.exitCode // "N/A") reason=\(.reason // "N/A")"] | join("; "))"
' | cloud_report
EOF
}

deployments_command() {
  cat <<EOF
cloud_header "ECS deployments"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
echo

$(aws_base) ecs describe-services \\
  --cluster "$ECS_CLUSTER" \\
  --services "$ECS_SERVICE" \\
| jq -r '
  if (.services | length) == 0 then
    "No ECS service found."
  elif (.services[0].deployments | length) == 0 then
    "No ECS deployments found."
  else
    .services[0].deployments[]
    | "\u001b[36m\(.status)\u001b[0m  id=\(.id | split("/")[-1]) desired=\(.desiredCount) running=\(.runningCount) pending=\(.pendingCount) failed=\(.failedTasks) rollout=\(.rolloutState // "N/A") created=\(.createdAt) updated=\(.updatedAt) reason=\(.rolloutStateReason // "N/A")"
  end
' | cloud_report
EOF
}

deployment_logs_command() {
  cat <<EOF
cloud_header "ECS latest deployment logs"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
cloud_kv "Service" "$ECS_SERVICE"
cloud_kv "Log group" "$LOG_GROUP"
echo

SERVICE_JSON=\$($(aws_base) ecs describe-services \\
  --cluster "$ECS_CLUSTER" \\
  --services "$ECS_SERVICE")

DEPLOYMENT_START=\$(printf '%s' "\$SERVICE_JSON" | jq -r '
  [.services[0].deployments[]?.createdAt]
  | sort
  | last
  // empty
')

if [ -n "\$DEPLOYMENT_START" ]; then
  START_MS=\$(date -d "\$DEPLOYMENT_START" +%s%3N 2>/dev/null || date -d "60 minutes ago" +%s%3N)
  cloud_kv "Since" "\$DEPLOYMENT_START"
else
  START_MS=\$(date -d "60 minutes ago" +%s%3N)
  cloud_warn "Could not find deployment start time. Falling back to the last 60 minutes."
fi

echo

$(aws_base) logs filter-log-events \\
  --log-group-name "$LOG_GROUP" \\
  --start-time "\$START_MS" \\
  --end-time $(now_ms) \\
  --max-items 300 \\
| jq -r '
  if (.events | length) == 0 then
    "No logs found for the latest deployment window."
  else
    .events[]
    | "\u001b[90m\(.timestamp / 1000 | todate)\u001b[0m  \u001b[36m\(.logStreamName)\u001b[0m  \(.message
        | gsub("ERROR"; "\u001b[31mERROR\u001b[0m")
        | gsub("WARN"; "\u001b[33mWARN\u001b[0m")
        | gsub("Exception"; "\u001b[31mException\u001b[0m")
        | gsub("Traceback"; "\u001b[31mTraceback\u001b[0m")
        | gsub("failed"; "\u001b[31mfailed\u001b[0m")
        | gsub("Failed"; "\u001b[31mFailed\u001b[0m"))"
  end
' | cloud_fzf "Deployment logs"
EOF
}

list_clusters_command() {
  cat <<EOF
cloud_header "ECS clusters"
cloud_kv "Profile" "$AWS_PROFILE"
echo

$(aws_base) ecs list-clusters | jq -r '.clusterArns[] | "\u001b[36m\(split("/")[-1])\u001b[0m  \u001b[90m\(.)\u001b[0m"' | cloud_report
EOF
}

list_services_command() {
  cat <<EOF
cloud_header "ECS services"
cloud_kv "Profile" "$AWS_PROFILE"
cloud_kv "Cluster" "$ECS_CLUSTER"
echo

$(aws_base) ecs list-services \\
  --cluster "$ECS_CLUSTER" \\
| jq -r '.serviceArns[] | "\u001b[36m\(split("/")[-1])\u001b[0m  \u001b[90m\(.)\u001b[0m"' \
| cloud_report
EOF
}

chosen="${EITR_CLOUD_ACTION:-}"

case "$chosen" in
  "󰅟  Service status")
    run_in_kitty "ECS Status - $AWS_PROFILE" "$(service_status_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰐱  Deployments")
    run_in_kitty "ECS Deployments - $AWS_PROFILE" "$(deployments_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰢬  Latest deploy logs")
    run_in_kitty "ECS Deploy Logs - $AWS_PROFILE" "$(deployment_logs_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰑓  Service events")
    run_in_kitty "ECS Events - $AWS_PROFILE" "$(service_events_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰐱  Running tasks")
    run_in_kitty "ECS Running Tasks - $AWS_PROFILE" "$(running_tasks_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "  Stopped tasks")
    run_in_kitty "ECS Stopped Tasks - $AWS_PROFILE" "$(stopped_tasks_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰌗  List clusters")
    run_in_kitty "ECS Clusters - $AWS_PROFILE" "$(list_clusters_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "󰓾  List services")
    run_in_kitty "ECS Services - $AWS_PROFILE" "$(list_services_command)" return-on-success toggle "$RETURN_TO_ECS_COMMAND"
    ;;
  "")
    exit 0
    ;;
esac
