#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "$AWS_PROFILE" ]; then
  exit 0
fi

choose_s3_bucket() {
  local buckets
  local chosen

  if ! buckets="$(aws_cli s3api list-buckets | jq -r '.Buckets[].Name')"; then
    notify-send "S3" "Failed to list buckets for $AWS_PROFILE"
    return 1
  fi

  if [ -z "$buckets" ]; then
    notify-send "S3" "No buckets found for $AWS_PROFILE"
    return 1
  fi

  chosen="$(printf "%s\n" "$buckets" | walker_menu "S3 Bucket")"

  if [ -z "$chosen" ]; then
    return 1
  fi

  echo "$chosen"
}

options="󰉋  List buckets
󰉋  Browse bucket
  Search bucket by name"

chosen="$(printf '%s\n' "$options" | walker_menu "S3 - $AWS_PROFILE")"

case "$chosen" in
  "󰉋  List buckets")
    run_in_kitty "S3 Buckets - $AWS_PROFILE" "
cloud_header 'S3 buckets'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) s3 ls \
| awk '{print \"\033[90m\" \$1 \" \" \$2 \"\033[0m  \033[36m\" \$3 \"\033[0m\"}' \
| cloud_fzf 'Buckets' plain
" close-on-success toggle
    ;;

  "󰉋  Browse bucket")
    bucket="$(choose_s3_bucket)" || exit 0
    quoted_bucket="$(shell_quote "$bucket")"

    run_in_kitty "S3 Browse - $AWS_PROFILE" "
cloud_header 'S3 bucket objects'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Bucket' $quoted_bucket
echo

$(aws_base) s3api list-objects-v2 \
  --bucket $quoted_bucket \
  --max-items 300 \
| jq -r '
  if (.Contents | length) == 0 then
    \"No objects found.\"
  else
    .Contents[]
    | \"\u001b[90m\(.LastModified)\u001b[0m  \u001b[36m\(.Key)\u001b[0m  size=\(.Size)\"
  end
' \
| cloud_fzf 'Objects'
" close-on-success toggle
    ;;

  "  Search bucket by name")
    word="$(ask_search_word)"

    if [ -z "$word" ]; then
      exit 0
    fi

    quoted_word="$(shell_quote "$word")"

    run_in_kitty "S3 Search - $AWS_PROFILE" "
cloud_header 'S3 bucket search'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Search' $quoted_word
echo

$(aws_base) s3 ls \
| grep -i -- $quoted_word \
| awk '{print \"\033[90m\" \$1 \" \" \$2 \"\033[0m  \033[36m\" \$3 \"\033[0m\"}' \
| cloud_fzf 'Buckets' plain
" close-on-success toggle
    ;;

  "")
    exit 0
    ;;
esac
