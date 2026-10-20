#!/usr/bin/env bash
# Builds the Eitr installer ISO from committed HEAD and an offline payload made
# by distro/payload/build-payload.py from the same commit:
#   EITR_PAYLOAD=/abs/payload EITR_ISO_BUILD_ROOT=/abs/build EITR_ISO_OUTPUT_ROOT=/abs/out \
#     bash distro/build-iso.sh
# The payload is stored on the ISO filesystem beside the live image, not inside
# it, and the live system reads it from the medium (copytoram=n).
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
profile_source=/usr/share/archiso/configs/releng
build_root="${EITR_ISO_BUILD_ROOT:-$repo_root/distro/build}"
output_root="${EITR_ISO_OUTPUT_ROOT:-$repo_root/distro/out}"
payload="${EITR_PAYLOAD:-}"
if [[ "$build_root" != /* || "$output_root" != /* || "$build_root" == / || "$output_root" == / ]]; then
  printf 'Build/output directories must be explicit absolute paths, not /.\n' >&2
  exit 1
fi
if [[ "$payload" != /* || ! -f "$payload/manifest.json" ]]; then
  printf 'Set EITR_PAYLOAD to the absolute path of a payload from build-payload.py.\n' >&2
  exit 1
fi
profile="$build_root/profile"
# Public images must contain only cleared artwork (distro/ARTWORK-LICENSING.md).
if [[ "${EITR_PUBLIC_RELEASE:-}" == 1 ]]; then
  if ! python3 "$repo_root/distro/artwork-check.py" --public; then
    printf 'Artwork under review blocks a public release; see distro/ARTWORK-LICENSING.md.\n' >&2
    exit 1
  fi
  # Nor may it carry packages EITR cannot redistribute (distro/redistribution.json).
  if ! python3 "$repo_root/distro/repo/publish.py" --check-payload "$payload"; then
    exit 1
  fi
fi

if [[ ${EUID} -eq 0 ]]; then
  printf 'Run as a regular user with sudo access.\n' >&2
  exit 1
fi
if [[ ! -d "$profile_source" ]] || ! command -v mkarchiso >/dev/null || ! command -v xorriso >/dev/null; then
  printf 'Install archiso first: sudo pacman -S archiso\n' >&2
  exit 1
fi
if ! git -C "$repo_root" rev-parse --verify --quiet HEAD >/dev/null; then
  printf 'Build from a Git checkout with at least one commit.\n' >&2
  exit 1
fi
if [[ -n "$(git -C "$repo_root" status --porcelain --untracked-files=no)" ]]; then
  printf 'Warning: uncommitted changes are not included; the ISO uses committed HEAD.\n' >&2
fi
# The installer scripts and the eitr-desktop package must come from one commit.
payload_commit="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["source_commit"])' "$payload/manifest.json")"
if [[ "$payload_commit" != "$(git -C "$repo_root" rev-parse HEAD)" ]]; then
  printf 'The payload was built from %s, not HEAD; rebuild it first.\n' "$payload_commit" >&2
  exit 1
fi
if [[ -e "$build_root" ]]; then
  printf 'Build directory exists: %s (remove it manually after checking mounts).\n' "$build_root" >&2
  exit 1
fi

# Release name for the ISO file and boot menus; see distro/RELEASES.md.
IFS=$'\t' read -r release_version release_stage release_codename < <(python3 -c '
import json, sys
data = json.load(open(sys.argv[1]))
print(data["version"], data["stage"], data["codename"], sep="\t")' "$repo_root/distro/release.json")
[[ "$release_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ && "$release_stage" =~ ^[a-z]+$ && "$release_codename" =~ ^[A-Za-z]+$ ]] ||
  { printf 'Invalid distro/release.json\n' >&2; exit 1; }
installer_title="Eitr $release_version $release_codename installer"

mkdir -p "$profile" "$output_root"
cp -a "$profile_source/." "$profile/"
entries="$profile/efiboot/loader/entries"
sed -i "/^title/s/Arch Linux install medium/$installer_title/" "$entries/"*.conf
sed -i "s/Arch Linux install medium/$installer_title/g" "$profile/syslinux/"*.cfg
# The splash replaces scrolling boot output; a separate entry keeps the messages
# for debugging (Escape also reveals them during the splash).
sed -e "s/^title.*/title    $installer_title (boot messages)/" -e 's/^sort-key.*/sort-key 03/' \
  -e '/^options/s/$/ copytoram=n/' "$entries/01-archiso-linux.conf" > "$entries/03-eitr-boot-messages.conf"
sed -i '/^options/s/$/ quiet splash copytoram=n/' "$entries/01-archiso-linux.conf"
sed -i '0,/^APPEND archisobasedir/s//APPEND quiet splash copytoram=n archisobasedir/' \
  "$profile/syslinux/archiso_sys-linux.cfg"
sed -i '/^HOOKS=/s/ kms / kms plymouth /' "$profile/airootfs/etc/mkinitcpio.conf.d/archiso.conf"
grep -q ' kms plymouth ' "$profile/airootfs/etc/mkinitcpio.conf.d/archiso.conf"
install -Dm644 -t "$profile/airootfs/usr/share/plymouth/themes/eitr" \
  "$repo_root/distro/plymouth/eitr/eitr.plymouth" "$repo_root/distro/plymouth/eitr/eitr.script" \
  "$repo_root/distro/plymouth/eitr/"*.png
install -Dm644 /dev/stdin "$profile/airootfs/etc/plymouth/plymouthd.conf" <<'EOF'
[Daemon]
Theme=eitr
EOF
# Export committed files only, so ignored or untracked machine-local state
# (primary display, caches, notification settings) never reaches the image.
# The installer reads scripts and small files from this tree; the eitr-desktop
# package in the payload already carries the wallpapers, theme previews and
# lockscreen videos, so they are not stored on the medium twice.
installer_excludes=(
  ':(exclude,glob)themes/*/backgrounds/**'
  ':(exclude,glob)themes/*/references/**'
  ':(exclude,glob)themes/*/preview.png'
  ':(exclude,glob)quickshell/lockscreen/themes/**/*.mp4'
)
desktop_config="$profile/airootfs/opt/desktop-config"
mkdir -p "$desktop_config"
git -C "$repo_root" archive --format=tar HEAD -- . "${installer_excludes[@]}" | tar -x -C "$desktop_config"
bash "$repo_root/distro/pkg/eitr-desktop/source-version.sh" "$repo_root" \
  > "$desktop_config/distro/pkg/eitr-desktop/source-version"
# mkarchiso copies airootfs without file modes; restore the executable bits.
while IFS= read -r -d '' file; do
  printf 'file_permissions[%q]="0:0:755"\n' "/opt/desktop-config/${file#"$desktop_config"/}"
done < <(find "$desktop_config" -type f -perm -u+x -print0 | sort -z) >> "$profile/profiledef.sh"
mkdir -p "$profile/airootfs/usr/local/bin"
ln -s /opt/desktop-config/distro/archinstall/eitr-guided-install "$profile/airootfs/usr/local/bin/eitr-guided-install"
# A test VM hands the installer its answers through QEMU's firmware config and
# reads the progress from the first serial port. A real machine installs
# unattended from eitr-answers.json on a drive labelled EITR-ANSWERS (after a
# countdown that Ctrl+C cancels); otherwise it gets the wizard.
cat >> "$profile/airootfs/root/.zlogin" <<'ZLOGIN'

if [[ $(tty) == /dev/tty1 ]]; then
  answers=/sys/firmware/qemu_fw_cfg/by_name/opt/eitr/answers/raw
  if [[ -r $answers ]]; then
    eitr-guided-install --answers "$answers" 2>&1 | tee /dev/ttyS0
  elif [[ -e /dev/disk/by-label/EITR-ANSWERS ]] && mkdir -p /run/eitr-answers \
      && mount -o ro /dev/disk/by-label/EITR-ANSWERS /run/eitr-answers \
      && [[ -r /run/eitr-answers/eitr-answers.json ]]; then
    eitr-guided-install --answers /run/eitr-answers/eitr-answers.json
  else
    eitr-guided-install
  fi
fi
ZLOGIN
printf '\niso_name="eitr"\niso_label="EITR_$(date +%%Y%%m)"\niso_publisher="Eitr <https://github.com/eitr-org/eitr>"\niso_application="%s"\n' \
  "$installer_title" >> "$profile/profiledef.sh"
# Fast rebuilds; the live kernel supports Zstandard SquashFS images.
printf '\nairootfs_image_tool_options=("-comp" "zstd" "-Xcompression-level" "6" "-b" "1M")\n' >> "$profile/profiledef.sh"
printf '\nTo install Eitr (erases the disk you select), run: eitr-guided-install\n' >> "$profile/airootfs/etc/motd"
# The live environment needs the installer and splash, not the desktop packages,
# which the installer reads from the payload on the medium.
printf '\ncurl\ngit\nplymouth\npython-pillow\n' >> "$profile/packages.x86_64"
sort -u -o "$profile/packages.x86_64" "$profile/packages.x86_64"
sudo mkarchiso -v -w "$build_root/work" -o "$build_root/base" "$profile"

base_iso="$(find "$build_root/base" -maxdepth 1 -name '*.iso' -print -quit)"
[[ -n "$base_iso" ]] || { printf 'mkarchiso produced no ISO.\n' >&2; exit 1; }
# The download is named by release only; the checksum tells builds apart.
final_iso="$output_root/eitr-$release_version.iso"
[[ ! -e "$final_iso" ]] || { printf 'Refusing to overwrite %s.\n' "$final_iso" >&2; exit 1; }
# Replay keeps the BIOS/UEFI boot records; the payload joins the ISO filesystem.
xorriso -indev "$base_iso" -outdev "$final_iso" -boot_image any replay \
  -map "$payload" /eitr -chown_r 0 /eitr -- -chgrp_r 0 /eitr -- -chmod_r a+r,go-w /eitr --
(cd "$output_root" && sha256sum "$(basename "$final_iso")" > "$(basename "$final_iso").sha256")
printf 'Built %s\n' "$final_iso"
