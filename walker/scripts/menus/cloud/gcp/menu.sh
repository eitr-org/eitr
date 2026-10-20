#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/gcp/common.sh"

case "${1:-}" in
  --login|--setup)
    if ! gcp_cli_available; then
      notify-send "GCP" "gcloud CLI is not installed"
      exit 0
    fi
    run_in_kitty "GCP Login" "
cloud_header 'GCP login'
cloud_success 'Opening gcloud auth login...'
echo
cloud_context_login
" close-on-success
    exit 0
    ;;
  --check-auth)
    require_gcloud || exit 0
    run_in_kitty "GCP Auth" "
cloud_header 'GCP auth'
cloud_context_check_auth \
| jq -r '.[] | \"\u001b[36m\(.account)\u001b[0m  status=\(.status)\"'
" close-on-key toggle
    exit 0
    ;;
  --projects)
    require_gcloud || exit 0
    run_in_kitty "GCP Projects" "
cloud_header 'GCP projects'
gcloud projects list --format=json \
| jq -r '.[] | \"\u001b[36m\(.projectId)\u001b[0m  name=\(.name)  state=\(.lifecycleState)\"' \
| cloud_report
" close-on-success toggle
    exit 0
    ;;
esac

options="󰊭  Login
󰑐  Refresh
󰅟  Check Auth
󰏗  Projects
  Compute Instances
󰉋  Storage Buckets
󰠇  GKE Clusters
󰣇  Cloud Run
󰈳  Cloud SQL
  Artifact Registry
󰊕  Cloud Functions
󰖟  VPC Networks
󰒃  IAM
󰢬  Logs"

chosen="$(printf '%s\n' "$options" | walker_menu "GCP — ${EITR_CLOUD_CONTEXT:-Select a tool}")"

case "$chosen" in
  "󰑐  Refresh")
    run_in_kitty "GCP Refresh" "cloud_context_refresh" close-on-key toggle
    ;;
  "󰊭  Login")
    if ! gcp_cli_available; then
      notify-send "GCP" "gcloud CLI is not installed"
      exit 0
    fi
    run_in_kitty "GCP Login" "
cloud_header 'GCP login'
cloud_success 'Opening gcloud auth login...'
echo
cloud_context_login
" close-on-success
    ;;
  "󰅟  Check Auth")
    require_gcloud || exit 0
    run_in_kitty "GCP Auth" "
cloud_header 'GCP auth'
cloud_context_check_auth \
| jq -r '.[] | \"\u001b[36m\(.account)\u001b[0m  status=\(.status)\"'
" close-on-key toggle
    ;;
  "󰏗  Projects")
    require_gcloud || exit 0
    run_in_kitty "GCP Projects" "
cloud_header 'GCP projects'
gcloud projects list --format=json \
| jq -r '.[] | \"\u001b[36m\(.projectId)\u001b[0m  name=\(.name)  state=\(.lifecycleState)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "  Compute Instances")
    "$GCP_MENUS_DIR/compute.sh"
    ;;
  "󰉋  Storage Buckets")
    "$GCP_MENUS_DIR/storage.sh"
    ;;
  "󰠇  GKE Clusters")
    "$GCP_MENUS_DIR/gke.sh"
    ;;
  "󰣇  Cloud Run")
    "$GCP_MENUS_DIR/cloud-run.sh"
    ;;
  "󰈳  Cloud SQL")
    "$GCP_MENUS_DIR/sql.sh"
    ;;
  "  Artifact Registry")
    "$GCP_MENUS_DIR/artifact-registry.sh"
    ;;
  "󰊕  Cloud Functions")
    "$GCP_MENUS_DIR/functions.sh"
    ;;
  "󰖟  VPC Networks")
    "$GCP_MENUS_DIR/vpc.sh"
    ;;
  "󰒃  IAM")
    "$GCP_MENUS_DIR/iam.sh"
    ;;
  "󰢬  Logs")
    "$GCP_MENUS_DIR/logs.sh"
    ;;
  "")
    exit 0
    ;;
esac
