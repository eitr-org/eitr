#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

MENUS_DIR="$EITR_CODE_ROOT/walker/scripts/menus"
ACTIONS_DIR="$EITR_CODE_ROOT/walker/scripts/actions"

if [[ "$(python3 "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/focus-mode.py" status)" == on ]]; then
  exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:shortcuts
fi

options="󰌌  Launchers
  SUPER + Enter             Open terminal
  SUPER + Ctrl + Enter      Open tmux
  SUPER + Space             Search apps
  SUPER + /                 Show shortcuts
  SUPER + Shift + /         Show LazyVim commands
  SUPER + E                 Open file manager
  SUPER + F                 Open main menu
  SUPER + F1                Toggle EITR handbook
  SUPER + ,                 Toggle control center
  SUPER + G                 Search Google
  SUPER + C                 Copy
  SUPER + X                 Cut
  SUPER + V                 Paste
  SUPER + Ctrl + V          Paste clipboard history
  SUPER + P                 Fuzzy-find files
  SUPER + Ctrl + P          Fuzzy-find text
  SUPER + D (hold)          Dictate, release to type
  SUPER + Shift + D (hold)  Voice reminders, release to send
󰖲  Windows
  SUPER + W                 Close active window
  SUPER + T                 Toggle floating and pin
  SUPER + Ctrl + F          Toggle fullscreen
  SUPER + Shift + P         Toggle pseudo tiling
  SUPER + A                 Open default AI assistant (Development)
  SUPER + R                 Toggle split direction
  SUPER + Shift + R         Rotate split direction
󰆾  Focus
  SUPER + H                 Focus left
  SUPER + J                 Focus down
  SUPER + K                 Focus up
  SUPER + L                 Focus right
󰙀  Move And Resize
  SUPER + Shift + H         Resize narrower
  SUPER + Shift + J         Resize taller
  SUPER + Shift + K         Resize shorter
  SUPER + Shift + L         Resize wider
  SUPER + Ctrl + U          Quarter-size window
  SUPER + Ctrl + H          Move window left
  SUPER + Ctrl + J          Move window down
  SUPER + Ctrl + K          Move window up
  SUPER + Ctrl + L          Move window right
󰎤  Workspaces
  SUPER + Tab               Toggle workspace overview
  SUPER + 1                 Go to workspace 1
  SUPER + 2                 Go to workspace 2
  SUPER + 3                 Go to workspace 3
  SUPER + 4                 Go to workspace 4
  SUPER + 5                 Go to workspace 5
  SUPER + 6                 Go to workspace 6
  SUPER + 7                 Go to workspace 7
  SUPER + 8                 Go to workspace 8
  SUPER + 9                 Go to workspace 9
  SUPER + 0                 Go to workspace 10
  SUPER + Shift + 1         Move window to workspace 1
  SUPER + Shift + 2         Move window to workspace 2
  SUPER + Shift + 3         Move window to workspace 3
  SUPER + Shift + 4         Move window to workspace 4
  SUPER + Shift + 5         Move window to workspace 5
  SUPER + Shift + 6         Move window to workspace 6
  SUPER + Shift + 7         Move window to workspace 7
  SUPER + Shift + 8         Move window to workspace 8
  SUPER + Shift + 9         Move window to workspace 9
  SUPER + Shift + 0         Move window to workspace 10
  SUPER + S                 Toggle special workspace
  SUPER + Shift + S         Move window to special workspace
  SUPER + Ctrl + S          Move window to workspace 1
  SUPER + Mouse Wheel Down  Next existing workspace
  SUPER + Mouse Wheel Up    Previous existing workspace
  SUPER + Alt + H           Previous existing workspace
  SUPER + Alt + L           Next existing workspace
  Capture And Desktop
  Print                     Full screenshot (floating editor)
  SUPER + Print             Frozen selection (floating editor)
  SUPER + Shift + Print     Window screenshot (floating editor)
  SUPER + Ctrl + Print      OCR text from selection
  SUPER + Alt + Print       Decode QR from selection
  SUPER + Shift + N         Next wallpaper
  SUPER + Ctrl + N          Wallpaper picker
  SUPER + Ctrl + Shift + N  Theme picker
  SUPER + Shift + Space     Toggle desktop bar
  SUPER + N                 Notification center
  SUPER + =                 Color picker
  SUPER + M                 Lock screen
  SUPER + ;                 Emoji picker
  Media And Hardware
  F8                        Play or pause media
  F9                        Next media
  Volume Up                 Raise volume
  Volume Down               Lower volume
  Volume Mute               Toggle output mute
  Mic Mute                  Toggle microphone mute
  Brightness Up             Raise brightness
  Brightness Down           Lower brightness
  Media Previous            Previous media
  Media Play/Pause          Play or pause media
  Media Next                Next media"

chosen="$(
  echo -e "$options" |
    "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --cache-file /dev/null --width 820 --height 720 --prompt="Shortcuts"
)"

