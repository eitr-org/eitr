#!/usr/bin/env bash
set -euo pipefail
i18n_library="${EITR_LIBRARY_ROOT:-${EITR_CODE_ROOT:-/usr/share/eitr}/lib}/i18n.sh"
[[ -f "$i18n_library" ]] || i18n_library="${EITR_CODE_ROOT:-/usr/share/eitr}/distro/lib/i18n.sh"
# shellcheck source=distro/lib/i18n.sh
source "$i18n_library"
restart_check="${EITR_CODE_ROOT:-/usr/share/eitr}/walker/scripts/actions/system/restart-check.py"
# Apps Eitr installs from Flatpak (such as GeForce NOW) live in the user's
# installation. A Flatpak failure is reported but does not undo the system update.
update_flatpaks() {
  command -v flatpak >/dev/null 2>&1 || return 0
  eitr_gettext 'Preparing Flatpak updates…' >&2; printf '\n' >&2
  [[ -n "$(flatpak list --user --app --columns=application 2>/dev/null)" ]] || return 0
  flatpak update --user --noninteractive || eitr_gettext 'Flatpak apps could not be updated; the system update itself finished.' >&2
}
# Arch announces upgrades that need a manual step on its news feed. When news
# arrived since the last upgrade, ask first; Enter cancels before anything changes.
# Automated updates (the VM tests) set EITR_SKIP_ARCH_NEWS=1.
arch_news_ok() {
  [[ "${EITR_SKIP_ARCH_NEWS:-}" == 1 ]] && return 0
  local status=0 answer=''
  eitr_gettext 'Checking Arch Linux news…' >&2; printf '\n' >&2
  python3 "${EITR_CODE_ROOT:-/usr/share/eitr}/walker/scripts/actions/system/arch-news.py" || status=$?
  (( status == 10 )) || return 0
  read -r -p "$(eitr_gettext 'Continue the update? [y/N] ')" answer || true
  [[ "$answer" =~ ^[Yy]([Ee][Ss])?$ ]]
}
cancel() { rm -f "$packages"; eitr_gettext 'Update cancelled; nothing was changed.'; printf '\n'; exit 0; }
# Only the distro's System Update path creates snapshots.
full_update() { sudo pacman -Syu; yay -Sua --devel; update_flatpaks; }
# Only a complete, successful check may skip the update. checkupdates keeps its
# sync database separate from the system database (exit 2 means no updates).
no_updates() {
  local official aur flatpaks aur_errors status=0
  eitr_gettext 'Checking official package updates…' >&2; printf '\n' >&2
  official="$(checkupdates)" || status=$?
  [[ "$status" == 0 || "$status" == 2 ]] || return 1
  [[ -z "$official" ]] || return 1
  # yay uses exit 1 for an empty update list as well as errors. Only its
  # silent empty result is a no-update result; diagnostics keep the update path.
  aur_errors="$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/eitr-update-check.XXXXXX")" || return 1
  status=0
  eitr_gettext 'Checking AUR updates…' >&2; printf '\n' >&2
  aur="$(yay -Qua --devel 2>"$aur_errors")" || status=$?
  if [[ -s "$aur_errors" ]]; then
    cat "$aur_errors" >&2
    rm -f "$aur_errors"
    return 1
  fi
  rm -f "$aur_errors"
  [[ "$status" == 0 || "$status" == 1 ]] || return 1
  [[ -z "$aur" ]] || return 1
  eitr_gettext 'Checking Flatpak updates…' >&2; printf '\n' >&2
  flatpaks="$(flatpak remote-ls --user --updates --columns=application)" || return 1
  [[ -z "$flatpaks" ]]
}
if [[ "${1:-}" == system ]] && no_updates; then
  eitr_gettext 'Everything is up to date.'
  printf '\n'
  sleep 3
  exit 0
fi
# After a successful update, offer a restart or log-out when changed packages need one.
packages="$(mktemp "${XDG_RUNTIME_DIR:-/tmp}/eitr-update-packages.XXXXXX")"
# A broken check must never block the update that would fix it; only the restart
# hint is lost then.
eitr_gettext 'Preparing the update…' >&2; printf '\n' >&2
python3 "$restart_check" snapshot "$packages" || eitr_gettext 'Could not record running packages; the update continues without a restart hint.' >&2
desktop_before="$(pacman -Q eitr-desktop 2>/dev/null || true)"
# The bar's updates icon re-checks once the update has finished; no bar running is fine.
# Elephant loads menu files only at start, so a new eitr-desktop restarts it; its
# KillMode=process keeps apps launched from menus running.
offer_restart() {
  eitr-shell desktop-bar ipc call -- updates refresh >/dev/null 2>&1 || true
  # The user's post-update hook (distro/lib/run-hook.sh); it never fails the update.
  local runner="${EITR_LIBRARY_ROOT:-${EITR_CODE_ROOT:-/usr/share/eitr}/lib}/run-hook.sh"
  [[ -f "$runner" ]] || runner="${EITR_CODE_ROOT:-/usr/share/eitr}/distro/lib/run-hook.sh"
  [[ -f "$runner" ]] && bash "$runner" post-update "$update_kind"
  if [[ "$(pacman -Q eitr-desktop 2>/dev/null || true)" != "$desktop_before" ]]; then
    systemctl --user try-restart elephant.service >/dev/null 2>&1 || true
  fi
  python3 "$restart_check" compare "$packages" || true
}
update_kind="${1:-}"
case "${1:-}" in
  system|pacman|full) arch_news_ok || cancel ;;
esac
case "${1:-}" in
  system)
    if [[ -f /etc/eitr/system-update-policy.conf ]]; then
      # Packaged helper first; /usr/local/lib holds earlier manual installs.
      helper=''
      for candidate in /usr/lib/eitr/eitr-system /usr/local/lib/eitr/eitr-system; do
        if [[ -x "$candidate" ]]; then helper="$candidate"; break; fi
      done
      [[ -n "$helper" ]] || { echo 'Distro snapshot helper is missing; update aborted.' >&2; exit 1; }
      exec 9>"${XDG_RUNTIME_DIR:-/tmp}/eitr-system-update-$UID.lock"
      flock -n 9 || { echo 'Another System Update is running.' >&2; exit 1; }
      eitr_gettext 'Creating the before-update snapshot…' >&2; printf '\n' >&2
      sudo "$helper" snapshot-pre
      # Always pair the pre snapshot, even when the upgrade fails or is declined.
      outcome=failed
      finish_snapshot() {
        eitr_gettext 'Creating the after-update snapshot…' >&2; printf '\n' >&2
        sudo "$helper" snapshot-post "$outcome"
      }
      trap finish_snapshot EXIT
      full_update
      outcome=success
      # Finish the post snapshot before a restart can be offered.
      trap - EXIT
      finish_snapshot
    else
      full_update
    fi
    offer_restart
    ;;
  pacman) sudo pacman -Syu; offer_restart ;;
  yay) yay -Sua --devel; offer_restart ;;
  # A function called in an && list would run with set -e disabled.
  full) full_update; offer_restart ;;
  *) echo 'Usage: update.sh system|pacman|yay|full' >&2; exit 2 ;;
esac
