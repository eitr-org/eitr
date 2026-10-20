#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

options="$(cat <<'EOF'
  Tmux basics
  tmux new -s work           Create a named session
  tmux attach -t work        Attach to a session
  tmux ls                    List sessions
  tmux kill-session -t work  Kill a session
  tmux rename-session -t old new  Rename a session
  tmux source-file ~/.config/tmux/tmux.conf Reload config from shell
󰌌  Prefix keys
  Ctrl-b                     Default tmux prefix
  Ctrl-b d                   Detach session
  Ctrl-b r                   Reload tmux config
  Ctrl-b ?                   Show all keybindings
  Ctrl-b :                   Open tmux command prompt
  Ctrl-b [                   Copy/scroll mode
  q                          Exit copy/scroll mode
󰓩  Windows
  Ctrl-b c                   New window
  Ctrl-b ,                   Rename window
  Ctrl-b &                   Close window
  Ctrl-b n                   Next window
  Ctrl-b p                   Previous window
  Ctrl-b 1                   Go to window 1
  Ctrl-b w                   Window/session picker
  Ctrl-b f                   Find window by name
󰖲  Panes
  Ctrl-b |                   Split right in current directory
  Ctrl-b -                   Split below in current directory
  Ctrl-b %                   Split right
  Ctrl-b "                   Split below
  Ctrl-b x                   Close pane
  Ctrl-b z                   Zoom current pane
  Ctrl-b o                   Next pane
  Ctrl-b ;                   Previous active pane
  Ctrl-b Space               Change pane layout
󰁔  Pane movement
  Ctrl-b h                   Move to left pane
  Ctrl-b j                   Move to lower pane
  Ctrl-b k                   Move to upper pane
  Ctrl-b l                   Move to right pane
  Ctrl-b arrows              Move between panes
  Ctrl-b {                   Move pane left
  Ctrl-b }                   Move pane right
󰩨  Pane resizing
  Ctrl-b H                   Resize pane left
  Ctrl-b J                   Resize pane down
  Ctrl-b K                   Resize pane up
  Ctrl-b L                   Resize pane right
  Ctrl-b Ctrl-arrows         Resize pane
  Ctrl-b Alt-1               Even horizontal layout
  Ctrl-b Alt-2               Even vertical layout
󰅇  Copy and paste
  Ctrl-b [                   Enter copy mode
  Space                      Start selection in copy mode
  Enter                      Copy selection
  Ctrl-b ]                   Paste tmux buffer
  tmux list-buffers          List tmux paste buffers
  tmux show-buffer           Show latest tmux buffer
  Useful workflows
  tmux new -s work           Start project session
  tmux attach                Attach to latest session
  tmux detach-client         Detach current client
  tmux switch-client -t work  Switch attached client
  tmux new-window -n logs    Create named window
  tmux capture-pane -p       Print current pane contents
  tmux kill-server           Stop all tmux sessions
EOF
)"

chosen="$(
  echo -e "$options" |
    "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --matching=contains --cache-file /dev/null --width 860 --height 720 --prompt="Tmux Commands"
)"

copy_command() {
  local command_text

  command_text="$(printf '%s' "$chosen" | sed -E 's/^  //; s/[[:space:]]{2,}.*$//')"

  if [[ -n "$command_text" ]]; then
    printf '%s' "$command_text" | wl-copy
    notify-send "Tmux command copied" "$command_text"
  fi
}

case "$chosen" in
  "" | * | 󰌌* | 󰓩* | 󰖲* | 󰁔* | 󰩨* | 󰅇* | *)
    exit 0
    ;;
  *)
    copy_command
    ;;
esac
