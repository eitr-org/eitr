#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

GCP_MENUS_DIR="$CLOUD_MENUS_DIR/gcp"
CLOUD_PROVIDER_HELPERS="$CLOUD_MENUS_DIR/context-auth.sh"

if [[ "$(realpath -- "$0")" == "$(realpath -- "$GCP_MENUS_DIR")/"* && "${1:-}" != --setup && -z "${EITR_CLOUD_CONTEXT:-}" ]]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" show gcp-contexts
fi

cloud_terminal_env() {
  # Tool scripts hold the project they chose in $project; passing it on keeps that
  # choice when the terminal returns to the menu.
  local CLOUDSDK_CORE_PROJECT="${CLOUDSDK_CORE_PROJECT:-${project:-}}"
  printf 'export EITR_CLOUD_PROVIDER=gcp\n'
  # gcloud treats an empty CLOUDSDK_* variable as an unset property, so only pass values.
  for key in EITR_CLOUD_CONTEXT CLOUDSDK_ACTIVE_CONFIG_NAME CLOUDSDK_CORE_ACCOUNT CLOUDSDK_CORE_PROJECT; do
    if [ -n "${!key:-}" ]; then
      printf 'export %s=%q\n' "$key" "${!key}"
    fi
  done
}

gcp_cli_available() {
  command -v gcloud >/dev/null 2>&1
}

require_gcloud() {
  if ! gcp_cli_available; then
    notify-send "GCP" "gcloud CLI is not installed"
    return 1
  fi
}

choose_gcp_project() {
  [ -n "${CLOUDSDK_CORE_PROJECT:-}" ] || return 1
  printf '%s\n' "$CLOUDSDK_CORE_PROJECT"
}

back_to_gcp_menu() {
  "$GCP_MENUS_DIR/menu.sh"
}
