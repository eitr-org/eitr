#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

project="$(choose_gcp_project)" || exit 0

run_in_kitty "GCP Functions - $project" "
cloud_header 'GCP Cloud Functions'
cloud_kv 'Project' '$project'
echo

gcloud functions list --project '$project' --format=json \
| jq -r '.[] | \"\u001b[36m\(.name | split(\"/\")[-1])\u001b[0m  runtime=\(.buildConfig.runtime // .runtime // \"N/A\")  state=\(.state // .status // \"N/A\")  url=\(.serviceConfig.uri // .httpsTrigger.url // \"N/A\")\"' \
| cloud_fzf 'Functions' plain
" close-on-success toggle
