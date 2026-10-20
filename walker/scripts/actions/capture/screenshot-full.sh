#!/usr/bin/env bash

exec "$(dirname "$0")/screenshot.sh" full "${1:-edit}"
