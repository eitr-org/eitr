#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

GCP_MENUS_DIR="$CLOUD_MENUS_DIR/gcp"
CLOUD_PROVIDER_HELPERS="$CLOUD_MENUS_DIR/context-auth.sh"

if [[ "$(realpath -- "$0")" == "$(realpath -- "$GCP_MENUS_DIR")/"* && "${1:-}" != --setup && -z "${EITR_CLOUD_CONTEXT:-}" ]]; then
  context_exports="$(python3 "$CLOUD_MENUS_DIR/contexts.py" gcp --shell --defer-project)" || exit 0
  eval "$context_exports"
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

# Prints the chosen project ID; returns 1 on cancel or failure.
choose_gcp_project() {
  if [ -n "${CLOUDSDK_CORE_PROJECT:-}" ] && [ -n "${EITR_CLOUD_CONTEXT:-}" ]; then
    printf '%s\n' "$CLOUDSDK_CORE_PROJECT"
    return
  fi
  local projects
  local chosen

  require_gcloud || return 1

  if ! projects="$(gcloud projects list --format='value(projectId)' 2>/dev/null)"; then
    notify-send "GCP" "Failed to list projects. Login or configure gcloud first."
    return 1
  fi

  if [ -z "$projects" ]; then
    notify-send "GCP" "No projects found"
    return 1
  fi

  chosen="$(printf "%s\n" "$projects" | walker_menu "GCP Project")"
  [ -n "$chosen" ] || return 1

  printf '%s\n' "$chosen"
}

back_to_gcp_menu() {
  "$GCP_MENUS_DIR/menu.sh"
}
