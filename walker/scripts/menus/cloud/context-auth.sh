#!/usr/bin/env bash
# Context actions run inside the generated terminal, with inherited scope.
cloud_context_login() {
  if [ "$EITR_CLOUD_PROVIDER" = gcp ]; then
    if [ -n "${CLOUDSDK_ACTIVE_CONFIG_NAME:-}" ]; then
      gcloud auth login "${CLOUDSDK_CORE_ACCOUNT:?}" --no-activate
    else
      gcloud auth login
    fi
  elif [ -n "${EITR_AZURE_TENANT:-}" ]; then
    local previous status
    previous="$(az account show --query id -o tsv 2>/dev/null)" || previous=""
    AZURE_CORE_LOGIN_EXPERIENCE_V2=off az login --tenant "$EITR_AZURE_TENANT"
    status=$?
    # Authentication may reset Azure's cached default; restore it after signing in.
    if [ -n "$previous" ]; then
      az account set --subscription "$previous" || return 1
    fi
    [ "$status" -eq 0 ] || return "$status"
    az account show --subscription "${EITR_AZURE_SUBSCRIPTION:?}" -o json
  else
    az login
  fi
}

cloud_context_check_auth() {
  gcloud auth list --filter="account=\"${CLOUDSDK_CORE_ACCOUNT:?}\"" --format=json
}

cloud_context_refresh() {
  if [ "$EITR_CLOUD_PROVIDER" = gcp ]; then
    if [ -n "${CLOUDSDK_CORE_PROJECT:-}" ]; then
      gcloud projects describe "$CLOUDSDK_CORE_PROJECT" --format=json
    else
      gcloud projects list --format=json
    fi
  else
    az account list --refresh --query "[?id=='${EITR_AZURE_SUBSCRIPTION:?}']" -o json
  fi
}
