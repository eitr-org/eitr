#!/usr/bin/env bash

EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
if [[ -f "$EITR_CODE_ROOT/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/lib/paths.sh";
elif [[ -f "$EITR_CODE_ROOT/distro/lib/paths.sh" ]]; then source "$EITR_CODE_ROOT/distro/lib/paths.sh"; fi

query="$(
  "$EITR_CODE_ROOT/walker/bin/walker-dmenu" \
    --dmenu \
    --exec-search \
    --hide-scroll \
    --cache-file /dev/null \
    --height 82 \
    --prompt="Google it..." \
    < /dev/null
)"

query="${query#"${query%%[![:space:]]*}"}"
query="${query%"${query##*[![:space:]]}"}"

[[ -z "$query" ]] && exit 0

encoded_query="$(printf '%s' "$query" | jq -sRr @uri)"

"$EITR_CODE_ROOT/walker/bin/app-launch" xdg-open "https://www.google.com/search?q=$encoded_query"
