#!/usr/bin/env python3
"""The screen-share picker xdg-desktop-portal-hyprland runs (custom_picker_binary in xdph.conf).

Eitr's Record button leaves a one-time request naming the focused display just before it
starts OBS (quickshell/desktop-bar/scripts/obs_screen.py); this answers OBS's screen
requests with that display, without showing a window. Every other request, and one that
has expired or names a display that is gone, gets Hyprland's own picker unchanged."""
import fcntl
import json
import os
from pathlib import Path
import sys
import time

PICKER = '/usr/bin/hyprland-share-picker'


def request_path():
    runtime = os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}'
    return Path(runtime) / 'eitr/share-request.json'


def outputs(listing):
    """Display names from XDPH_OUTPUT_SHARING_LIST: "id:NAME:x:y:width:height;" entries."""
    return {fields[1] for entry in listing.split(';') if len(fields := entry.split(':')) >= 6}


def take_request(path, available, now=None):
    """The requested display, using up one answer; None when there is nothing valid to answer."""
    try:
        handle = path.open('r+')
    except OSError:
        return None
    with handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            request = json.loads(handle.read())
            output, remaining, expires = request['output'], int(request['remaining']), float(request['expires'])
        except (ValueError, KeyError, TypeError):
            output, remaining, expires = None, 0, 0
        current = time.time() if now is None else now
        if remaining <= 1 or current > expires:
            path.unlink(missing_ok=True)
        else:
            handle.seek(0)
            handle.truncate()
            handle.write(json.dumps(dict(request, remaining=remaining - 1)))
        if output in available and remaining > 0 and current <= expires:
            return output
    return None


def main():
    output = take_request(request_path(), outputs(os.environ.get('XDPH_OUTPUT_SHARING_LIST', '')))
    if output:
        # "r" keeps the restore token, so OBS reopens the same display until Eitr asks again.
        print(f'[SELECTION]r/screen:{output}', flush=True)
        return 0
    os.execv(PICKER, [PICKER, *sys.argv[1:]])


if __name__ == '__main__':
    sys.exit(main())
