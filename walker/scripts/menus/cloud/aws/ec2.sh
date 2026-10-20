#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

[ -z "$AWS_PROFILE" ] && exit 0

options="󰍹  Instances
󰒋  Security groups
󰋊  Volumes
󰓦  Elastic IPs
󰅟  Instance status checks"

chosen="$(printf '%s\n' "$options" | walker_menu "EC2 - $AWS_PROFILE")"

case "$chosen" in
  "󰍹  Instances")
    run_in_kitty "EC2 Instances - $AWS_PROFILE" "
cloud_header 'EC2 instances'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-instances \
| jq -r '.Reservations[].Instances[] | \"\u001b[36m\((.Tags // [] | map(select(.Key == \"Name\"))[0].Value) // \"<no-name>\")\u001b[0m  id=\(.InstanceId)  state=\(.State.Name)  type=\(.InstanceType)  private=\(.PrivateIpAddress // \"N/A\")  public=\(.PublicIpAddress // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰒋  Security groups")
    run_in_kitty "EC2 Security Groups - $AWS_PROFILE" "
cloud_header 'EC2 security groups'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-security-groups \
| jq -r '.SecurityGroups[] | \"\u001b[36m\(.GroupName)\u001b[0m  id=\(.GroupId)  vpc=\(.VpcId // \"classic\")  inbound=\(.IpPermissions | length)  outbound=\(.IpPermissionsEgress | length)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰋊  Volumes")
    run_in_kitty "EC2 Volumes - $AWS_PROFILE" "
cloud_header 'EC2 volumes'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-volumes \
| jq -r '.Volumes[] | \"\u001b[36m\(.VolumeId)\u001b[0m  state=\(.State)  size=\(.Size)GiB  type=\(.VolumeType)  attached=\([.Attachments[].InstanceId] | join(\",\"))\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰓦  Elastic IPs")
    run_in_kitty "EC2 Elastic IPs - $AWS_PROFILE" "
cloud_header 'EC2 Elastic IPs'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-addresses \
| jq -r '.Addresses[] | \"\u001b[36m\(.PublicIp)\u001b[0m  allocation=\(.AllocationId // \"N/A\")  instance=\(.InstanceId // \"N/A\")  private=\(.PrivateIpAddress // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰅟  Instance status checks")
    run_in_kitty "EC2 Status - $AWS_PROFILE" "
cloud_header 'EC2 instance status checks'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) ec2 describe-instance-status --include-all-instances \
| jq -r '.InstanceStatuses[] | \"\u001b[36m\(.InstanceId)\u001b[0m  state=\(.InstanceState.Name)  system=\(.SystemStatus.Status)  instance=\(.InstanceStatus.Status)  az=\(.AvailabilityZone)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
