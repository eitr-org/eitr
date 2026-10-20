#!/usr/bin/env bash
# fzf preview for cloud log lines: pretty-print embedded JSON, else highlight as a log line.

line="$(printf '%b\n' "${1:-}")"
plain="$(printf '%s\n' "$line" | sed 's/\x1b\[[0-9;]*m//g')"

if printf '%s\n' "$plain" | jq -C . 2>/dev/null; then
  exit 0
fi

json_object="$(printf '%s\n' "$plain" | sed 's/^[^{]*//')"
if [ -n "$json_object" ] && [ "$json_object" != "$plain" ] && printf '%s\n' "$json_object" | jq -C . 2>/dev/null; then
  exit 0
fi

json_array="$(printf '%s\n' "$plain" | sed 's/^[^[]*//')"
if [ -n "$json_array" ] && [ "$json_array" != "$plain" ] && printf '%s\n' "$json_array" | jq -C . 2>/dev/null; then
  exit 0
fi

printf '%s\n' "$line" | bat --style=plain --color=always --language=log 2>/dev/null || printf '%s\n' "$line"
