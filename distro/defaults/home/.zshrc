source /usr/share/eitr/home/.zshrc
# An if statement, unlike [[ ]] &&, leaves a successful status when the file is absent.
if [[ -f "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh" ]]; then
  source "${XDG_CONFIG_HOME:-$HOME/.config}/eitr/shell.local.zsh"
fi
