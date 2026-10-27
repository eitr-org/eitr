#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config_dirs=(nvim)
config_files=(dolphinrc filetypesrc mimeapps.list)
shell_files=(.zshrc .p10k.zsh .ls_colors)
# Paths this installer created are recorded here, so a rerun after a partial
# failure skips them instead of mistaking them for pre-existing user configs.
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/eitr"
install_record="$state_dir/installed-paths"

cleanup_paths=()
cleanup() {
  if (( ${#cleanup_paths[@]} )); then rm -rf -- "${cleanup_paths[@]}"; fi
}
trap cleanup EXIT

die() { printf '%s\n' "$*" >&2; exit 1; }
manifest() {
  python3 - "$repo_root/distro/lib" "$1" <<'PYPROFILE'
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from eitr_policy import excluded
blocked = excluded()
for line in Path(sys.argv[2]).read_text().splitlines():
    package = line.split('#')[0].strip()
    if package and package not in blocked:
        print(package)
PYPROFILE
}

is_recorded() { [[ -f "$install_record" ]] && grep -Fxq -- "$1" "$install_record"; }
record() {
  is_recorded "$1" && return
  mkdir -p -- "$state_dir"
  printf '%s\n' "$1" >> "$install_record"
}

same_content() {
  if [[ -L "$1" || -L "$2" ]]; then
    [[ -L "$1" && -L "$2" && "$(readlink -- "$1")" == "$(readlink -- "$2")" ]]
  else
    diff -rq -- "$1" "$2" >/dev/null 2>&1
  fi
}

# Prints clear, installed, or conflict for one source -> target pair.
target_state() {
  if [[ ! -e "$2" && ! -L "$2" ]]; then printf 'clear\n'
  elif is_recorded "${2#"$HOME"/}"; then printf 'installed\n'
  elif same_content "$1" "$2"; then printf 'installed\n'
  else printf 'conflict\n'
  fi
}

# Builds the eitr-desktop package from this tree's committed HEAD (or a
# stamped ISO export) and installs it; pacman resolves its official depends.
# The package ships the default configs, data files, root helper and user units.
install_desktop_package() {
  local build_dir
  local -a package
  local name
  mkdir -p -- "${XDG_CACHE_HOME:-$HOME/.cache}/eitr"
  # Kept on disk, not in a tmpfs /tmp: the tree includes large wallpapers.
  build_dir="$(mktemp -d -- "${XDG_CACHE_HOME:-$HOME/.cache}/eitr/package.XXXXXX")"
  cleanup_paths+=("$build_dir")
  export BUILDDIR="$build_dir/build" PKGDEST="$build_dir/out" PKGEXT=.pkg.tar
  while IFS= read -r name; do
    (cd "$repo_root/distro/pkg/$name" && makepkg --syncdeps --noconfirm --force)
    mapfile -t package < <(cd "$repo_root/distro/pkg/$name" && makepkg --packagelist)
    sudo pacman -U --needed -- "${package[@]}"
  done < <(manifest "$repo_root/distro/local-packages.txt")
  (cd "$repo_root/distro/pkg/eitr-desktop" && makepkg --nodeps --noconfirm --force)
  mapfile -t package < <(cd "$repo_root/distro/pkg/eitr-desktop" && makepkg --packagelist)
  unset BUILDDIR PKGDEST PKGEXT
  sudo pacman -U --needed -- "${package[@]}"
}

# EITR_SHELL_ASSETS names a directory of <name>.tar.zst checkouts that the ISO
# bundles, so an offline installation unpacks them instead of cloning.
clone_once() {
  local url="$1" target="$2" name="$3" parent staging
  if [[ -d "$target/.git" ]]; then return; fi
  [[ ! -e "$target" ]] || die "Exists but is not a Git checkout: $target"
  parent="$(dirname -- "$target")"
  mkdir -p -- "$parent"
  staging="$(mktemp -d -- "$parent/.eitr-clone.XXXXXX")"
  cleanup_paths+=("$staging")
  if [[ -n ${EITR_SHELL_ASSETS:-} ]]; then
    mkdir -- "$staging/item"
    tar --zstd -xf "$EITR_SHELL_ASSETS/$name.tar.zst" -C "$staging/item"
    [[ -d "$staging/item/.git" ]] || die "Bundled $name is not a Git checkout"
  else
    git clone --depth 1 -- "$url" "$staging/item"
  fi
  mv -T -- "$staging/item" "$target"
}

# Oh My Zsh loads custom plugins from <name>/<name>.plugin.zsh, while Arch
# installs these plugins as <name>.zsh, so a small loader bridges the names.
zsh_plugin_loader() {
  local name="$1" loader="$HOME/.oh-my-zsh/custom/plugins/$1/$1.plugin.zsh"
  [[ ! -e "$loader" ]] || return 0
  mkdir -p -- "$(dirname -- "$loader")"
  printf 'source /usr/share/zsh/plugins/%s/%s.zsh\n' "$name" "$name" > "$loader"
}

sources=()
targets=()
add_target() { sources+=("$1"); targets+=("$2"); }
add_tree() {
  local source_root="$1" target_root="$2" file
  [[ -d "$source_root" ]] || return 0
  while IFS= read -r -d '' file; do
    add_target "$file" "$target_root/${file#"$source_root"/}"
  done < <(find "$source_root" \( -type f -o -type l \) -print0 | sort -z)
}
collect_targets() {
  local source target
  local -a config_command=(eitr-config targets)
  if [[ -f "$repo_root/distro/bin/eitr-config" ]]; then
    config_command=(python3 "$repo_root/distro/bin/eitr-config" --repo "$repo_root" targets)
  fi
  while IFS=$'\t' read -r source target; do
    add_target "$source" "$target"
  done < <("${config_command[@]}")
}

shell_setup_clear() {
  local name home_sources="$repo_root/HOME_FILES"
  [[ -d "$home_sources" ]] || home_sources="$repo_root/home"
  for name in "${shell_files[@]}"; do
    [[ "$(target_state "$home_sources/$name" "$HOME/$name")" != conflict ]] || return 1
  done
}

validate_manifests() {
  local -a official=("$@") missing=() aur=() not_found=()
  local package found
  if ! pacman -Si -- "${official[@]}" >/dev/null 2>&1; then
    # pacman -Si does not resolve virtual packages; -Sp resolves like -S does.
    for package in "${official[@]}"; do
      pacman -Si -- "$package" >/dev/null 2>&1 ||
        pacman -Sp --print-format '%n' -- "$package" >/dev/null 2>&1 ||
        missing+=("$package")
    done
  fi
  if (( ${#missing[@]} )); then
    die "Official manifest entries not found in enabled repositories: ${missing[*]}"
  fi
  mapfile -t aur < <(manifest "$repo_root/distro/aur-packages.txt"; manifest "$repo_root/distro/aur-apps.txt")
  if ! command -v yay >/dev/null; then
    printf 'yay is not installed yet; AUR manifest names were not validated.\n'
    return
  fi
  found="$(yay -Si -- "${aur[@]}" 2>/dev/null | sed -n 's/^Name[[:space:]]*:[[:space:]]*//p')" || true
  for package in "${aur[@]}"; do
    grep -Fxq -- "$package" <<< "$found" || not_found+=("$package")
  done
  if (( ${#not_found[@]} )); then
    die "AUR manifest entries not found: ${not_found[*]}"
  fi
}

# Seeds this user's defaults, shell, theme styles and user units. Never
# overwrites existing files; needs no root.
seed_user() {
  mkdir -p "$HOME/.config" "$HOME/.cache" "$HOME/.local/bin"
  # Standard folders (Desktop, Documents, Downloads, Music, Pictures, Videos...)
  # in the account's language, plus Development for the project menus.
  mkdir -p "$HOME/Development"
  if command -v xdg-user-dirs-update >/dev/null 2>&1; then
    # Development is the projects folder, so xdg-user-dirs does not add Projects.
    xdg-user-dirs-update --set PROJECTS "$HOME/Development" &&
      xdg-user-dirs-update || printf 'Could not create the standard home folders.\n' >&2
  fi
  # The shipped .zshrc needs Oh My Zsh (eitr-config waits for it), so clone it
  # before seeding the defaults.
  if shell_setup_clear; then
    clone_once https://github.com/ohmyzsh/ohmyzsh.git "$HOME/.oh-my-zsh" oh-my-zsh
    clone_once https://github.com/romkatv/powerlevel10k.git "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" powerlevel10k
    zsh_plugin_loader zsh-autosuggestions
    zsh_plugin_loader zsh-syntax-highlighting
    for name in "${shell_files[@]}"; do targets+=("$HOME/$name"); done
  else
    printf 'Existing Zsh files found; skipped Oh My Zsh setup and kept your shell files.\n' >&2
  fi
  # Copies only missing defaults (never overwrites) and records their checksums
  # so later `eitr-config update` runs can tell unedited files from edited ones.
  eitr-config seed
  for target in "${targets[@]}"; do
    if [[ -e "$target" || -L "$target" ]]; then record "${target#"$HOME"/}"; fi
  done

  # Hyprland and the bar default to a generic layout. Machine-local overrides are
  # Git-ignored, but a copy made from a working checkout could still carry them.
  # Only remove files that exist in this checkout too, so a user's own override
  # created after a failed first run is never deleted.
  if ! is_recorded step:machine-local-cleanup; then
    for name in local.lua preferred-outputs primary-display; do
      if [[ -e "$repo_root/hypr/$name" ]] && same_content "$repo_root/hypr/$name" "$HOME/.config/hypr/$name"; then
        rm -f -- "$HOME/.config/hypr/$name"
      fi
    done
    record step:machine-local-cleanup
  fi
  # The keyboard chosen in the installer becomes the desktop layout; plain US keeps
  # the default US + US International, and an existing choice is never replaced.
  python3 "$repo_root/quickshell/desktop-bar/scripts/keyboard-layout.py" seed-from-system >/dev/null ||
    printf 'Could not apply the installer keyboard layout; choose it in the Keyboard panel.\n' >&2
  # OBS records into the Videos folder's Records instead of its default, the home folder.
  if command -v obs >/dev/null 2>&1; then
    python3 "$repo_root/quickshell/desktop-bar/scripts/obs-control.py" default-folder >/dev/null ||
      printf 'Could not set the OBS recording folder; choose it in OBS > Settings > Output.\n' >&2
  fi
  [[ -e "$HOME/.cache/current-theme" ]] || printf 'afterglow\n' > "$HOME/.cache/current-theme"
  if [[ ! -e "$HOME/.cache/current-wallpaper-image" && ! -L "$HOME/.cache/current-wallpaper-image" ]]; then
    wallpaper="$(find "$HOME/.config/theme/current/backgrounds" -maxdepth 1 -type f \
      \( -iname '*.png' -o -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.webp' \) | sort | head -n 1)"
    if [[ -n "$wallpaper" ]]; then
      ln -s -- "$wallpaper" "$HOME/.cache/current-wallpaper-image"
      printf '%s\n' "$wallpaper" > "$HOME/.cache/current-wallpaper"
    fi
  fi
  # Generate the app styles for the seeded theme. Running-session effects are
  # skipped; without a session bus, a private one lets gsettings write dconf.
  styles=(env EITR_NO_SESSION=1 eitr-run walker/scripts/themes/generate.sh)
  if [[ -n ${DBUS_SESSION_BUS_ADDRESS:-} ]]; then "${styles[@]}" >/dev/null
  else dbus-run-session -- "${styles[@]}" >/dev/null 2>&1
  fi || printf 'Some theme styles failed; choose a theme in Walker to retry.\n' >&2
  # A new home already has the current settings shape.
  python3 /usr/share/eitr/lib/migrations.py --mark-all
  # Packaged icons and desktop entries are indexed by pacman hooks; only user
  # directories that exist (the themed Codex icon, user entries) need a refresh.
  if [[ -d "$HOME/.local/share/icons/hicolor" ]] && command -v gtk-update-icon-cache >/dev/null; then
    gtk-update-icon-cache -f -t -q "$HOME/.local/share/icons/hicolor"
  fi
  if [[ -d "$HOME/.local/share/applications" ]]; then
    update-desktop-database "$HOME/.local/share/applications"
  fi

  if systemctl --user show-environment >/dev/null 2>&1; then
    systemctl --user daemon-reload
    systemctl --user enable --now nightlight-auto.timer
  else
    # What `systemctl --user enable` does, for a TTY or installer chroot.
    mkdir -p -- "$HOME/.config/systemd/user/timers.target.wants"
    ln -sfn /usr/lib/systemd/user/nightlight-auto.timer \
      "$HOME/.config/systemd/user/timers.target.wants/nightlight-auto.timer"
  fi
}

if [[ ${EUID} -eq 0 ]]; then
  die 'Run as the new desktop user, not root.'
fi
if ! command -v pacman >/dev/null || ! command -v sudo >/dev/null; then
  die 'This installer requires an installed Arch Linux system and sudo.'
fi
if ! command -v python3 >/dev/null; then
  die 'Preflight requires Python. Run sudo pacman -Syu --needed python, then retry.'
fi
if [[ ${1:-} == --check ]]; then
  if systemctl is-enabled --quiet NetworkManager.service 2>/dev/null; then
    die 'NetworkManager is enabled. This desktop uses iwd/networkd; resolve that conflict first.'
  fi
  # The same read-only layout check snapshots-setup runs later, so an
  # unsupported subvolume layout stops here before any package is installed.
  python3 "$repo_root/distro/system/eitr-system.py" snapshots-check ||
    die 'Snapshot-protected updates need a supported Btrfs layout; see distro/RECOVERY.md.'
  for item in "${config_dirs[@]}" "${config_files[@]}"; do
    [[ -e "$repo_root/$item" ]] || die "Missing source: $item"
  done
  collect_targets
  conflicts=()
  installed=0
  for index in "${!targets[@]}"; do
    case "$(target_state "${sources[$index]}" "${targets[$index]}")" in
      conflict) conflicts+=("${targets[$index]}") ;;
      installed) installed=$((installed + 1)) ;;
    esac
  done
  if (( ${#conflicts[@]} )); then
    printf 'Existing user config would be overwritten; move it aside first:\n' >&2
    printf '  %s\n' "${conflicts[@]}" >&2
    exit 1
  fi
  (( installed == 0 )) || printf 'Already installed by this installer (will skip): %d paths\n' "$installed"
  shell_setup_clear || printf 'Existing Zsh files found; Zsh/Oh My Zsh setup will be skipped.\n'
  if ! pacman -Si steam >/dev/null 2>&1; then
    die 'Enable [multilib] in /etc/pacman.conf, run sudo pacman -Sy, then retry.'
  fi
  hardware_output="$(bash "$repo_root/distro/hardware/detect.sh")"
  mapfile -t hardware_packages <<< "$hardware_output"
  mapfile -t official < <(manifest "$repo_root/distro/packages.txt"; manifest "$repo_root/distro/apps.txt")
  validate_manifests "${hardware_packages[@]}" "${official[@]}"
  printf 'Fresh-install target looks clear for %s. No changes made.\n' "$HOME"
  exit 0
fi
if [[ ${1:-} == --seed-user && $# -eq 1 ]]; then
  # The ISO installer's per-user step, after it installed the packages offline.
  collect_targets
  seed_user
  exit 0
fi
if [[ $# -ne 0 ]]; then
  printf 'Usage: %s [--check|--seed-user]\n' "$0" >&2
  exit 2
fi

bash "$0" --check
collect_targets
hardware_output="$(bash "$repo_root/distro/hardware/detect.sh")"
mapfile -t hardware_packages <<< "$hardware_output"
mapfile -t official < <(manifest "$repo_root/distro/packages.txt")
mapfile -t apps < <(manifest "$repo_root/distro/apps.txt")
mapfile -t aur < <(manifest "$repo_root/distro/aur-packages.txt")
mapfile -t aur_apps < <(manifest "$repo_root/distro/aur-apps.txt")

sudo pacman -Syu --needed -- "${hardware_packages[@]}" "${official[@]}" "${apps[@]}"
export MAKEPKG_CONF="$repo_root/distro/makepkg.conf"
if ! command -v yay >/dev/null; then
  build_dir="$(mktemp -d)"
  cleanup_paths+=("$build_dir")
  git clone --depth 1 https://aur.archlinux.org/yay.git "$build_dir/yay"
  (cd "$build_dir/yay" && makepkg -si --noconfirm)
fi
yay -S --needed -- "${aur[@]}" "${aur_apps[@]}"

# Development runtimes and AI CLIs are installed only by explicit menu selection;
# their catalogs ship in /usr/share/eitr with the package.
install_desktop_package
sudo /usr/lib/eitr/eitr-system snapshots-setup
# Snapshot boot entries change the boot menu, so they need typed confirmation.
bash "$repo_root/distro/bootloader/setup.sh" --offer
sudo install -Dm644 /usr/share/eitr/system-update-policy.conf /etc/eitr/system-update-policy.conf

seed_user
sudo bash "$repo_root/distro/system/configure-desktop.sh" "$(id -un)"
# GeForce NOW uses the same software.json recipe as Walker → Gaming.
python3 "$repo_root/walker/scripts/actions/install/software.py" recipe gaming geforcenow
printf '\nInstalled desktop files for %s. Reboot after reviewing network and SDDM setup.\n' "$USER"
printf 'Docker and cronie are installed but not enabled. Enable them only if needed:\n'
printf '  sudo systemctl enable --now docker.service cronie.service\n'
printf '  sudo usermod -aG docker %s   # docker group membership is root-equivalent\n' "$(id -un)"
