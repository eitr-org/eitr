#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0

run_in_kitty "GCP VPC - $project" "
cloud_header 'GCP VPC networks'
cloud_kv 'Project' '$project'
echo

gcloud compute networks list --project '$project' --format=json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  mode=\(.routingConfig.routingMode // \"N/A\")  subnets=\(.subnetworks | length)  autoCreate=\(.autoCreateSubnetworks)\"' \
| cloud_report
" close-on-success toggle
