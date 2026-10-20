#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_iam_user() {
  local users chosen

  if ! users="$(aws_cli iam list-users | jq -r '.Users[].UserName')"; then
    notify-send "IAM" "Failed to list users"
    return 1
  fi

  [ -z "$users" ] && notify-send "IAM" "No users found" && return 1
  chosen="$(printf "%s\n" "$users" | walker_menu "IAM User")"
  [ -z "$chosen" ] && return 1
  echo "$chosen"
}

options="󰀄  Account summary
󰀄  Users
󰌾  Roles
󰒃  Policies
󰘦  Groups
󰌆  User access keys"

chosen="$(printf '%s\n' "$options" | walker_menu "IAM - $AWS_PROFILE")"

case "$chosen" in
  "󰀄  Account summary")
    run_in_kitty "IAM Summary - $AWS_PROFILE" "
cloud_header 'IAM account summary'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) iam get-account-summary \
| jq -r '.SummaryMap | to_entries[] | \"\u001b[36m\(.key)\u001b[0m  \(.value)\"'
" close-on-key toggle
    ;;
  "󰀄  Users")
    run_in_kitty "IAM Users - $AWS_PROFILE" "
cloud_header 'IAM users'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) iam list-users \
| jq -r '.Users[] | \"\u001b[36m\(.UserName)\u001b[0m  id=\(.UserId)  created=\(.CreateDate)  path=\(.Path)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰌾  Roles")
    run_in_kitty "IAM Roles - $AWS_PROFILE" "
cloud_header 'IAM roles'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) iam list-roles \
| jq -r '.Roles[] | \"\u001b[36m\(.RoleName)\u001b[0m  id=\(.RoleId)  created=\(.CreateDate)  path=\(.Path)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰒃  Policies")
    run_in_kitty "IAM Policies - $AWS_PROFILE" "
cloud_header 'IAM customer managed policies'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) iam list-policies --scope Local \
| jq -r '.Policies[] | \"\u001b[36m\(.PolicyName)\u001b[0m  arn=\(.Arn)  attachments=\(.AttachmentCount)  updated=\(.UpdateDate)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰘦  Groups")
    run_in_kitty "IAM Groups - $AWS_PROFILE" "
cloud_header 'IAM groups'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) iam list-groups \
| jq -r '.Groups[] | \"\u001b[36m\(.GroupName)\u001b[0m  id=\(.GroupId)  created=\(.CreateDate)  path=\(.Path)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰌆  User access keys")
    user="$(choose_iam_user)" || exit 0
    quoted_user="$(shell_quote "$user")"

    run_in_kitty "IAM Access Keys - $AWS_PROFILE" "
cloud_header 'IAM access keys'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'User' $quoted_user
echo

$(aws_base) iam list-access-keys --user-name $quoted_user \
| jq -r '.AccessKeyMetadata[] | \"\u001b[36m\(.AccessKeyId)\u001b[0m  status=\(.Status)  created=\(.CreateDate)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
