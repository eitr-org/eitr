#!/usr/bin/env bash
set -euo pipefail

mode="${1:-wallpaper}"
case "$mode" in
  wallpaper|theme|theme-dark|theme-light) ;;
  *) exit 2 ;;
esac

eitr-shell desktop-bar ipc call -- appearance show "$mode"
