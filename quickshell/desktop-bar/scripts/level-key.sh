#!/usr/bin/env bash
# Dynamic owns its level display; every other layout retains swayosd's behavior.
set -euo pipefail
kind="${1:?level kind required}"
action="${2:?level action required}"
case "$kind:$action" in
  volume:up) osd=(--output-volume=2 --max-volume=100) ;;
  volume:down) osd=(--output-volume=-2 --max-volume=100) ;;
  volume:mute) osd=(--output-volume=mute-toggle --max-volume=100) ;;
  brightness:up) osd=(--brightness +2) ;;
  brightness:down) osd=(--brightness -2) ;;
  *) exit 2 ;;
esac
config_root="${XDG_CONFIG_HOME:-$HOME/.config}"
if ! jq -e '(.version // 1) == 1 and .layout == "dynamic"' "$config_root/quickshell/desktop-bar/bar-settings.json" >/dev/null 2>&1 \
    || jq -e '.enabled == true' "$config_root/eitr/focus.json" >/dev/null 2>&1; then
  exec swayosd-client "${osd[@]}"
fi
if [[ "$kind" == volume ]]; then
  case "$action" in
    up) wpctl set-volume --limit 1 @DEFAULT_AUDIO_SINK@ 2%+ ;;
    down) wpctl set-volume --limit 1 @DEFAULT_AUDIO_SINK@ 2%- ;;
    mute) wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle ;;
  esac
  level=null
else
  # Match swayosd's backlight path, excluding keyboard LEDs. No per-key Python.
  step=+2%
  [[ "$action" == down ]] && step=2%-
  result="$(brightnessctl --class=backlight --min-value=1 --machine-readable set "$step")"
  IFS=, read -r _device _class _current percentage _maximum <<< "$result"
  level="${percentage%\%}"
  [[ "$level" =~ ^[0-9]+$ ]] || exit 1
fi
[[ -n "${XDG_RUNTIME_DIR:-}" ]] || exit 0
umask 077
# Serialize the short publication only; atomic replacement is observed on every bar.
exec 9>"$XDG_RUNTIME_DIR/eitr-level-moment.lock"
flock -x 9
moment_file="$(mktemp "$XDG_RUNTIME_DIR/eitr-level-moment.XXXXXX")"
trap 'rm -f "$moment_file"' EXIT
printf '{"kind":"%s","level":%s,"at":%s}\n' "$kind" "$level" "$(date +%s%3N)" >"$moment_file"
mv -f "$moment_file" "$XDG_RUNTIME_DIR/eitr-level-moment.json"
