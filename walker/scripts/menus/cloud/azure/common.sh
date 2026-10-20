#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

AZURE_MENUS_DIR="$CLOUD_MENUS_DIR/azure"
CLOUD_PROVIDER_HELPERS="$CLOUD_MENUS_DIR/context-auth.sh"

if [[ "$(realpath -- "$0")" == "$(realpath -- "$AZURE_MENUS_DIR")/"* && "${1:-}" != --setup && -z "${EITR_CLOUD_CONTEXT:-}" ]]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" show azure-contexts
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

choose_azure_subscription() {
  [ -n "${EITR_AZURE_SUBSCRIPTION:-}" ] || return 1
  printf '%s\n' "$EITR_AZURE_SUBSCRIPTION"
}

back_to_azure_menu() {
  "$AZURE_MENUS_DIR/menu.sh"
}
