#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/azure/common.sh"

subscription="$(choose_azure_subscription)" || exit 0

run_in_kitty "Azure ACR" "
cloud_header 'Azure Container Registries'
cloud_kv 'Subscription' '$subscription'
echo

az acr list --subscription '$subscription' -o json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  group=\(.resourceGroup)  location=\(.location)  sku=\(.sku.name // \"N/A\")  login=\(.loginServer // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
