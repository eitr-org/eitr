#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
# Selecting a reference copies it; this menu never executes cmux commands.
options="$(cat <<'EOF'
  Sessions
  cmux                       Open the default session
  cmux --session work        Open a named session
  cmux --headless --session work  Start a session without a UI
  cmux attach --session work  Attach to a running session
  cmux --help                Show command help
  cmux workspace --help      Show workspace command help
󰌌  Prefix and help
  Ctrl-b                     Prefix; release before the next key
  Ctrl-b Ctrl-b              Send Ctrl-b to the terminal
  Ctrl-b ?                   Show cmux shortcuts
  Ctrl-b d                   Quit locally or detach from a server
󰓩  Workspaces and screens
  Ctrl-b W                   New workspace
  Ctrl-b (                   Previous workspace
  Ctrl-b )                   Next workspace
  Ctrl-b $                   Rename workspace
  Ctrl-b c                   New screen
  Ctrl-b p                   Previous screen
  Ctrl-b n                   Next screen
  Ctrl-b 0                   Select screen 0
  Ctrl-b ,                   Rename screen
󰖲  Panes and tabs
  Ctrl-b %                   Split right
  Ctrl-b "                   Split down
  Ctrl-b t                   New terminal tab
  Ctrl-b B                   Browser URL prompt (Chrome/Chromium)
  Ctrl-b Tab                 Next tab
  Ctrl-b o                   Focus next pane
  Ctrl-b h/j/k/l             Focus left/down/up/right
  Ctrl-b z                   Maximize/restore pane
  Ctrl-b U                   Undo a layout action
󰁔  Sidebar and mouse
  Ctrl-b s                   Show/hide sidebar
  Ctrl-b S                   Focus sidebar
  Ctrl-b e                   Switch files/workspaces
  Click tabs or panes        Focus tab or pane
  Right-click pane           Open pane actions
  Shift + right-click        Use cmux menu when child owns mouse
󰩨  Closing (review first)
  Ctrl-b x                   Close active tab
  Ctrl-b X                   Close active pane
  Ctrl-b &                   Close active screen
  Ctrl-b D                   Close active workspace
  CLI examples
  cmux --session work workspace list --json  List workspace metadata
  cmux --session work workspace create --name review --json  Create workspace
EOF
)"

chosen="$(printf '%s\n' "$options" |
  "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --matching=contains \
    --cache-file /dev/null --width 860 --height 720 --prompt="Cmux Commands")"
[[ "$chosen" == '  '* ]] || exit 0
command_text="$(printf '%s' "$chosen" | sed -E 's/^  //; s/[[:space:]]{2,}.*$//')"
[[ -n "$command_text" ]] || exit 0
printf '%s' "$command_text" | wl-copy
notify-send "Cmux command copied" "$command_text"
