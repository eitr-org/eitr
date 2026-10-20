#!/usr/bin/env bash
# One-time step before installing eitr-desktop on a desktop set up before the
# package layout. pacman refuses to install over files that no package owns,
# and two kinds can exist from earlier setups: login designs copied to
# /usr/share/sddm/themes/desktop-lockscreen-* by the old login installer, and a
# network helper installed by hand at /usr/lib/eitr/eitr-network. --check only
# reports. --apply archives exactly those unowned files, then removes them so the
# package can install its own. The selected login design
# (/etc/sddm.conf.d/90-desktop-lockscreen.conf) is kept, and SDDM is never
# restarted. Review this script before running it with sudo.
set -euo pipefail

themes=/usr/share/sddm/themes
helpers=(/usr/lib/eitr/eitr-network)
backups=/var/lib/eitr/unowned-file-backups
mode="${1:-}"
[[ "$mode" == --check || "$mode" == --apply ]] || { printf 'Usage: %s --check|--apply\n' "$0" >&2; exit 2; }
[[ $mode == --check || ${EUID} -eq 0 ]] || { printf 'Run --apply as root.\n' >&2; exit 1; }

owned() { pacman -Qoq -- "$1" >/dev/null 2>&1; }

unowned=()
shopt -s nullglob
for directory in "$themes"/desktop-lockscreen-*; do
  [[ -d "$directory" && ! -L "$directory" ]] || { printf 'Skipping non-directory %s\n' "$directory" >&2; continue; }
  found_owned=false
  while IFS= read -r -d '' file; do
    if owned "$file"; then found_owned=true; break; fi
  done < <(find "$directory" -type f -print0)
  if [[ $found_owned == true ]]; then
    printf 'Owned by a package already, left alone: %s\n' "$directory"
  else
    unowned+=("$directory")
  fi
done
for helper in "${helpers[@]}"; do
  if [[ -f "$helper" && ! -L "$helper" ]] && ! owned "$helper"; then
    unowned+=("$helper")
  fi
done

if ((${#unowned[@]} == 0)); then
  printf 'No unowned files; the package can be installed directly.\n'
  exit 0
fi
printf 'Unowned files from earlier setups:\n'
printf '  %s\n' "${unowned[@]}"
if [[ $mode == --check ]]; then
  printf 'Run with --apply (as root) to archive and remove them before installing eitr-desktop.\n'
  exit 0
fi

install -d -m 700 "$backups"
archive="$backups/$(date +%Y%m%d-%H%M%S).tar"
tar -C / -cf "$archive" "${unowned[@]#/}"
chmod 600 "$archive"
rm -rf -- "${unowned[@]}"
printf 'Archived to %s and removed. Now install eitr-desktop, then run as the desktop user:\n' "$archive"
printf '  sudo /usr/bin/python3 -I /usr/share/eitr/quickshell/lockscreen/scripts/install-login.py\n'
printf 'To undo before installing: sudo tar -C / -xf %s\n' "$archive"
