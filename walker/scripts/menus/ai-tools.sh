#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

export EITR_ASSISTANT_RUNNER="$EITR_CODE_ROOT/walker/scripts/actions/ai-assistant.py"

WALKER_DMENU="$EITR_CODE_ROOT/walker/bin/walker-dmenu"

case "${1:-}" in
  claude-continue-last)
    chosen="󰚩  Claude Code > Continue Last"
    ;;
  codex-continue-last)
    chosen="  Codex > Continue Last"
    ;;
  gemini-continue-last)
    chosen="Gemini CLI > Continue Last"
    ;;
  gemini-resume-picker)
    chosen="Gemini CLI > Resume Picker"
    ;;
  gemini-resume-number)
    chosen="Gemini CLI > Resume by Number"
    ;;
  grok-continue-last)
    chosen="Grok Build > Continue Last"
    ;;
  grok-resume-id)
    chosen="Grok Build > Resume by ID or Title"
    ;;
  grok-resume-picker)
    chosen="Grok Build > Resume Picker"
    ;;
  copilot-continue-last)
    chosen="GitHub Copilot CLI > Continue Last"
    ;;
  copilot-new-named)
    chosen="GitHub Copilot CLI > New Named"
    ;;
  copilot-resume-name)
    chosen="GitHub Copilot CLI > Resume by Name or ID"
    ;;
  copilot-resume-picker)
    chosen="GitHub Copilot CLI > Resume Picker"
    ;;
  agy-continue-last)
    chosen="Antigravity CLI > Continue Last"
    ;;
  agy-resume-id)
    chosen="Antigravity CLI > Resume by ID"
    ;;
  opencode-continue-last)
    chosen="OpenCode > Continue Last"
    ;;
  opencode-resume-id)
    chosen="OpenCode > Resume by ID"
    ;;
  opencode-new-named)
    chosen="OpenCode > New Named"
    ;;
  opencode-resume-picker)
    chosen="OpenCode > Resume Picker"
    ;;
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
  opencode-new)
    chosen="OpenCode > New"
    ;;
  pi-new)
    chosen="Pi > New"
    ;;
  *)
    exec "$EITR_CODE_ROOT/walker/bin/walker" --provider menus:ai-tools
    ;;
esac

[[ -z "$chosen" ]] && exit 0

# Back at the top of the folder picker returns to this assistant's menu.
case "${1:-}" in
  opencode-*|pi-*|agy-*|claude-*|codex-*|gemini-*|grok-*|copilot-*) parent="menus:ai-${1%%-*}" ;;
  *) parent="" ;;
esac
status=0
repo_path="$("$EITR_CODE_ROOT/walker/scripts/menus/choose-folder.sh" "AI project" "")" || status=$?
if [ "$status" -eq 2 ] && [ -n "$parent" ]; then
  exec "$EITR_CODE_ROOT/walker/bin/walker" --provider "$parent"
fi
[ "$status" -eq 0 ] || exit 0

if [[ -f "$EITR_LIBRARY_ROOT/i18n.sh" ]]; then source "$EITR_LIBRARY_ROOT/i18n.sh";
else source "$EITR_CODE_ROOT/distro/lib/i18n.sh"; fi

prompt_text() {
  local prompt="$1"

  printf "" |
    "$WALKER_DMENU" --dmenu --no-sort --cache-file /dev/null --prompt="$prompt"
}

case "$chosen" in
  "󰚩  Claude Code > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run claude --continue; exec zsh'
    ;;
  "  Codex > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run codex resume --last; exec zsh'
    ;;
  "Gemini CLI > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run gemini --resume latest; exec zsh'
    ;;
  "Gemini CLI > Resume Picker")
    session_name="$(cd -- "$repo_path" && python3 "$EITR_ASSISTANT_RUNNER" session-picker gemini)" || exit 0
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run gemini --resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "Gemini CLI > Resume by Number")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" resume-number gemini; exec zsh'
    ;;
  "Grok Build > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run grok --continue; exec zsh'
    ;;
  "Grok Build > Resume by ID or Title")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run grok --resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "Grok Build > Resume Picker")
    session_name="$(cd -- "$repo_path" && python3 "$EITR_ASSISTANT_RUNNER" session-picker grok)" || exit 0
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run grok --resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "GitHub Copilot CLI > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run copilot --continue; exec zsh'
    ;;
  "GitHub Copilot CLI > New Named")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run copilot --name "$AI_SESSION_NAME"; exec zsh'
    ;;
  "GitHub Copilot CLI > Resume by Name or ID")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run copilot --resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "GitHub Copilot CLI > Resume Picker")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run copilot --resume; exec zsh'
    ;;
  "Antigravity CLI > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run agy --continue; exec zsh'
    ;;
  "Antigravity CLI > Resume by ID")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run agy --conversation "$AI_SESSION_NAME"; exec zsh'
    ;;
  "OpenCode > Continue Last")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run opencode --continue; exec zsh'
    ;;
  "OpenCode > Resume by ID")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run opencode --session "$AI_SESSION_NAME"; exec zsh'
    ;;
  "OpenCode > New Named")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run opencode --session "$AI_SESSION_NAME"; exec zsh'
    ;;
  "OpenCode > Resume Picker")
    session_name="$(cd -- "$repo_path" && python3 "$EITR_ASSISTANT_RUNNER" session-picker opencode)" || exit 0
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run opencode --session "$AI_SESSION_NAME"; exec zsh'
    ;;
  "  Codex > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run codex; exec zsh'
    ;;
  "  Codex > Resume Picker")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run codex resume; exec zsh'
    ;;
  "  Codex > Resume by Name or ID")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run codex resume "$AI_SESSION_NAME"; exec zsh'
    ;;
  "󰚩  Claude Code > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run claude; exec zsh'
    ;;
  "󰚩  Claude Code > New Named")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run claude -n "$AI_SESSION_NAME"; exec zsh'
    ;;
  "󰚩  Claude Code > Resume Picker")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run claude -r; exec zsh'
    ;;
  "󰚩  Claude Code > Resume by Name")
    session_name="$(prompt_text "$(eitr_gettext 'Session name or ID')")"
    [[ -z "$session_name" ]] && exit 0
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" env AI_SESSION_NAME="$session_name" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run claude -r "$AI_SESSION_NAME"; exec zsh'
    ;;
  "GitHub Copilot CLI > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run copilot; exec zsh'
    ;;
  "Antigravity CLI > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run agy; exec zsh'
    ;;
  "Gemini CLI > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run gemini; exec zsh'
    ;;
  "Grok Build > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run grok; exec zsh'
    ;;
  "OpenCode > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run opencode; exec zsh'
    ;;
  "Pi > New")
    EITR_TERMINAL_STYLE=window "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/menu-path/kitty" --directory "$repo_path" zsh -ic 'python3 "$EITR_ASSISTANT_RUNNER" run pi; exec zsh'
    ;;
  *)
    exit 0
    ;;
esac
