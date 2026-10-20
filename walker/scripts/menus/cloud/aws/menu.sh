#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

# Used by the Elephant AWS and Grafana menus: "Label<TAB>profile" lines.
if [ "${1:-}" = "--list-profiles" ]; then
  aws_profile_choices
  exit 0
fi

if [ -n "${1:-}" ]; then
  AWS_PROFILE="$1"
else
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" show aws-profiles
fi

case "${2:-}" in
  --sso-login)
    run_in_kitty "AWS SSO - $AWS_PROFILE" "
cloud_header 'AWS SSO login'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_success 'Opening AWS SSO login...'
echo
$(aws_base) sso login
" close-on-success
    exit 0
    ;;
  --check-auth)
    run_in_kitty "AWS Auth - $AWS_PROFILE" "
cloud_header 'AWS auth'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_success 'Checking AWS auth...'
echo
$(aws_base) sts get-caller-identity \
| jq -r '
  \"\u001b[34mUserId:\u001b[0m  \(.UserId)\",
  \"\u001b[34mAccount:\u001b[0m \(.Account)\",
  \"\u001b[34mArn:\u001b[0m     \(.Arn)\"
'
" close-on-key toggle
    exit 0
    ;;
esac

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE"
fi

chosen="${EITR_CLOUD_ACTION:-}"

case "$chosen" in

  "󰒋  SSO Login")
    run_in_kitty "AWS SSO - $AWS_PROFILE" "
cloud_header 'AWS SSO login'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_success 'Opening AWS SSO login...'
echo
$(aws_base) sso login
" close-on-success
    ;;

  "󰅟  Check Auth")
    run_in_kitty "AWS Auth - $AWS_PROFILE" "
cloud_header 'AWS auth'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_success 'Checking AWS auth...'
echo
$(aws_base) sts get-caller-identity \
| jq -r '
  \"\u001b[34mUserId:\u001b[0m  \(.UserId)\",
  \"\u001b[34mAccount:\u001b[0m \(.Account)\",
  \"\u001b[34mArn:\u001b[0m     \(.Arn)\"
'
" close-on-key toggle
    ;;

  "")
    exit 0
    ;;
esac
