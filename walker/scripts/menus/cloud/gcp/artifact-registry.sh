#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0

run_in_kitty "GCP Artifact Registry - $project" "
cloud_header 'GCP Artifact Registry repositories'
cloud_kv 'Project' '$project'
echo

gcloud artifacts repositories list --project '$project' --format=json \
| jq -r '.[] | \"\u001b[36m\(.name | split(\"/\")[-1])\u001b[0m  location=\(.name | split(\"/\")[3])  format=\(.format)  mode=\(.mode // \"STANDARD\")\"' \
| cloud_report
" close-on-success toggle
