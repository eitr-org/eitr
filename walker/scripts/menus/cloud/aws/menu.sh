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
  AWS_PROFILE="$(choose_aws_profile)" || exit 0
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

options="󰒋  SSO Login
󰅟  Check Auth
󰃷  CloudWatch
󰡨  ECS
󰓟  S3
  Aurora / RDS
  ECR
󰨇  Grafana
󰘦  Cognito
  DocumentDB
󰊕  Lambda
󰅧  CloudFront
󰌢  Lightsail
󰍹  EC2
󰑃  Route 53
󰖟  VPC
󰒃  IAM"

chosen="$(printf '%s\n' "$options" | walker_menu "AWS - $AWS_PROFILE")"

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

  "󰃷  CloudWatch")
    "$AWS_MENUS_DIR/cloudwatch.sh" "$AWS_PROFILE"
    ;;

  "󰡨  ECS")
    "$AWS_MENUS_DIR/ecs.sh" "$AWS_PROFILE"
    ;;

  "󰓟  S3")
    "$AWS_MENUS_DIR/s3.sh" "$AWS_PROFILE"
    ;;

  "  Aurora / RDS")
    "$AWS_MENUS_DIR/rds.sh" "$AWS_PROFILE"
    ;;

  "  ECR")
    "$AWS_MENUS_DIR/ecr.sh" "$AWS_PROFILE"
    ;;

  "󰨇  Grafana")
    "$AWS_MENUS_DIR/grafana.sh" "$AWS_PROFILE"
    ;;

  "󰘦  Cognito")
    "$AWS_MENUS_DIR/cognito.sh" "$AWS_PROFILE"
    ;;

  "  DocumentDB")
    "$AWS_MENUS_DIR/docdb.sh" "$AWS_PROFILE"
    ;;

  "󰊕  Lambda")
    "$AWS_MENUS_DIR/lambda.sh" "$AWS_PROFILE"
    ;;

  "󰅧  CloudFront")
    "$AWS_MENUS_DIR/cloudfront.sh" "$AWS_PROFILE"
    ;;

  "󰌢  Lightsail")
    "$AWS_MENUS_DIR/lightsail.sh" "$AWS_PROFILE"
    ;;

  "󰍹  EC2")
    "$AWS_MENUS_DIR/ec2.sh" "$AWS_PROFILE"
    ;;

  "󰑃  Route 53")
    "$AWS_MENUS_DIR/route53.sh" "$AWS_PROFILE"
    ;;

  "󰖟  VPC")
    "$AWS_MENUS_DIR/vpc.sh" "$AWS_PROFILE"
    ;;

  "󰒃  IAM")
    "$AWS_MENUS_DIR/iam.sh" "$AWS_PROFILE"
    ;;

  "")
    exit 0
    ;;
esac
