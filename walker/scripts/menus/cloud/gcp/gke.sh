#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0

run_in_kitty "GCP GKE - $project" "
cloud_header 'GCP GKE clusters'
cloud_kv 'Project' '$project'
echo

gcloud container clusters list --project '$project' --format=json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  location=\(.location)  status=\(.status)  version=\(.currentMasterVersion // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
