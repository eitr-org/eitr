#!/usr/bin/env bash
set -euo pipefail
mode="${1:-selection}"
action="${2:-edit}"
case "$mode" in selection|window|full) ;; *) exit 2 ;; esac
case "$action" in edit|copy|save|both) ;; *) exit 2 ;; esac
temp="$(mktemp --suffix=.png)"
freeze_pid=""
cleanup() {
    if [[ -n "$freeze_pid" ]]; then
        kill "$freeze_pid" 2>/dev/null || true
        wait "$freeze_pid" 2>/dev/null || true
    fi
    rm -f "$temp"
}
trap cleanup EXIT
sleep 0.2
if [[ "$mode" == full ]]; then
    monitor="$(hyprctl monitors -j | jq -r '.[] | select(.focused) | .name')"
    [[ -n "$monitor" ]] || exit 1
    grim -o "$monitor" "$temp"
else
    boxes=""
    if [[ "$mode" == window ]]; then
        monitors="$(hyprctl monitors -j)"
        boxes="$(hyprctl clients -j | jq -r --argjson monitors "$monitors" '
            .[] | select(.mapped and (.hidden | not)) |
            select(.workspace.id as $id | any($monitors[];
                .activeWorkspace.id == $id or .specialWorkspace.id == $id)) |
            "\(.at[0]),\(.at[1]) \(.size[0])x\(.size[1])"')"
        [[ -n "$boxes" ]] || { notify-send "Screenshot" "No visible windows"; exit 0; }
    fi
    hyprpicker -r -z >/dev/null 2>&1 &
    freeze_pid=$!
    sleep 0.15
    if [[ "$mode" == window ]]; then
        geometry="$(printf '%s\n' "$boxes" | slurp -r -d)" || exit 0
    else
        geometry="$(slurp -d)" || exit 0
    fi
    [[ -n "$geometry" ]] || exit 0
    grim -g "$geometry" "$temp"
    kill "$freeze_pid" 2>/dev/null || true
    wait "$freeze_pid" 2>/dev/null || true
    freeze_pid=""
fi
# The lightning flash starts only after grim has written the image, so it never appears in it.
eitr-shell desktop-bar ipc call -- realm lightning "${monitor:-}" "${geometry:-}" >/dev/null 2>&1 &
directory="$HOME/Pictures/Screenshots"
file="$directory/$(date +'%Y-%m-%d_%H-%M-%S_%N').png"
if [[ "$action" == edit ]]; then
    mkdir -p "$directory"
    "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/app-launch" satty -f "$temp" -o "$file" --copy-command "wl-copy --type image/png" \
        --early-exit --actions-on-escape exit \
        --app-id dev.local.ScreenshotEditor --title "Screenshot" \
        --notification-thumbnail screenshot --disable-notifications
    if [[ -f "$file" ]]; then
        python3 "${EITR_CODE_ROOT:-/usr/share/eitr}/quickshell/desktop-bar/scripts/obs-control.py" notify-screenshot "$file" &
    fi
else
    if [[ "$action" == save || "$action" == both ]]; then
        mkdir -p "$directory"
        cp "$temp" "$file"
    fi
    if [[ "$action" == copy || "$action" == both ]]; then
        wl-copy --type image/png < "$temp"
    fi
    case "$action" in
        copy) notify-send "Screenshot copied" "Ready to paste" ;;
        save|both) python3 "${EITR_CODE_ROOT:-/usr/share/eitr}/quickshell/desktop-bar/scripts/obs-control.py" notify-screenshot "$file" "$action" & ;;
    esac
fi
