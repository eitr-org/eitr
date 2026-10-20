#!/usr/bin/env bash
# Run the user's hook for an Eitr event: an executable file named after the
# event in ~/.config/eitr/hooks/ (for example ~/.config/eitr/hooks/theme-set).
#
#   run-hook.sh post-update KIND     after System Update or a pacman/AUR update
#   run-hook.sh theme-set THEME      after switching theme (the theme's folder name)
#   run-hook.sh battery-low PERCENT  once each time the battery drops to 15%
#   run-hook.sh post-boot            at the first login after each start
#
# A hook gets up to 60 seconds, and its output and failures go to
# ~/.local/state/eitr/hooks.log: a broken hook never breaks the action that
# called it. A file that is not executable is skipped, with a note in the log.
set -uo pipefail

event="${1:-}"
shift || true
case "$event" in
  post-update|theme-set|battery-low|post-boot) ;;
  *) echo "run-hook.sh: unknown event '$event'" >&2; exit 2 ;;
esac

config="${XDG_CONFIG_HOME:-$HOME/.config}"
[[ "$config" == /* ]] || config="$HOME/.config"
state="${XDG_STATE_HOME:-$HOME/.local/state}"
[[ "$state" == /* ]] || state="$HOME/.local/state"
hook="$config/eitr/hooks/$event"
log="$state/eitr/hooks.log"

[[ -e "$hook" ]] || exit 0
mkdir -p "${log%/*}"
# The bar asks at every start; post-boot runs once per boot.
if [[ "$event" == post-boot ]]; then
  boot_id="$(cat /proc/sys/kernel/random/boot_id 2>/dev/null || true)"
  marker="$state/eitr/hooks-last-boot"
  [[ -n "$boot_id" && "$(cat "$marker" 2>/dev/null || true)" == "$boot_id" ]] && exit 0
  printf '%s\n' "$boot_id" > "$marker"
fi
stamp="$(date '+%Y-%m-%d %H:%M:%S')"
if [[ ! -x "$hook" ]]; then
  printf '%s %s: skipped, not executable (chmod +x %s)\n' "$stamp" "$event" "$hook" >> "$log"
  exit 0
fi
printf '%s %s: running%s\n' "$stamp" "$event" "${*:+ with $*}" >> "$log"
timeout 60 "$hook" "$@" >> "$log" 2>&1
status=$?
if (( status == 124 )); then
  printf '%s %s: stopped after 60 seconds\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$event" >> "$log"
elif (( status != 0 )); then
  printf '%s %s: exited with %d\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$event" "$status" >> "$log"
fi
exit 0
