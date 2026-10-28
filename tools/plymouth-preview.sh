#!/usr/bin/env bash
# Preview this checkout without selecting a default theme or touching boot files.
set -euo pipefail

preview_theme=/usr/share/plymouth/themes/eitr-preview
renderer_directory=/usr/lib/plymouth/renderers
runtime_directory=/run/plymouth
x11_sockets=/tmp/.X11-unix

preview_player() (
    local work=$1 daemon_pid='' attempt
    [[ $(id -u) == 0 ]] || return 1
    if [[ $(readlink /proc/self/ns/net) == "$(readlink /proc/1/ns/net)" || $(readlink /proc/self/ns/mnt) == "$(readlink /proc/1/ns/mnt)" ]]; then
        echo 'The preview player requires private network and mount namespaces.' >&2; return 1
    fi
    finish_player() {
        trap - EXIT INT TERM
        timeout 3 plymouth quit >/dev/null 2>&1 || true
        if [[ -n "$daemon_pid" ]]; then
            kill "$daemon_pid" 2>/dev/null || true
            wait "$daemon_pid" 2>/dev/null || true
        fi
    }
    trap finish_player EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    mount --make-rprivate /
    mount --bind "$work/renderers" "$renderer_directory"
    mount --bind "$work/runtime" "$runtime_directory"
    # The upstream X11 test setup provides two decorated windows, never fullscreen.
    export GDK_BACKEND=x11 PLY_CREATE_FAKE_MULTI_HEAD_SETUP=1
    unset WAYLAND_DISPLAY NOTIFY_SOCKET
    plymouthd --no-daemon --no-boot-log --ignore-serial-consoles --graphical-boot \
        --tty=/dev/null --mode=boot --pid-file="$work/daemon.pid" \
        --kernel-command-line='splash plymouth.splash=eitr-preview plymouth.ignore-udev plymouth.nolog plymouth.force-scale=1' \
        >/dev/null 2>&1 &
    daemon_pid=$!
    for attempt in {1..50}; do
        kill -0 "$daemon_pid" 2>/dev/null || { echo 'The windowed Plymouth daemon could not start.' >&2; return 1; }
        if plymouth --ping >/dev/null 2>&1; then break; fi
        sleep 0.1
    done
    plymouth --ping >/dev/null 2>&1 || { echo 'The preview daemon did not become ready.' >&2; return 1; }
    echo 'Boot: flowing logo and gold rune loading (6 seconds).'
    plymouth show-splash
    sleep 6
    echo 'Password: logo and password box only. Type any demo text in a preview window and press Enter.'
    # The answer goes directly to cat and /dev/null, never to shell variables or logs.
    if ! plymouth ask-for-password --command=/usr/bin/cat --number-of-tries=1 --prompt='Preview only: type any demo text' </dev/null >/dev/null 2>&1; then
        echo 'The preview password prompt was canceled or failed.' >&2; return 1
    fi
    echo 'Password accepted: gold rune loading returns (6 seconds).'
    sleep 6
    echo 'Shutdown: flowing logo and gold rune loading (5 seconds).'
    plymouth change-mode --shutdown
    sleep 5
    echo 'Preview finished.'
)

