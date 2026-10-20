#!/usr/bin/env bash
# Prints the eitr-desktop package version for an Eitr tree: computed from Git
# for a checkout, or read from the stamp build-iso.sh writes into its export.
set -euo pipefail

repo="${1:?usage: source-version.sh REPO}"
repo="$(cd -- "$repo" && pwd -P)"
stamp="$repo/distro/pkg/eitr-desktop/source-version"

if [[ "$(git -C "$repo" rev-parse --show-toplevel 2>/dev/null)" == "$repo" ]]; then
  # The release from distro/release.json, then the commit's UTC time (identical
  # in shallow and full clones) and hash. See distro/RELEASES.md.
  release="$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["version"])' "$repo/distro/release.json")"
  [[ "$release" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { printf 'Invalid release version: %s\n' "$release" >&2; exit 1; }
  printf '%s.%s.g%s\n' "$release" "$(TZ=UTC git -C "$repo" log -1 --format=%cd --date=format-local:%Y%m%d.%H%M%S HEAD)" \
    "$(git -C "$repo" rev-parse --short=7 HEAD)"
elif [[ -f "$stamp" ]]; then
  version="$(<"$stamp")"
  [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]{8}\.[0-9]{6}\.g[0-9a-f]{7,}$ ]] || { printf 'Invalid version stamp: %s\n' "$stamp" >&2; exit 1; }
  printf '%s\n' "$version"
else
  printf '%s is neither a Git checkout nor a stamped export of Eitr.\n' "$repo" >&2
  exit 1
fi
