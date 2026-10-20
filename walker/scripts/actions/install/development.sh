#!/usr/bin/env bash
# Optional development tools, invoked only by an explicit menu selection.
set -euo pipefail
[[ ${EUID} -ne 0 ]] || { echo 'Run as your normal user.' >&2; exit 1; }
kind="${1:-}"
installer="$(mktemp)"
trap 'rm -f -- "$installer"' EXIT
installer_url() {
  python3 "$(dirname "${BASH_SOURCE[0]}")/software.py" installer "$1"
}
download_run() {
  curl --proto '=https' --tlsv1.2 -fsSL "$1" -o "$installer"
  shift
  bash "$installer" "$@"
}
# Shell profiles already load these tools (HOME_FILES/.zshrc), so installers
# must not append their own PATH lines.
node_setup() {
  export NVM_DIR="$HOME/.nvm"
  if [[ ! -s "$NVM_DIR/nvm.sh" ]]; then
    # The NVM installer refuses an NVM_DIR that does not exist yet.
    mkdir -p -- "$NVM_DIR"
    PROFILE=/dev/null download_run "$(installer_url nvm)"
  fi
  # nvm is not written for errexit/nounset; check each step explicitly.
  set +eu
  source "$NVM_DIR/nvm.sh" || exit 1
  nvm install --lts || exit 1
  nvm alias default 'lts/*' || exit 1
  nvm use default || exit 1
  set -eu
}
case "$kind" in
  node) node_setup ;;
  java)
    export SDKMAN_DIR="$HOME/.sdkman"
    if [[ ! -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]]; then
      download_run "$(installer_url sdkman)"
    fi
    lts="$(curl -fsSL "$(installer_url java-releases)" | python3 -c 'import json,sys; n=json.load(sys.stdin)["most_recent_lts"]; assert isinstance(n,int) and 8<=n<=99; print(n)')"
    set +eu
    source "$SDKMAN_DIR/bin/sdkman-init.sh" || exit 1
    sdkman_auto_answer=true
    versions="$(sdk list java)" || exit 1
    version="$(printf '%s' "$versions" | python3 -c 'import re,sys; major=sys.argv[1]; candidates=set(re.findall(r"\b"+major+r"(?:\.\d+){1,3}-oracle\b",sys.stdin.read())); assert candidates,"No Oracle JDK LTS found in SDKMAN"; print(max(candidates,key=lambda s:tuple(map(int,s.split("-")[0].split(".")))))' "$lts")" || exit 1
    sdk install java "$version" || exit 1
    sdk default java "$version" || exit 1
    sdk install maven || exit 1
    ;;
  python) UV_NO_MODIFY_PATH=1 download_run "$(installer_url uv)"; "$HOME/.local/bin/uv" python install ;;
  rust) rustup toolchain install stable; rustup default stable ;;
  rails)
    mise use --global ruby@latest
    mise exec ruby -- gem install rails
    ;;
  laravel) composer global require laravel/installer ;;
  # Bun's script installer always edits shell profiles; npm is an official
  # Bun install method that leaves them alone.
  yarn|pnpm|bun) node_setup; npm install --global "$kind" ;;
  deno) download_run "$(installer_url deno)" -y --no-modify-path ;;
  codex|gemini|copilot)
    node_setup
    if [[ "$kind" == codex ]]; then npm install --global @openai/codex;
    elif [[ "$kind" == gemini ]]; then npm install --global @google/gemini-cli;
    else npm_config_ignore_scripts=false npm install --global @github/copilot; fi
    ;;
  claude) download_run "$(installer_url claude)" ;;
  grok) download_run "$(installer_url grok)" ;;
  *) printf 'Unknown optional development tool: %s\n' "$kind" >&2; exit 2 ;;
esac
printf '\nInstalled %s. Open a new terminal to load its environment.\n' "$kind"
