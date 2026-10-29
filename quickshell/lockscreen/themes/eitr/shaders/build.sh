#!/usr/bin/env bash
set -euo pipefail
shader_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
for shader in brand sky burn; do
    /usr/lib/qt6/bin/qsb --glsl '100 es,120,150' --hlsl 50 --msl 12 -o "$shader_dir/$shader.frag.qsb" "$shader_dir/$shader.frag"
done
