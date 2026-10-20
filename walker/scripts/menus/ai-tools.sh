#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

WALKER_DMENU="$EITR_CODE_ROOT/walker/bin/walker-dmenu"

case "${1:-}" in
  codex-new)
    chosen="  Codex > New"
    ;;
  codex-resume-picker)
    chosen="  Codex > Resume Picker"
    ;;
  codex-resume-name)
    chosen="  Codex > Resume by Name or ID"
    ;;
  claude-new)
    chosen="󰚩  Claude Code > New"
    ;;
  claude-new-named)
    chosen="󰚩  Claude Code > New Named"
    ;;
  claude-resume-picker)
    chosen="󰚩  Claude Code > Resume Picker"
    ;;
  claude-resume-name)
    chosen="󰚩  Claude Code > Resume by Name"
    ;;
  copilot-new)
    chosen="GitHub Copilot CLI > New"
    ;;
  agy-new)
    chosen="Antigravity CLI > New"
    ;;
  gemini-new)
    chosen="Gemini CLI > New"
    ;;
  grok-new)
    chosen="Grok Build > New"
    ;;
  *)
    exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:ai-tools
    ;;
esac

[[ -z "$chosen" ]] && exit 0

# Back at the top of the folder picker returns to this assistant's menu.
case "${1:-}" in
  agy-*|claude-*|codex-*|gemini-*|grok-*|copilot-*) parent="menus:ai-${1%%-*}" ;;
  *) parent="" ;;
esac
status=0
repo_path="$("$EITR_CODE_ROOT/walker/scripts/menus/choose-folder.sh" "AI project" "")" || status=$?
if [ "$status" -eq 2 ] && [ -n "$parent" ]; then
  exec "$EITR_CODE_ROOT/walker/bin/walker" --provider "$parent"
fi
[ "$status" -eq 0 ] || exit 0

prompt_text() {
  local prompt="$1"

  printf "" |
    "$WALKER_DMENU" --dmenu --no-sort --cache-file /dev/null --prompt="$prompt"
}

case "$chosen" in
  "  Codex > New")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'codex; exec zsh'
    ;;
  "  Codex > Resume Picker")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'codex resume; exec zsh'
    ;;
  "  Codex > Resume by Name or ID")
    session_name="$(prompt_text "Codex Session Name or ID")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'codex resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "󰚩  Claude Code > New")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'claude; exec zsh'
    ;;
  "󰚩  Claude Code > New Named")
    session_name="$(prompt_text "Claude Session Name")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'claude -n "$AI_SESSION_NAME"; exec zsh'
    ;;
  "󰚩  Claude Code > Resume Picker")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'claude -r; exec zsh'
    ;;
  "󰚩  Claude Code > Resume by Name")
    session_name="$(prompt_text "Claude Session Name")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'claude -r "$AI_SESSION_NAME"; exec zsh'
    ;;
  "GitHub Copilot CLI > New")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'copilot; exec zsh'
    ;;
  "Antigravity CLI > New")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'agy; exec zsh'
    ;;
  "Gemini CLI > New")
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'gemini; exec zsh'
    ;;
  "Grok Build > New")
    # The xAI installer puts grok in ~/.grok/bin, which login shells may not list yet.
    EITR_TERMINAL_STYLE=window kitty --directory "$repo_path" zsh -ic 'PATH="$HOME/.grok/bin:$PATH" grok; exec zsh'
    ;;
  *)
    exit 0
    ;;
esac
