#!/usr/bin/env bash
# Opt-in Snapper snapshot boot entries for GRUB or Limine. This changes boot
# configuration, so it always asks first and never runs unattended.
#   setup.sh          detect, confirm, install packages, configure (fails if unsupported)
#   setup.sh --offer  the same, but an unsupported boot loader is only reported
#   setup.sh --check  report the detected boot loader and planned packages only
set -euo pipefail
i18n_library="${EITR_LIBRARY_ROOT:-${EITR_CODE_ROOT:-/usr/share/eitr}/lib}/i18n.sh"
[[ -f "$i18n_library" ]] || i18n_library="${EITR_CODE_ROOT:-/usr/share/eitr}/distro/lib/i18n.sh"
# shellcheck source=distro/lib/i18n.sh
source "$i18n_library"

bootloader_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
helper="${EITR_SYSTEM_HELPER:-}"
if [[ -z "$helper" ]]; then
  # Packaged location first, then the older manual install path.
  for helper in /usr/lib/eitr/eitr-system /usr/local/lib/eitr/eitr-system; do
    [[ -x "$helper" ]] && break
  done
fi
mode="${1:-}"

die() { printf '%s\n' "$*" >&2; exit 1; }
manifest() { [[ -f "$1" ]] && sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$1"; return 0; }

case "$mode" in
  ''|--offer|--check) ;;
  *) printf 'Usage: %s [--offer|--check]\n' "$0" >&2; exit 2 ;;
esac
# Never sudo a user-writable copy of the helper; use the installed root-owned one.
[[ -x "$helper" ]] || die "Install the root-owned helper first: $helper (see distro/README.md)."

# The EFI partition is usually root-only, so detection runs through sudo.
loader="$(sudo "$helper" bootloader-detect)"
case "$loader" in
  grub|limine) ;;
  *)
    sudo "$helper" snapshots-boot-status || true
    [[ "$mode" == --offer || "$mode" == --check ]] && exit 0
    exit 1
    ;;
esac

mapfile -t official < <(manifest "$bootloader_dir/$loader.txt")
mapfile -t aur < <(manifest "$bootloader_dir/$loader-aur.txt")
printf 'Detected boot loader: %s\n' "$loader"
printf 'Packages: %s\n' "${official[*]} ${aur[*]}"
[[ "$mode" == --check ]] && exit 0

case "${EITR_BOOT_SNAPSHOTS:-}" in
  yes) ;;
  no) printf 'Skipped snapshot boot entries (EITR_BOOT_SNAPSHOTS=no).\n'; exit 0 ;;
  *)
    if [[ ! -t 0 ]]; then
      eitr_gettext 'Snapshot boot entries were not configured (no terminal to confirm).'; printf '\n'
      printf 'Run later: bash %s\n' "$bootloader_dir/setup.sh"
      exit 0
    fi
    printf 'This installs the packages above and adds read-only snapshot entries to the %s menu.\n' "$loader"
    eitr_gettext 'Your current boot entries stay; the boot menu file is backed up first. See distro/RECOVERY.md.'; printf '\n'
    read -r -p "$(eitr_gettext 'Type yes to continue (anything else skips): ')" answer
    [[ "$answer" == yes ]] || { eitr_gettext 'Skipped snapshot boot entries.'; printf '\n'; exit 0; }
    ;;
esac

(( ${#official[@]} == 0 )) || sudo pacman -S --needed -- "${official[@]}"
if (( ${#aur[@]} )); then
  command -v yay >/dev/null || die 'yay is required for the AUR packages above.'
  MAKEPKG_CONF="$bootloader_dir/../makepkg.conf" yay -S --needed -- "${aur[@]}"
fi
sudo "$helper" snapshots-boot-setup
