#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE" aws-cognito
fi

[ -z "$AWS_PROFILE" ] && exit 0

choose_user_pool() {
  printf '%s\n' "${EITR_PICK_choose_user_pool:?Missing resource selection}"
}

chosen="${EITR_CLOUD_ACTION:-}"

case "$chosen" in
  "󰟵  User pools")
    run_in_kitty "Cognito User Pools - $AWS_PROFILE" "
cloud_header 'Cognito user pools'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) cognito-idp list-user-pools --max-results 60 \
| jq -r '.UserPools[] | \"\u001b[36m\(.Name)\u001b[0m  id=\(.Id)  status=\(.Status // \"N/A\")  created=\(.CreationDate)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰀄  Identity pools")
    run_in_kitty "Cognito Identity Pools - $AWS_PROFILE" "
cloud_header 'Cognito identity pools'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) cognito-identity list-identity-pools --max-results 60 \
| jq -r '.IdentityPools[] | \"\u001b[36m\(.IdentityPoolName)\u001b[0m  id=\(.IdentityPoolId)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰘦  App clients")
    pool_id="$(choose_user_pool)" || exit 0
    quoted_pool_id="$(shell_quote "$pool_id")"

    run_in_kitty "Cognito App Clients - $AWS_PROFILE" "
cloud_header 'Cognito app clients'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'User pool' $quoted_pool_id
echo

$(aws_base) cognito-idp list-user-pool-clients --user-pool-id $quoted_pool_id --max-results 60 \
| jq -r '.UserPoolClients[] | \"\u001b[36m\(.ClientName)\u001b[0m  id=\(.ClientId)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰅟  User pool details")
    pool_id="$(choose_user_pool)" || exit 0
    quoted_pool_id="$(shell_quote "$pool_id")"

    run_in_kitty "Cognito User Pool - $AWS_PROFILE" "
cloud_header 'Cognito user pool details'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'User pool' $quoted_pool_id
echo

$(aws_base) cognito-idp describe-user-pool --user-pool-id $quoted_pool_id | cloud_json
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
