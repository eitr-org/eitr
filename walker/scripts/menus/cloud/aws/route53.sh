#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_hosted_zone() {
  local zones chosen

  if ! zones="$(aws_cli route53 list-hosted-zones | jq -r '.HostedZones[] | "\(.Name)  \(.Id | split("/")[-1])"')"; then
    notify-send "Route 53" "Failed to list hosted zones"
    return 1
  fi

  [ -z "$zones" ] && notify-send "Route 53" "No hosted zones found" && return 1
  chosen="$(printf "%s\n" "$zones" | walker_menu "Hosted Zone")"
  [ -z "$chosen" ] && return 1
  echo "$chosen" | awk '{ print $NF }'
}

options="󰖟  Hosted zones
󰑓  Records
󰅟  Zone details"

chosen="$(printf '%s\n' "$options" | walker_menu "Route 53 - $AWS_PROFILE")"

case "$chosen" in
  "󰖟  Hosted zones")
    run_in_kitty "Route 53 Zones - $AWS_PROFILE" "
cloud_header 'Route 53 hosted zones'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) route53 list-hosted-zones \
| jq -r '.HostedZones[] | \"\u001b[36m\(.Name)\u001b[0m  id=\(.Id | split(\"/\")[-1])  records=\(.ResourceRecordSetCount)  private=\(.Config.PrivateZone)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰑓  Records")
    zone_id="$(choose_hosted_zone)" || exit 0
    quoted_zone_id="$(shell_quote "$zone_id")"

    run_in_kitty "Route 53 Records - $AWS_PROFILE" "
cloud_header 'Route 53 records'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Zone' $quoted_zone_id
echo

$(aws_base) route53 list-resource-record-sets --hosted-zone-id $quoted_zone_id \
| jq -r '.ResourceRecordSets[] | \"\u001b[36m\(.Name)\u001b[0m  type=\(.Type)  ttl=\(.TTL // \"alias\")  values=\([.ResourceRecords[]?.Value] | join(\",\")) alias=\(.AliasTarget.DNSName // \"\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰅟  Zone details")
    zone_id="$(choose_hosted_zone)" || exit 0
    quoted_zone_id="$(shell_quote "$zone_id")"

    run_in_kitty "Route 53 Zone - $AWS_PROFILE" "
cloud_header 'Route 53 hosted zone'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'Zone' $quoted_zone_id
echo

$(aws_base) route53 get-hosted-zone --id $quoted_zone_id | cloud_json
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
