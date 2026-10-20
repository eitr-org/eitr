#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_distribution() {
  local distributions chosen

  if ! distributions="$(aws_cli cloudfront list-distributions | jq -r '.DistributionList.Items[]? | "\(.DomainName)  \(.Id)"')"; then
    notify-send "CloudFront" "Failed to list distributions"
    return 1
  fi

  [ -z "$distributions" ] && notify-send "CloudFront" "No distributions found" && return 1
  chosen="$(printf "%s\n" "$distributions" | walker_menu "Distribution")"
  [ -z "$chosen" ] && return 1
  echo "$chosen" | awk '{ print $NF }'
}

options="󰖟  Distributions
󰅟  Distribution details
󰑓  Invalidations"

chosen="$(printf '%s\n' "$options" | walker_menu "CloudFront - $AWS_PROFILE")"

case "$chosen" in
  "󰖟  Distributions")
    run_in_kitty "CloudFront Distributions - $AWS_PROFILE" "
cloud_header 'CloudFront distributions'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) cloudfront list-distributions \
| jq -r '.DistributionList.Items[]? | \"\u001b[36m\(.DomainName)\u001b[0m  id=\(.Id)  status=\(.Status)  enabled=\(.Enabled)  aliases=\([.Aliases.Items[]?] | join(\",\"))\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰅟  Distribution details")
    distribution_id="$(choose_distribution)" || exit 0
    quoted_distribution_id="$(shell_quote "$distribution_id")"

    run_in_kitty "CloudFront Distribution - $AWS_PROFILE" "
cloud_header 'CloudFront distribution'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Distribution' $quoted_distribution_id
echo

$(aws_base) cloudfront get-distribution --id $quoted_distribution_id | cloud_json
" close-on-success toggle
    ;;
  "󰑓  Invalidations")
    distribution_id="$(choose_distribution)" || exit 0
    quoted_distribution_id="$(shell_quote "$distribution_id")"

    run_in_kitty "CloudFront Invalidations - $AWS_PROFILE" "
cloud_header 'CloudFront invalidations'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Distribution' $quoted_distribution_id
echo

$(aws_base) cloudfront list-invalidations --distribution-id $quoted_distribution_id \
| jq -r '.InvalidationList.Items[]? | \"\u001b[36m\(.Id)\u001b[0m  status=\(.Status)  created=\(.CreateTime)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
