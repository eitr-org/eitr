#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0
if ! minutes="$(choose_time_range_minutes)"; then
  back_to_gcp_menu
  exit 0
fi

since="$(date -u -d "$minutes minutes ago" '+%Y-%m-%dT%H:%M:%SZ')"

run_in_kitty "GCP Logs - $project" "
cloud_header 'GCP logs'
cloud_kv 'Project' '$project'
cloud_kv 'Since' '$since'
echo

gcloud logging read 'timestamp >= \"$since\"' --project '$project' --limit=300 --format=json \
| jq -r '.[] | \"\u001b[90m\(.timestamp)\u001b[0m  \u001b[36m\(.resource.type)\u001b[0m  \((.severity // \"DEFAULT\"))  \((.textPayload // .jsonPayload.message // .protoPayload.methodName // \"\"))\"' \
| cloud_fzf 'Logs'
" close-on-success toggle
