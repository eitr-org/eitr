#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

choose_vpc() {
  local vpcs chosen

  if ! vpcs="$(aws_cli ec2 describe-vpcs | jq -r '.Vpcs[] | "\((.Tags // [] | map(select(.Key == \"Name\"))[0].Value) // \"<no-name>\")  \(.VpcId)"')"; then
    notify-send "VPC" "Failed to list VPCs"
    return 1
  fi

  [ -z "$vpcs" ] && notify-send "VPC" "No VPCs found" && return 1
  chosen="$(printf "%s\n" "$vpcs" | walker_menu "VPC")"
  [ -z "$chosen" ] && return 1
  echo "$chosen" | awk '{ print $NF }'
}

options="󰩠  VPCs
󰩠  Subnets
󰑓  Route tables
󰒋  Network ACLs
󰒄  VPC endpoints"

chosen="$(printf '%s\n' "$options" | walker_menu "VPC - $AWS_PROFILE")"

case "$chosen" in
  "󰩠  VPCs")
    run_in_kitty "VPCs - $AWS_PROFILE" "
cloud_header 'VPCs'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-vpcs \
| jq -r '.Vpcs[] | \"\u001b[36m\((.Tags // [] | map(select(.Key == \"Name\"))[0].Value) // \"<no-name>\")\u001b[0m  id=\(.VpcId)  cidr=\(.CidrBlock)  default=\(.IsDefault)  state=\(.State)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰩠  Subnets")
    vpc_id="$(choose_vpc)" || exit 0
    quoted_vpc_id="$(shell_quote "$vpc_id")"

    run_in_kitty "Subnets - $AWS_PROFILE" "
cloud_header 'VPC subnets'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'VPC' $quoted_vpc_id
echo

$(aws_base) ec2 describe-subnets --filters Name=vpc-id,Values=$quoted_vpc_id \
| jq -r '.Subnets[] | \"\u001b[36m\((.Tags // [] | map(select(.Key == \"Name\"))[0].Value) // \"<no-name>\")\u001b[0m  id=\(.SubnetId)  cidr=\(.CidrBlock)  az=\(.AvailabilityZone)  availableIps=\(.AvailableIpAddressCount)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰑓  Route tables")
    vpc_id="$(choose_vpc)" || exit 0
    quoted_vpc_id="$(shell_quote "$vpc_id")"

    run_in_kitty "Route Tables - $AWS_PROFILE" "
cloud_header 'VPC route tables'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'VPC' $quoted_vpc_id
echo

$(aws_base) ec2 describe-route-tables --filters Name=vpc-id,Values=$quoted_vpc_id \
| jq -r '.RouteTables[] | \"\u001b[36m\(.RouteTableId)\u001b[0m  routes=\(.Routes | length)  associations=\(.Associations | length)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰒋  Network ACLs")
    vpc_id="$(choose_vpc)" || exit 0
    quoted_vpc_id="$(shell_quote "$vpc_id")"

    run_in_kitty "Network ACLs - $AWS_PROFILE" "
cloud_header 'VPC network ACLs'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'VPC' $quoted_vpc_id
echo

$(aws_base) ec2 describe-network-acls --filters Name=vpc-id,Values=$quoted_vpc_id \
| jq -r '.NetworkAcls[] | \"\u001b[36m\(.NetworkAclId)\u001b[0m  default=\(.IsDefault)  entries=\(.Entries | length)  associations=\(.Associations | length)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰒄  VPC endpoints")
    vpc_id="$(choose_vpc)" || exit 0
    quoted_vpc_id="$(shell_quote "$vpc_id")"

    run_in_kitty "VPC Endpoints - $AWS_PROFILE" "
cloud_header 'VPC endpoints'
cloud_kv 'Profile' '$AWS_PROFILE'
cloud_kv 'VPC' $quoted_vpc_id
echo

$(aws_base) ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=$quoted_vpc_id \
| jq -r '.VpcEndpoints[] | \"\u001b[36m\(.VpcEndpointId)\u001b[0m  service=\(.ServiceName)  type=\(.VpcEndpointType)  state=\(.State)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
