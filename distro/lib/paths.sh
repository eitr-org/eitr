# shellcheck shell=bash
# Source from package scripts; launchers supply the same resolved roots to QML.
EITR_CODE_ROOT="${EITR_CODE_ROOT:-/usr/share/eitr}"
EITR_LIBRARY_ROOT="${EITR_LIBRARY_ROOT:-$EITR_CODE_ROOT/lib}"
EITR_CONFIG_ROOT="${XDG_CONFIG_HOME:-$HOME/.config}"
EITR_STATE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}"
EITR_CACHE_ROOT="${XDG_CACHE_HOME:-$HOME/.cache}"
EITR_DATA_ROOT="${XDG_DATA_HOME:-$HOME/.local/share}"
for name in EITR_CONFIG_ROOT EITR_STATE_ROOT EITR_CACHE_ROOT EITR_DATA_ROOT; do
    if [[ ${!name} != /* ]]; then
        case "$name" in
            EITR_CONFIG_ROOT) EITR_CONFIG_ROOT="$HOME/.config" ;;
            EITR_STATE_ROOT) EITR_STATE_ROOT="$HOME/.local/state" ;;
            EITR_CACHE_ROOT) EITR_CACHE_ROOT="$HOME/.cache" ;;
            EITR_DATA_ROOT) EITR_DATA_ROOT="$HOME/.local/share" ;;
        esac
    fi
done
export EITR_CODE_ROOT EITR_LIBRARY_ROOT EITR_CONFIG_ROOT EITR_STATE_ROOT EITR_CACHE_ROOT EITR_DATA_ROOT
export PYTHONPATH="$EITR_LIBRARY_ROOT${PYTHONPATH:+:$PYTHONPATH}"
