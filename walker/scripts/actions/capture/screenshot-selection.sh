#!/usr/bin/env bash

exec "$(dirname "$0")/screenshot.sh" selection "${1:-edit}"