preview_main() (
    local script root source work='' child_group='' created_theme=no created_runtime=no display_number
    [[ $(id -u) == 0 ]] || { echo 'Run this preview with sudo from a graphical terminal.' >&2; return 1; }
    [[ ${DISPLAY:-} =~ ^:([0-9]+)(\.[0-9]+)?$ ]] || { echo 'A local X11/Xwayland DISPLAY is required; run from your graphical terminal.' >&2; return 1; }
    display_number=${BASH_REMATCH[1]}
    [[ -S "$x11_sockets/X$display_number" ]] || { echo 'The local X11 socket is unavailable.' >&2; return 1; }
    if [[ -n ${XAUTHORITY:-} && ! -r $XAUTHORITY ]]; then
        echo 'The graphical session XAUTHORITY file is not readable.' >&2; return 1
    fi
    if [[ -z ${XAUTHORITY:-} && -n ${SUDO_USER:-} ]]; then
        local user_home
        user_home=$(getent passwd "$SUDO_USER" | cut -d: -f6)
        if [[ -r "$user_home/.Xauthority" ]]; then export XAUTHORITY="$user_home/.Xauthority"; fi
    fi
    [[ -r "$renderer_directory/x11.so" ]] || { echo 'The Plymouth X11 renderer is not installed.' >&2; return 1; }
    [[ ! -e "$preview_theme" && ! -L "$preview_theme" ]] || { echo 'eitr-preview already exists; refusing to overwrite it.' >&2; return 1; }
    for dependency in plymouth plymouthd unshare mount setsid timeout python3; do
        command -v "$dependency" >/dev/null || { echo "Missing preview dependency: $dependency" >&2; return 1; }
    done
    timeout 5 python3 - <<'PY_X11'
import ctypes
from ctypes.util import find_library
library = ctypes.CDLL(find_library("X11") or "libX11.so.6")
library.XOpenDisplay.argtypes = [ctypes.c_char_p]
library.XOpenDisplay.restype = ctypes.c_void_p
connection = library.XOpenDisplay(None)
if not connection:
    raise SystemExit("Root cannot access X11. Preserve your graphical session's DISPLAY and XAUTHORITY when invoking sudo.")
library.XCloseDisplay.argtypes = [ctypes.c_void_p]
library.XCloseDisplay(connection)
PY_X11
    script=$(realpath -- "${BASH_SOURCE[0]}")
    root=$(dirname -- "$(dirname -- "$script")")
    source="$root/distro/plymouth/eitr"
    [[ -f "$source/eitr.plymouth" && -f "$source/eitr.script" ]] || { echo 'Run the script from a complete Eitr checkout.' >&2; return 1; }
    finish_preview() {
        local attempt
        trap - EXIT INT TERM
        if [[ -n "$child_group" ]]; then
            kill -TERM -- "-$child_group" 2>/dev/null || true
            for attempt in {1..50}; do
                kill -0 -- "-$child_group" 2>/dev/null || break
                sleep 0.1
            done
            kill -KILL -- "-$child_group" 2>/dev/null || true
            wait "$child_group" 2>/dev/null || true
        fi
        [[ $created_theme != yes ]] || rm -rf -- "$preview_theme"
        [[ -z "$work" ]] || rm -rf -- "$work"
        if [[ $created_runtime == yes ]]; then rmdir -- "$runtime_directory" 2>/dev/null || true; fi
    }
    trap finish_preview EXIT
    trap 'exit 130' INT
    trap 'exit 143' TERM
    umask 077
    work=$(mktemp -d /tmp/eitr-plymouth-preview.XXXXXX)
    mkdir -- "$preview_theme"
    created_theme=yes
    chmod 755 "$preview_theme"
    cp -- "$source/"*.png "$preview_theme/"
    cp -- "$source/eitr.script" "$preview_theme/eitr-preview.script"
    sed -e 's/^Name=.*/Name=Eitr preview/' \
        -e 's@/themes/eitr/@/themes/eitr-preview/@g' \
        -e 's@/themes/eitr$@/themes/eitr-preview@' \
        -e 's@/eitr.script$@/eitr-preview.script@' \
        "$source/eitr.plymouth" > "$preview_theme/eitr-preview.plymouth"
    mkdir -- "$work/renderers" "$work/runtime"
    cp -- "$renderer_directory/x11.so" "$work/renderers/x11.so"
    if [[ ! -d "$runtime_directory" ]]; then
        mkdir -- "$runtime_directory"
        created_runtime=yes
    fi
    echo 'Opening two windowed Plymouth test displays. Ctrl+C in this terminal cancels and cleans up.'
    # Private mount and network namespaces isolate renderers, state and the abstract control socket.
    setsid unshare --mount --net --fork bash "$script" --player "$work" &
    child_group=$!
    local result=0
    wait "$child_group" || result=$?
    child_group=''
    return "$result"
)

if [[ ${1:-} == --player && $# == 2 ]]; then
    preview_player "$2"
elif (( $# == 0 )); then
    preview_main
else
    echo 'Usage: sudo bash tools/plymouth-preview.sh' >&2
    exit 2
fi
