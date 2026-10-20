#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

AZURE_MENUS_DIR="$CLOUD_MENUS_DIR/azure"
CLOUD_PROVIDER_HELPERS="$CLOUD_MENUS_DIR/context-auth.sh"

if [[ "$(realpath -- "$0")" == "$(realpath -- "$AZURE_MENUS_DIR")/"* && "${1:-}" != --setup && -z "${EITR_CLOUD_CONTEXT:-}" ]]; then
  context_exports="$(python3 "$CLOUD_MENUS_DIR/contexts.py" azure --shell)" || exit 0
  eval "$context_exports"
fi

cloud_terminal_env() {
  printf 'export EITR_CLOUD_PROVIDER=azure\nexport EITR_AZURE_TENANT=%q\n' "${EITR_AZURE_TENANT:-}"
  printf 'export EITR_CLOUD_CONTEXT=%q\nexport EITR_AZURE_SUBSCRIPTION=%q\n' "${EITR_CLOUD_CONTEXT:-}" "${EITR_AZURE_SUBSCRIPTION:-}"
}

azure_cli_available() {
  command -v az >/dev/null 2>&1
}

require_az() {
  if ! azure_cli_available; then
    notify-send "Azure" "Azure CLI is not installed"
    return 1
  fi
}

# Prints the chosen subscription ID; returns 1 on cancel or failure.
choose_azure_subscription() {
  if [ -n "${EITR_AZURE_SUBSCRIPTION:-}" ]; then
    printf '%s\n' "$EITR_AZURE_SUBSCRIPTION"
    return
  fi
  local subscriptions
  local chosen

  require_az || return 1

  if ! subscriptions="$(az account list --query '[].{name:name,id:id}' -o tsv 2>/dev/null)"; then
    notify-send "Azure" "Failed to list subscriptions. Login or configure az first."
    return 1
  fi

  if [ -z "$subscriptions" ]; then
    notify-send "Azure" "No subscriptions found"
    return 1
  fi

  chosen="$(printf "%s\n" "$subscriptions" | awk -F '\t' '{ print $1 "  " $2 }' | walker_menu "Azure Subscription")"
  [ -n "$chosen" ] || return 1

  printf '%s\n' "$chosen" | awk '{ print $NF }'
}

back_to_azure_menu() {
  "$AZURE_MENUS_DIR/menu.sh"
}
