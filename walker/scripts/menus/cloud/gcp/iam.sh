#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0

run_in_kitty "GCP IAM - $project" "
cloud_header 'GCP IAM bindings'
cloud_kv 'Project' '$project'
echo

gcloud projects get-iam-policy '$project' --format=json \
| jq -r '.bindings[] | \"\u001b[36m\(.role)\u001b[0m  members=\(.members | join(\", \"))\"' \
| cloud_report
" close-on-success toggle
