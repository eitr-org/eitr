#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi
# Selecting a reference copies it; this menu never executes herdr commands.
options="$(cat <<'EOF'
  Sessions
  herdr                      Open or attach to the default session
  herdr --session work       Open a named session
  herdr session list         List sessions
  herdr session attach work  Attach to a running session
  herdr server stop          End the session and its panes
  herdr update               Update herdr
󰌌  Prefix and help
  Ctrl-b                     Prefix; release before the next key
  Ctrl-b ?                   Show herdr shortcuts
  Ctrl-b s                   Settings
  Ctrl-b q                   Detach (agents keep running)
󰓩  Workspaces and tabs
  Ctrl-b N                   New workspace
  Ctrl-b G                   New Git worktree workspace
  Ctrl-b W                   Rename workspace
  Ctrl-b D                   Close workspace
  Ctrl-b w                   Workspace navigation
  Ctrl-b g                   Session navigator
  Ctrl-b c                   New tab
  Ctrl-b n                   Next tab
  Ctrl-b p                   Previous tab
  Ctrl-b 1-9                 Switch to tab 1-9
󰖲  Panes
  Ctrl-b v                   Split side by side
  Ctrl-b -                   Split stacked
  Ctrl-b h/j/k/l             Focus left/down/up/right
  Ctrl-b Tab                 Next pane
  Ctrl-b z                   Zoom/restore pane
  Ctrl-b r                   Resize mode
  Ctrl-b [                   Copy mode
  Ctrl-b e                   Edit scrollback in $EDITOR
  Ctrl-b b                   Show/hide sidebar
  Ctrl-b x                   Close pane
󱚝  Agents
  claude                     Run Claude Code in any pane; herdr detects it
  codex                      Run Codex in any pane; herdr detects it
  herdr agent list           List the agents herdr sees
  herdr agent start review --kind claude --pane ID  Start an agent in a pane
EOF
)"

chosen="$(printf '%s\n' "$options" |
  "$EITR_CODE_ROOT/walker/bin/walker-dmenu" --dmenu --no-sort --matching=contains \
    --cache-file /dev/null --width 860 --height 720 --prompt="Herdr Commands")"
[[ "$chosen" == '  '* ]] || exit 0
command_text="$(printf '%s' "$chosen" | sed -E 's/^  //; s/[[:space:]]{2,}.*$//')"
[[ -n "$command_text" ]] || exit 0
printf '%s' "$command_text" | wl-copy
notify-send "Herdr command copied" "$command_text"
