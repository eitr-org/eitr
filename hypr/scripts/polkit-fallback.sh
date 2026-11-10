#!/usr/bin/env bash
# The bar is the session's polkit agent (administrator password prompts). When it has
# not registered within 15 s of the bar answering (it failed, crashed, or polkit refused
# it), KDE's agent takes over so password prompts still work.
set -uo pipefail

for ((attempt = 0; attempt < 30; attempt++)); do
  if [[ "$(eitr-shell desktop-bar ipc call -- polkit status 2>/dev/null)" == registered ]]; then
    exit 0
  fi
  sleep 0.5
done
# The agent's Qt Quick dialog takes QT_STYLE_OVERRIDE as a Qt Quick style, and there is
# no Kvantum one: with it set, every password prompt fails before it opens.
exec env -u QT_STYLE_OVERRIDE /usr/lib/polkit-kde-authentication-agent-1
