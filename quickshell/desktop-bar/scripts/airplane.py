#!/usr/bin/env python3
"""Block WiFi/Bluetooth and restore only radios this toggle previously blocked."""
import eitr_bootstrap
from eitr_i18n import tr
import json
import os
from pathlib import Path
import subprocess
import sys

STATE = Path(os.environ.get('XDG_RUNTIME_DIR', '/run/user/' + str(os.getuid()))) / 'eitr-airplane.json'

def radios():
    output = subprocess.run(['rfkill', '--json', '--output', 'ID,TYPE,SOFT,HARD'],
                            capture_output=True, text=True, check=True, timeout=5).stdout
    return [r for r in json.loads(output)['rfkilldevices'] if r['type'] in ('wlan', 'bluetooth')]

def blocked(value):
    return value in (True, 'blocked', 'yes')

def status():
    devices = radios()
    return {'available': bool(devices), 'enabled': bool(devices) and all(blocked(r['soft']) or blocked(r['hard']) for r in devices)}

def set_enabled(enabled):
    devices = radios()
    if enabled:
        restore = [str(r['id']) for r in devices if not blocked(r['soft'])]
        # Persist before operating: even a partial failure can be undone.
        if not STATE.exists():
            STATE.write_text(json.dumps(restore))
            STATE.chmod(0o600)
        for radio in devices:
            subprocess.run(['rfkill', 'block', str(radio['id'])], check=True, timeout=5)
    else:
        if not STATE.exists():
            raise ValueError(tr('Radios were blocked elsewhere; enable them individually in WiFi/Bluetooth.'))
        restore = json.loads(STATE.read_text())
        present = {str(r['id']) for r in devices}
        for ident in restore:
            if ident in present:
                subprocess.run(['rfkill', 'unblock', ident], check=True, timeout=5)
        STATE.unlink()
    return status()

if __name__ == '__main__':
    try:
        result = set_enabled(sys.argv[2] == 'true') if len(sys.argv) == 3 and sys.argv[1] == 'set' else status()
        print(json.dumps(result))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({'error': str(error)}))
        sys.exit(1)
