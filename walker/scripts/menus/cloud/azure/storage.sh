#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/azure/common.sh"

subscription="$(choose_azure_subscription)" || exit 0

run_in_kitty "Azure Storage" "
cloud_header 'Azure storage accounts'
cloud_kv 'Subscription' '$subscription'
echo

az storage account list --subscription '$subscription' -o json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  group=\(.resourceGroup)  location=\(.location)  sku=\(.sku.name)\"' \
| cloud_fzf 'Storage' plain
" close-on-success toggle
