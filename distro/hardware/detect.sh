#!/usr/bin/env bash
set -euo pipefail

hardware_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pci_root="${HARDWARE_SYSFS_ROOT:-/sys/bus/pci/devices}"
cpuinfo="${HARDWARE_CPUINFO:-/proc/cpuinfo}"
modules_root="${HARDWARE_MODULES_ROOT:-/usr/lib/modules}"
power_supply_root="${HARDWARE_POWER_SUPPLY_ROOT:-/sys/class/power_supply}"
chassis_type="${HARDWARE_CHASSIS_TYPE:-/sys/class/dmi/id/chassis_type}"
declare -A found=() packages=()
declare -a manifests=()

if [[ -r "$cpuinfo" ]]; then
  if grep -qm1 '^vendor_id[[:space:]]*:[[:space:]]*AuthenticAMD' "$cpuinfo"; then
    manifests+=(amd.txt)
  elif grep -qm1 '^vendor_id[[:space:]]*:[[:space:]]*GenuineIntel' "$cpuinfo"; then
    manifests+=(intel.txt)
  fi
fi

shopt -s nullglob
for device in "$pci_root"/*; do
  [[ -r "$device/class" && -r "$device/vendor" ]] || continue
  class="$(<"$device/class")"
  [[ "$class" == 0x03* ]] || continue
  vendor="$(<"$device/vendor")"
  case "${vendor,,}" in
    0x1002) found[amd]=1 ;;
    0x8086) found[intel]=1 ;;
    0x10de) found[nvidia]=1 ;;
    0x1af4|0x1234|0x80ee|0x15ad|0x1b36|0x1414) found[virtual]=1 ;;
    *) printf 'Unknown display controller: %s (vendor %s)\n' "$device" "$vendor" >&2 ;;
  esac
done

if (( ${#found[@]} == 0 )); then
  printf 'No supported GPU detected. Review PCI hardware before installing Steam drivers.\n' >&2
  exit 1
fi
if [[ -n ${found[nvidia]:-} ]]; then
  case "${DISTRO_NVIDIA_DRIVER:-}" in
    open)
      manifests+=(nvidia.txt)
      if [[ -n ${found[intel]:-} || -n ${found[amd]:-} ]]; then
        manifests+=(nvidia-hybrid.txt)
      fi
      ;;
    skip)
      if (( ${#found[@]} == 1 )); then
        printf 'Cannot skip the only detected GPU.\n' >&2
        exit 1
      fi
      ;;
    *)
      printf 'NVIDIA GPU detected. Review its generation, then set DISTRO_NVIDIA_DRIVER=open for Turing or newer, or skip if another GPU will drive the desktop. Legacy cards need manual driver selection.\n' >&2
      exit 1
      ;;
  esac
fi

manifests+=(graphics-common.txt)

# Laptop-only packages: a system battery (peripheral batteries are not BAT*),
# or a DMI portable/laptop/notebook/sub-notebook/convertible/detachable chassis.
is_laptop() {
  local supply
  for supply in "$power_supply_root"/BAT*; do
    [[ -r "$supply/type" && "$(<"$supply/type")" == Battery ]] && return 0
  done
  [[ -r "$chassis_type" ]] || return 1
  case "$(<"$chassis_type")" in 8|9|10|14|31|32) return 0 ;; esac
  return 1
}
if is_laptop; then
  printf 'Laptop detected: adding power profile support and laptop audio firmware.\n' >&2
  manifests+=(laptop.txt)
  [[ " ${manifests[*]} " == *' intel.txt '* ]] && manifests+=(intel-laptop.txt)
fi
[[ -n ${found[amd]:-} ]] && manifests+=(amd-gpu.txt)
[[ -n ${found[intel]:-} ]] && manifests+=(intel-gpu.txt)
[[ -n ${found[virtual]:-} ]] && manifests+=(virtual-gpu.txt)

# Prebuilt nvidia-open modules only match Arch's default kernel. Any other
# installed kernel needs the DKMS variant plus headers for every kernel.
nvidia_dkms_headers=()
if [[ " ${manifests[*]} " == *' nvidia.txt '* ]]; then
  for pkgbase in "$modules_root"/*/pkgbase; do
    kernel="$(<"$pkgbase")"
    [[ "$kernel" == linux ]] || nvidia_dkms_headers=(linux-headers)
  done
  if (( ${#nvidia_dkms_headers[@]} )); then
    for pkgbase in "$modules_root"/*/pkgbase; do
      nvidia_dkms_headers+=("$(<"$pkgbase")-headers")
    done
  fi
fi

emit() {
  [[ -n ${packages[$1]:-} ]] && return
  packages["$1"]=1
  printf '%s\n' "$1"
}

printf 'Detected GPU vendors: %s\n' "${!found[*]}" >&2
for manifest in "${manifests[@]}"; do
  while IFS= read -r package || [[ -n "$package" ]]; do
    [[ -z "$package" || "$package" == \#* ]] && continue
    if [[ "$package" == nvidia-open ]] && (( ${#nvidia_dkms_headers[@]} )); then
      package=nvidia-open-dkms
    fi
    emit "$package"
  done < "$hardware_dir/$manifest"
done
for package in "${nvidia_dkms_headers[@]}"; do
  emit "$package"
done
