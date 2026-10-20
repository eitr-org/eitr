#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

set -euo pipefail

WALKER_DMENU="$EITR_CODE_ROOT/walker/bin/walker-dmenu"

missing=()
for cmd in file magick ffmpeg wl-copy realpath; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done

if ((${#missing[@]})); then
  notify-send -u critical "Transcode unavailable" "Missing: ${missing[*]}"
  exit 1
fi

pick() {
  local prompt="$1"
  shift
  printf "%s\n" "$@" | "$WALKER_DMENU" --dmenu --no-sort --cache-file /dev/null --prompt="$prompt"
}

pick_file() {
  find "$HOME/Pictures" "$HOME/Videos" "$HOME/Downloads" -type f \
    \( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' -o -iname '*.webp' -o -iname '*.gif' -o -iname '*.heic' -o -iname '*.avif' \
    -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.m4v' -o -iname '*.mkv' -o -iname '*.webm' -o -iname '*.avi' \) 2>/dev/null |
    "$WALKER_DMENU" --dmenu --matching=contains --cache-file /dev/null --prompt="Transcode file"
}

media_type() {
  case "$(file -b --mime-type "$1")" in
    image/*) echo image ;;
    video/*) echo video ;;
    *) return 1 ;;
  esac
}

output_path() {
  local input="$1" format="$2" resolution="$3"
  local dir base stem

  dir="$(dirname -- "$input")"
  base="$(basename -- "$input")"
  stem="${base%.*}"

  printf "%s/%s-%s.%s" "$dir" "$stem" "$resolution" "$format"
}

input="${1:-}"
[[ -n "$input" ]] || input="$(pick_file)"
[[ -n "$input" ]] || exit 0
[[ -f "$input" ]] || {
  notify-send -u critical "File not found" "$input"
  exit 1
}

type="$(media_type "$input" || true)"
[[ -n "$type" ]] || {
  notify-send -u critical "Unsupported media" "$(file -b --mime-type "$input")"
  exit 1
}

if [[ "$type" == image ]]; then
  format="$(pick "Image format" jpg png)"
  [[ -n "$format" ]] || exit 0
  resolution="$(pick "Image size" high medium low)"
  [[ -n "$resolution" ]] || exit 0

  output="$(output_path "$input" "$format" "$resolution")"
  case "$resolution" in
    high) resize="3160x>" ;;
    medium) resize="2160x>" ;;
    low) resize="1080x>" ;;
    *) exit 1 ;;
  esac

  case "$format" in
    jpg) magick "$input" -resize "$resize" -quality 85 -strip "$output" ;;
    png) magick "$input" -resize "$resize" -strip -define png:compression-filter=5 -define png:compression-level=9 -define png:compression-strategy=1 -define png:exclude-chunk=all "$output" ;;
    *) exit 1 ;;
  esac
else
  format="$(pick "Video format" mp4 gif)"
  [[ -n "$format" ]] || exit 0
  resolution="$(pick "Video size" 1080p 720p 4k)"
  [[ -n "$resolution" ]] || exit 0

  output="$(output_path "$input" "$format" "$resolution")"
  case "$resolution" in
    4k) scale="scale=-2:2160" ;;
    1080p) scale="scale=-2:1080" ;;
    720p) scale="scale=-2:720" ;;
    *) exit 1 ;;
  esac

  notify-send "Transcoding video" "$(basename -- "$input") to $format $resolution"

  case "$format" in
    mp4) ffmpeg -y -i "$input" -vf "$scale" -c:v libx264 -preset fast -crf 23 -c:a aac -b:a 192k -movflags +faststart "$output" ;;
    gif) ffmpeg -y -i "$input" -vf "fps=10,$scale:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" "$output" ;;
    *) exit 1 ;;
  esac
fi

printf "file://%s\n" "$(realpath -- "$output")" | wl-copy --type text/uri-list
notify-send "Transcode complete" "$(basename -- "$output") copied as file URI."
