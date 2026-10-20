#!/usr/bin/env bash

set -u
i18n_library="${EITR_LIBRARY_ROOT:-${EITR_CODE_ROOT:-/usr/share/eitr}/lib}/i18n.sh"
[[ -f "$i18n_library" ]] || i18n_library="${EITR_CODE_ROOT:-/usr/share/eitr}/distro/lib/i18n.sh"
# shellcheck source=distro/lib/i18n.sh
source "$i18n_library"

section() {
  printf '\n\033[1;36m%s\033[0m\n' "$1"
}

size_of() {
  du -sh "$@" 2>/dev/null | sort -hr || true
}

confirm() {
  local prompt="$1"
  local answer

  printf "%s [y/N] " "$prompt"
  read -r answer

  case "$answer" in
    y | Y | yes | YES)
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

run_if_available() {
  local command_name="$1"

  shift

  if command -v "$command_name" >/dev/null 2>&1; then
    "$@"
  else
    eitr_gettext 'Skipping {command}: command not found' "command=$command_name"; printf '\n'
  fi
}

section "$(eitr_gettext 'Current Disk Usage')"
df -h /

section "$(eitr_gettext 'Cache Sizes')"
size_of \
  "$HOME/.cache/yay" \
  /var/cache/pacman/pkg \
  "$HOME/.cache/yarn" \
  "$HOME/.npm" \
  "$HOME/.cache/go-build" \
  "$HOME/go/pkg/mod" \
  "$HOME/.local/share/pnpm/store" \
  "$HOME/.cache/pnpm" \
  "$HOME/.cache/JetBrains" \
  "$HOME/.cache/google-chrome"

section "$(eitr_gettext 'Cleanup')"

if confirm "$(eitr_gettext 'Clean yay/AUR build cache?')"; then
  run_if_available yay yay -Sc
fi

if confirm "$(eitr_gettext 'Clean old pacman package cache?')"; then
  run_if_available paccache sudo paccache -r
fi

if confirm "$(eitr_gettext 'Clean npm cache?')"; then
  run_if_available npm npm cache clean --force
fi

if confirm "$(eitr_gettext 'Clean yarn cache?')"; then
  run_if_available yarn yarn cache clean
fi

if confirm "$(eitr_gettext 'Prune pnpm store?')"; then
  run_if_available pnpm pnpm store prune
fi

if confirm "$(eitr_gettext 'Clean Go build/module cache?')"; then
  run_if_available go go clean -cache -modcache
fi

section "$(eitr_gettext 'Disk Usage After Cleanup')"
df -h /

printf '\n'; eitr_gettext 'Cleanup complete.'; printf '\n'
