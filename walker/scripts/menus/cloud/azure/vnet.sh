#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/azure/common.sh"

subscription="$(choose_azure_subscription)" || exit 0

run_in_kitty "Azure VNets" "
cloud_header 'Azure virtual networks'
cloud_kv 'Subscription' '$subscription'
echo

az network vnet list --subscription '$subscription' -o json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  group=\(.resourceGroup)  location=\(.location)  prefixes=\((.addressSpace.addressPrefixes // []) | join(\",\"))\"' \
| cloud_fzf 'Virtual networks' plain
" close-on-success toggle
