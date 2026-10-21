#!/usr/bin/env bash

source "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/common.sh"

AWS_MENUS_DIR="$CLOUD_MENUS_DIR/aws"
CLOUD_PROVIDER_HELPERS="$AWS_MENUS_DIR/terminal-helpers.sh"

# Empty lets the AWS CLI use the profile's configured region.
AWS_REGION="${EITR_AWS_REGION:-${AWS_REGION:-}}"

now_ms() {
  date +%s%3N
}

minutes_ago_ms() {
  date -d "$1 minutes ago" +%s%3N
}

aws_region_args() {
  if [ -n "$AWS_REGION" ]; then
    printf -- '--region %q' "$AWS_REGION"
  fi
}

# Command prefix embedded into generated terminal scripts.
aws_base() {
  printf 'aws --profile %q %s' "$AWS_PROFILE" "$(aws_region_args)"
}

aws_cli() {
  if [ -n "$AWS_REGION" ]; then
    aws --profile "$AWS_PROFILE" --region "$AWS_REGION" "$@"
  else
    aws --profile "$AWS_PROFILE" "$@"
  fi
}

cloud_terminal_env() {
  printf 'export AWS_PROFILE=%q\n' "$AWS_PROFILE"
  if [ -n "$AWS_REGION" ]; then
    printf 'export AWS_REGION=%q\n' "$AWS_REGION"
  fi
}

back_to_aws_menu() {
  "$AWS_MENUS_DIR/menu.sh" "$AWS_PROFILE"
}

# Friendly mappings restrict and label the config-backed AWS account list.
aws_profile_choices() {
  EITR_AWS_PROFILES="${EITR_AWS_PROFILES:-}" python3 "$CLOUD_MENUS_DIR/accounts.py" aws-choices 2>/dev/null
}
