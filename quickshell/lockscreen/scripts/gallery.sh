#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export QML_IMPORT_PATH="$root/imports:$root/..${QML_IMPORT_PATH:+:$QML_IMPORT_PATH}"
exec quickshell -n -p "$root/design-gallery.qml"
