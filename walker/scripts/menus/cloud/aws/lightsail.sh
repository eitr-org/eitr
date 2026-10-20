#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

AWS_PROFILE="$1"
source "$EITR_CODE_ROOT/walker/scripts/menus/cloud/aws/common.sh"

if [ -z "${EITR_CLOUD_ACTION:-}" ]; then
  exec python3 "$CLOUD_MENUS_DIR/navigation.py" select aws "$AWS_PROFILE" aws-lightsail
fi

[ -z "$AWS_PROFILE" ] && exit 0

chosen="${EITR_CLOUD_ACTION:-}"

case "$chosen" in
  "󰍹  Instances")
    run_in_kitty "Lightsail Instances - $AWS_PROFILE" "
cloud_header 'Lightsail instances'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) lightsail get-instances \
| jq -r '.instances[] | \"\u001b[36m\(.name)\u001b[0m  state=\(.state.name)  publicIp=\(.publicIpAddress // \"N/A\")  blueprint=\(.blueprintId)  bundle=\(.bundleId)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰩠  Static IPs")
    run_in_kitty "Lightsail Static IPs - $AWS_PROFILE" "
cloud_header 'Lightsail static IPs'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) lightsail get-static-ips \
| jq -r '.staticIps[] | \"\u001b[36m\(.name)\u001b[0m  ip=\(.ipAddress)  attached=\(.isAttached)  resource=\(.attachedTo // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "󰖟  Distributions")
    run_in_kitty "Lightsail Distributions - $AWS_PROFILE" "
cloud_header 'Lightsail distributions'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) lightsail get-distributions \
| jq -r '.distributions[] | \"\u001b[36m\(.name)\u001b[0m  status=\(.status)  domain=\(.domainName)  enabled=\(.isEnabled)\"' \
| cloud_report
" close-on-success toggle
    ;;
  "  Databases")
    run_in_kitty "Lightsail Databases - $AWS_PROFILE" "
cloud_header 'Lightsail databases'
cloud_kv 'Profile' '$AWS_PROFILE'
echo

$(aws_base) lightsail get-relational-databases \
| jq -r '.relationalDatabases[] | \"\u001b[36m\(.name)\u001b[0m  engine=\(.engine)  state=\(.state)  endpoint=\(.masterEndpoint.address // \"N/A\")\"' \
| cloud_report
" close-on-success toggle
    ;;
  "")
    exit 0
    ;;
esac
