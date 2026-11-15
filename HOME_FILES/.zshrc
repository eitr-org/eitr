if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

export ZSH="$HOME/.oh-my-zsh"

ZSH_THEME="powerlevel10k/powerlevel10k"

plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

[[ ! -f ~/.p10k.zsh ]] || source ~/.p10k.zsh

[[ -f "$HOME/.dart-cli-completion/zsh-config.zsh" ]] && . "$HOME/.dart-cli-completion/zsh-config.zsh" || true

export LS_COLORS=$(cat ~/.ls_colors)

export SDKMAN_DIR="$HOME/.sdkman"
[[ -s "$HOME/.sdkman/bin/sdkman-init.sh" ]] && source "$HOME/.sdkman/bin/sdkman-init.sh"

# nvm itself loads on first use: sourcing it costs up to 0.4 s in every new shell. Its
# default Node version is on PATH from the start, so node, npm and global tools work at once.
export NVM_DIR="$HOME/.nvm"
if [[ -s "$NVM_DIR/nvm.sh" ]]; then
  _eitr_nvm_version=default
  for _eitr_nvm_hop in 1 2 3 4 5; do
    [[ -f "$NVM_DIR/alias/$_eitr_nvm_version" ]] || break
    _eitr_nvm_version=$(<"$NVM_DIR/alias/$_eitr_nvm_version")
  done
  if [[ -n "$_eitr_nvm_version" && -d "$NVM_DIR/versions/node/$_eitr_nvm_version/bin" ]]; then
    export PATH="$NVM_DIR/versions/node/$_eitr_nvm_version/bin:$PATH"
    _eitr_nvm_commands=(nvm)
  else
    _eitr_nvm_commands=(nvm node npm npx)
  fi
  _eitr_load_nvm() {
    local command
    for command in nvm node npm npx _eitr_load_nvm; do
      (( $+functions[$command] )) && unfunction $command
    done
    \. "$NVM_DIR/nvm.sh"
    [[ -s "$NVM_DIR/bash_completion" ]] && \. "$NVM_DIR/bash_completion"
  }
  for _eitr_nvm_command in $_eitr_nvm_commands; do
    eval "$_eitr_nvm_command() { _eitr_load_nvm; $_eitr_nvm_command \"\$@\"; }"
  done
  unset _eitr_nvm_version _eitr_nvm_hop _eitr_nvm_commands _eitr_nvm_command
fi

open_file() {
  local file="$1"

  case "$file" in
    *.ts|*.js|*.jsx|*.tsx|*.json|*.md|*.xml|*.java|*.go|*.py|*.sh|*.zsh|*.lua|*.css|*.html|*.yml|*.yaml|*.rs|*.rb|*.erb|*.txt)
      setsid -f "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/bin/app-launch" --terminal -e nvim "$file" >/dev/null 2>&1 < /dev/null
      ;;
    *)
      setsid -f xdg-open "$file" >/dev/null 2>&1 < /dev/null
      ;;
  esac
}

fif() {
  local file

  file=$(rg --files | fzf \
    --layout=default \
    --border \
    --info=hidden \
    --prompt='❯ '
  ) || return

  open_file "$file"

  exit 0
}

fifs() {
  local result file

  result=$(fzf --ansi \
    --layout=default \
    --border \
    --info=hidden \
    --prompt='❯ ' \
    --disabled \
    --bind "start:reload:rg --line-number --no-heading --color=always ''" \
    --bind "change:reload:rg --line-number --no-heading --color=always {q} || true" \
    --delimiter : \
    --preview 'bat --style=numbers --color=always {1} --highlight-line {2}'
  ) || return

  file=$(echo "$result" | cut -d: -f1)

  [[ -z "$file" ]] && return

  open_file "$file"

  exit 0
}

export PATH="$HOME/.local/bin:$PATH"
[[ -s "$HOME/.cargo/env" ]] && source "$HOME/.cargo/env"
[[ -d "$HOME/.bun/bin" ]] && export PATH="$HOME/.bun/bin:$PATH"
[[ -d "$HOME/.deno/bin" ]] && export PATH="$HOME/.deno/bin:$PATH"
[[ -d "$HOME/.config/composer/vendor/bin" ]] && export PATH="$HOME/.config/composer/vendor/bin:$PATH"
(( $+commands[mise] )) && eval "$(mise activate zsh)"

alias ls='eza --icons=auto --group-directories-first'
alias ll='eza -la --icons=auto --group-directories-first --git'
