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

# Profile choices as "Label<TAB>profile" lines. EITR_AWS_PROFILES in cloud.env
# maps friendly labels ("Development=my-dev Production=my-prod"); otherwise
# every AWS CLI profile is listed under its name from Cloud > AWS > Add AWS
# Account or Ctrl+R, else its profile name.
aws_profile_choices() {
  local entry

  if [ -n "${EITR_AWS_PROFILES:-}" ]; then
    for entry in $EITR_AWS_PROFILES; do
      if [[ "$entry" == *=* ]]; then
        printf '%s\t%s\n' "${entry%%=*}" "${entry#*=}"
      else
        printf '%s\t%s\n' "$entry" "$entry"
      fi
    done
  elif command -v aws >/dev/null 2>&1; then
    python3 "$CLOUD_MENUS_DIR/accounts.py" aws-choices 2>/dev/null
  fi
}