# Normalize Walker's output so actions also match when indentation is trimmed.
chosen="${chosen#"${chosen%%[![:space:]]*}"}"
[[ -n "$chosen" ]] || exit 0
chosen="  $chosen"
# Let the launcher release keyboard focus before acting on the previous window.
sleep 0.15

case "$chosen" in
  "  󰌌"* | "  󰖲"* | "  󰆾"* | "  󰙀"* | "  󰎤"* | "  "* | "  "*)
    exit 0
    ;;
  "  SUPER + Enter "*)
    "$EITR_CODE_ROOT/walker/bin/menu-path/kitty" &
    ;;
  "  SUPER + Ctrl + Enter "*)
    "$EITR_CODE_ROOT/walker/bin/menu-path/kitty" -e tmux new-session -A -s main &
    ;;
  "  SUPER + Space "*)
    "$MENUS_DIR/search.sh"
    ;;
  "  SUPER + / "*)
    "$MENUS_DIR/shortcuts.sh"
    ;;
  "  SUPER + Shift + / "*)
    "$MENUS_DIR/vim.sh"
    ;;
  "  SUPER + E "*)
    "$EITR_CODE_ROOT/walker/bin/app-launch" dolphin --new-window &
    ;;
  "  SUPER + F "*)
    "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:main
    ;;
  "  SUPER + F1 "*)
    bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/handbook.sh" toggle
    ;;
  "  SUPER + , "*)
    eitr-shell desktop-bar ipc call -- controlCenter toggle
    ;;
  "  SUPER + G "*)
    "$ACTIONS_DIR/search/google.sh"
    ;;
  "  SUPER + C "*)
    wtype -M ctrl c -m ctrl
    ;;
  "  SUPER + X "*)
    wtype -M ctrl x -m ctrl
    ;;
  "  SUPER + V "*)
    wtype -M ctrl v -m ctrl
    ;;
  "  SUPER + Ctrl + V "*)
    "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:clipboard --width 850
    ;;
  "  SUPER + P "*)
    "$EITR_CODE_ROOT/walker/bin/menu-path/kitty" --class fif-terminal -e python3 "$EITR_CODE_ROOT/walker/scripts/actions/task-terminal.py" zsh -c 'source ~/.zshrc; fif' &
    ;;
  "  SUPER + Ctrl + P "*)
    "$EITR_CODE_ROOT/walker/bin/menu-path/kitty" --class fifs-terminal -e python3 "$EITR_CODE_ROOT/walker/scripts/actions/task-terminal.py" zsh -c 'source ~/.zshrc; fifs; exit 0' &
    ;;
  "  SUPER + D (hold) "*)
    notify-send --app-name=Dictation "Offline dictation" "Hold SUPER + D in a text field, speak, then release."
    ;;
  "  SUPER + Shift + D (hold) "*)
    python3 "$ACTIONS_DIR/tools/voice-command.py" typed
    ;;
  "  SUPER + W "*)
    hyprctl dispatch killactive
    ;;
  "  SUPER + T "*)
    hyprctl --batch "dispatch togglefloating; dispatch pin"
    ;;
  "  SUPER + Ctrl + F "*)
    hyprctl dispatch fullscreen
    ;;
  "  SUPER + Shift + P "*)
    hyprctl dispatch pseudo
    ;;
  "  SUPER + A "*)
    python3 "$EITR_CODE_ROOT/walker/scripts/actions/ai-assistant.py" open
    ;;
  "  SUPER + R "*)
    hyprctl dispatch layoutmsg togglesplit
    ;;
  "  SUPER + Shift + R "*)
    hyprctl dispatch layoutmsg rotatesplit
    ;;
  "  SUPER + H "*)
    hyprctl dispatch movefocus l
    ;;
  "  SUPER + J "*)
    hyprctl dispatch movefocus d
    ;;
  "  SUPER + K "*)
    hyprctl dispatch movefocus u
    ;;
  "  SUPER + L "*)
    hyprctl dispatch movefocus r
    ;;
  "  SUPER + Shift + H "*)
    hyprctl dispatch resizeactive -15 0
    ;;
  "  SUPER + Shift + J "*)
    hyprctl dispatch resizeactive 0 15
    ;;
  "  SUPER + Shift + K "*)
    hyprctl dispatch resizeactive 0 -15
    ;;
  "  SUPER + Shift + L "*)
    hyprctl dispatch resizeactive 15 0
    ;;
  "  SUPER + Ctrl + U "*)
    "$EITR_CODE_ROOT/hypr/scripts/window-quarter-size.sh"
    ;;
  "  SUPER + Ctrl + H "*)
    hyprctl dispatch movewindow l
    ;;
  "  SUPER + Ctrl + J "*)
    hyprctl dispatch movewindow d
    ;;
  "  SUPER + Ctrl + K "*)
    hyprctl dispatch movewindow u
    ;;
  "  SUPER + Ctrl + L "*)
    hyprctl dispatch movewindow r
    ;;
  "  SUPER + Tab "*)
    eitr-shell desktop-bar ipc call -- panels show overview
    ;;
  "  SUPER + 1 "*)
    hyprctl dispatch workspace 1
    ;;
  "  SUPER + 2 "*)
    hyprctl dispatch workspace 2
    ;;
  "  SUPER + 3 "*)
    hyprctl dispatch workspace 3
    ;;
  "  SUPER + 4 "*)
    hyprctl dispatch workspace 4
    ;;
  "  SUPER + 5 "*)
    hyprctl dispatch workspace 5
    ;;
  "  SUPER + 6 "*)
    hyprctl dispatch workspace 6
    ;;
  "  SUPER + 7 "*)
    hyprctl dispatch workspace 7
    ;;
  "  SUPER + 8 "*)
    hyprctl dispatch workspace 8
    ;;
  "  SUPER + 9 "*)
    hyprctl dispatch workspace 9
    ;;
  "  SUPER + 0 "*)
    hyprctl dispatch workspace 10
    ;;
  "  SUPER + Shift + 1 "*)
    hyprctl dispatch movetoworkspace 1
    ;;
  "  SUPER + Shift + 2 "*)
    hyprctl dispatch movetoworkspace 2
    ;;
  "  SUPER + Shift + 3 "*)
    hyprctl dispatch movetoworkspace 3
    ;;
  "  SUPER + Shift + 4 "*)
    hyprctl dispatch movetoworkspace 4
    ;;
  "  SUPER + Shift + 5 "*)
    hyprctl dispatch movetoworkspace 5
    ;;
  "  SUPER + Shift + 6 "*)
    hyprctl dispatch movetoworkspace 6
    ;;
  "  SUPER + Shift + 7 "*)
    hyprctl dispatch movetoworkspace 7
    ;;
  "  SUPER + Shift + 8 "*)
    hyprctl dispatch movetoworkspace 8
    ;;
  "  SUPER + Shift + 9 "*)
    hyprctl dispatch movetoworkspace 9
    ;;
  "  SUPER + Shift + 0 "*)
    hyprctl dispatch movetoworkspace 10
    ;;
  "  SUPER + Shift + S "*)
    hyprctl dispatch movetoworkspace special:magic
    ;;
  "  SUPER + Ctrl + S "*)
    hyprctl dispatch movetoworkspace 1
    ;;
  "  SUPER + S "*)
    hyprctl dispatch togglespecialworkspace magic
    ;;
  "  SUPER + Mouse Wheel Down "*)
    hyprctl dispatch workspace e+1
    ;;
  "  SUPER + Mouse Wheel Up "*)
    hyprctl dispatch workspace e-1
    ;;
  "  SUPER + Alt + H "*)
    hyprctl dispatch workspace e-1
    ;;
  "  SUPER + Alt + L "*)
    hyprctl dispatch workspace e+1
    ;;
  "  Print "*)
    "$ACTIONS_DIR/capture/screenshot-full.sh"
    ;;
  "  SUPER + Print "*)
    "$ACTIONS_DIR/capture/screenshot-selection.sh"
    ;;
  "  SUPER + Shift + Print "*)
    "$ACTIONS_DIR/capture/screenshot.sh" window edit
    ;;
  "  SUPER + Ctrl + Print "*)
    "$ACTIONS_DIR/capture/text.sh"
    ;;
  "  SUPER + Alt + Print "*)
    "$ACTIONS_DIR/capture/qr.sh"
    ;;
  "  SUPER + Shift + N "*)
    "$ACTIONS_DIR/wallpaper/next.sh"
    ;;
  "  SUPER + Ctrl + N "*)
    bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-picker.sh" wallpaper
    ;;
  "  SUPER + Ctrl + Shift + N "*)
    bash "$EITR_CODE_ROOT/quickshell/desktop-bar/scripts/appearance-picker.sh" theme
    ;;
  "  SUPER + Shift + Space "*)
    "$ACTIONS_DIR/toggle/desktop-bar.sh"
    ;;
  "  SUPER + N "*)
    eitr-shell desktop-bar ipc call -- notifications toggle
    ;;
  "  SUPER + = "*)
    hyprpicker -a
    ;;
  "  SUPER + M "*)
    "$EITR_CODE_ROOT/hypr/scripts/manual-lock.sh"
    ;;
  "  SUPER + ; "*)
    "$ACTIONS_DIR/emoji-picker.sh"
    ;;
  "  F8"* | "  Media Play/Pause"*)
    playerctl play-pause
    ;;
  "  F9"* | "  Media Next"*)
    playerctl next
    ;;
  "  Volume Up"*)
    swayosd-client --output-volume=2 --max-volume=100
    ;;
  "  Volume Down"*)
    swayosd-client --output-volume=-2 --max-volume=100
    ;;
  "  Volume Mute"*)
    swayosd-client --output-volume=mute-toggle --max-volume=100
    ;;
  "  Mic Mute"*)
    wpctl set-mute @DEFAULT_AUDIO_SOURCE@ toggle
    ;;
  "  Brightness Up"*)
    swayosd-client --brightness +2
    ;;
  "  Brightness Down"*)
    swayosd-client --brightness -2
    ;;
  "  Media Previous"*)
    playerctl previous
    ;;
esac
