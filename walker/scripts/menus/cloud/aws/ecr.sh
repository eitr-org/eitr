#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "$AWS_PROFILE" ]; then
  exit 0
fi

choose_ecr_repository() {
  local repositories
  local chosen

  if ! repositories="$(aws_cli ecr describe-repositories | jq -r '.repositories[].repositoryName')"; then
    notify-send "ECR" "Failed to list repositories for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$repositories" ]; then
    notify-send "ECR" "No repositories found for $AWS_PROFILE"
    return 1
  fi

  chosen="$(printf "%s\n" "$repositories" | walker_menu "ECR Repository")"

  if [ -z "$chosen" ]; then
    return 1
  fi

  echo "$chosen"
}

options="  List repositories
  Search repository
󰁫  Latest image tags"

chosen="$(printf '%s\n' "$options" | walker_menu "ECR - $AWS_PROFILE")"

case "$chosen" in
  "  List repositories")
    run_in_kitty "ECR Repositories - $AWS_PROFILE" "
cloud_header 'ECR repositories'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ecr describe-repositories \
| jq -r '.repositories[] | \"\u001b[36m\(.repositoryName)\u001b[0m  \u001b[90m\(.repositoryUri)\u001b[0m\"' \
| cloud_fzf 'Repositories' plain
" close-on-success toggle
    ;;

  "  Search repository")
    word="$(ask_search_word)"

    if [ -z "$word" ]; then
      exit 0
    fi

    quoted_word="$(shell_quote "$word")"

    run_in_kitty "ECR Search - $AWS_PROFILE" "
cloud_header 'ECR repository search'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Search' $quoted_word
echo

$(aws_base) ecr describe-repositories \
| jq -r '.repositories[] | \"\u001b[36m\(.repositoryName)\u001b[0m  \u001b[90m\(.repositoryUri)\u001b[0m\"' \
| grep -i -- $quoted_word \
| cloud_fzf 'Repositories' plain
" close-on-success toggle
    ;;

  "󰁫  Latest image tags")
    repo="$(choose_ecr_repository)" || exit 0

    quoted_repo="$(shell_quote "$repo")"

    run_in_kitty "ECR Images - $AWS_PROFILE" "
cloud_header 'Latest ECR images'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Repository' $quoted_repo
echo

$(aws_base) ecr describe-images \
  --repository-name $quoted_repo \
  --query 'reverse(sort_by(imageDetails,& imagePushedAt))[:20]' \
| jq -r '.[] | \"\u001b[90m\(.imagePushedAt)\u001b[0m  \u001b[36mtags=\(.imageTags // [])\u001b[0m  digest=\(.imageDigest)\"' \
| cloud_fzf 'Images' plain
" close-on-success toggle
    ;;

  "")
    exit 0
    ;;
esac
