#!/usr/bin/env bash
# Compile the desktop bar's shaders for Qt Quick; commit each .qsb with its source.
set -euo pipefail
cd "$(dirname "$0")"
for source in *.frag; do
  # SPIR-V (Vulkan) is always written; GLSL covers the OpenGL backends Linux uses.
  /usr/lib/qt6/bin/qsb --glsl "100 es,120,150" -o "$source.qsb" "$source"
done
