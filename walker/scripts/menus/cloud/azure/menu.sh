#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/azure/common.sh"

case "${1:-}" in
  --login|--setup)
    if ! azure_cli_available; then
      notify-send "Azure" "Azure CLI is not installed"
      exit 0
    fi
    run_in_kitty "Azure Login" "
cloud_header 'Azure login'
cloud_success 'Opening az login...'
echo
cloud_context_login
" close-on-success
    exit 0
    ;;
  --check-auth)
    require_az || exit 0
    run_in_kitty "Azure Auth" "
cloud_header 'Azure auth'
az account show ${EITR_AZURE_SUBSCRIPTION:+--subscription '$EITR_AZURE_SUBSCRIPTION'} -o json \
| jq -r '\"\u001b[34mName:\u001b[0m \(.name)\", \"\u001b[34mID:\u001b[0m   \(.id)\", \"\u001b[34mUser:\u001b[0m \(.user.name // \"N/A\")\"'
" close-on-key toggle
    exit 0
    ;;
  --subscriptions)
    require_az || exit 0
    run_in_kitty "Azure Subscriptions" "
cloud_header 'Azure subscriptions'
az account list -o json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  id=\(.id)  state=\(.state)\"' \
| cloud_fzf 'Subscriptions' plain
" close-on-success toggle
    exit 0
    ;;
esac

options="󰊭  Login
󰑐  Refresh
󰅟  Check Auth
󰏗  Subscriptions
󰉖  Resource Groups
  Virtual Machines
󰉋  Storage Accounts
󰠇  AKS Clusters
󰣇  App Services
󰈳  SQL Servers
  Container Registries
󰊕  Function Apps
󰖟  Virtual Networks
󰢬  Activity Logs"

chosen="$(printf '%s\n' "$options" | walker_menu "Azure — ${EITR_CLOUD_CONTEXT:-Select a tool}")"

case "$chosen" in
  "󰑐  Refresh")
    run_in_kitty "Azure Refresh" "cloud_context_refresh" close-on-key toggle
    ;;
  "󰊭  Login")
    if ! azure_cli_available; then
      notify-send "Azure" "Azure CLI is not installed"
      exit 0
    fi
    run_in_kitty "Azure Login" "
cloud_header 'Azure login'
cloud_success 'Opening az login...'
echo
cloud_context_login
" close-on-success
    ;;
  "󰅟  Check Auth")
    require_az || exit 0
    run_in_kitty "Azure Auth" "
cloud_header 'Azure auth'
az account show ${EITR_AZURE_SUBSCRIPTION:+--subscription '$EITR_AZURE_SUBSCRIPTION'} -o json \
| jq -r '\"\u001b[34mName:\u001b[0m \(.name)\", \"\u001b[34mID:\u001b[0m   \(.id)\", \"\u001b[34mUser:\u001b[0m \(.user.name // \"N/A\")\"'
" close-on-key toggle
    ;;
  "󰏗  Subscriptions")
    require_az || exit 0
    run_in_kitty "Azure Subscriptions" "
cloud_header 'Azure subscriptions'
az account list -o json \
| jq -r '.[] | \"\u001b[36m\(.name)\u001b[0m  id=\(.id)  state=\(.state)\"' \
| cloud_fzf 'Subscriptions' plain
" close-on-success toggle
    ;;
  "󰉖  Resource Groups")
    "$AZURE_MENUS_DIR/resource-groups.sh"
    ;;
  "  Virtual Machines")
    "$AZURE_MENUS_DIR/compute.sh"
    ;;
  "󰉋  Storage Accounts")
    "$AZURE_MENUS_DIR/storage.sh"
    ;;
  "󰠇  AKS Clusters")
    "$AZURE_MENUS_DIR/aks.sh"
    ;;
  "󰣇  App Services")
    "$AZURE_MENUS_DIR/app-service.sh"
    ;;
  "󰈳  SQL Servers")
    "$AZURE_MENUS_DIR/sql.sh"
    ;;
  "  Container Registries")
    "$AZURE_MENUS_DIR/acr.sh"
    ;;
  "󰊕  Function Apps")
    "$AZURE_MENUS_DIR/functions.sh"
    ;;
  "󰖟  Virtual Networks")
    "$AZURE_MENUS_DIR/vnet.sh"
    ;;
  "󰢬  Activity Logs")
    "$AZURE_MENUS_DIR/logs.sh"
    ;;
  "")
    exit 0
    ;;
esac
