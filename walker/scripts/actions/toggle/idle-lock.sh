#!/usr/bin/env bash

if pgrep -x hypridle >/dev/null; then
  pkill -x hypridle
  eitr-run quickshell/desktop-bar/scripts/brightness.py restore
else
  if command -v uwsm >/dev/null 2>&1; then
    uwsm app -- eitr-hypridle >/dev/null 2>&1 &
  else
    setsid eitr-hypridle >/dev/null 2>&1 &
  fi

fi
