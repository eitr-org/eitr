#!/usr/bin/env python3
"""Display panel brightness and exact idle dim/restore for supported displays."""
import eitr_bootstrap
from eitr_i18n import tr

import fcntl
import os
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


def run(*command):
    return subprocess.run(command, capture_output=True, text=True, timeout=8, check=True).stdout


def backlight():
    devices = []
    for device in Path('/sys/class/backlight').glob('*'):
        try:
            if int((device / 'max_brightness').read_text()) <= 0:
                continue
            kind = (device / 'type').read_text().strip()
        except (OSError, ValueError):
            continue
        devices.append(({'raw': 0, 'platform': 1, 'firmware': 2}.get(kind, 3), device.name, device))
    return min(devices)[2] if devices else None


def status():
    device = backlight()
    if device:
        current = int((device / 'brightness').read_text())
        maximum = int((device / 'max_brightness').read_text())
        return {'available': True, 'kind': 'backlight', 'name': device.name,
                'value': round(100 * current / maximum) if maximum else 0}
    if shutil.which('ddcutil'):
        match = re.search(r'VCP 10 C (\d+) (\d+)', run('ddcutil', 'getvcp', '10', '--brief'))
        if match:
            current, maximum = map(int, match.groups())
            return {'available': True, 'kind': 'ddc', 'name': 'Display brightness',
                    'value': round(100 * current / maximum) if maximum else 0,
                    'maximum': maximum}
    return {'available': False, 'kind': '', 'name': 'No brightness control available', 'value': 0}


def set_brightness(value, maximum=None):
    value = max(1, min(100, int(value)))
    device = backlight()
    if device:
        if shutil.which('brightnessctl'):
            run('brightnessctl', '--device', device.name, 'set', f'{value}%')
        else:
            current = status()['value']
            difference = value - current
            if difference:
                run('swayosd-client', '--brightness', f'{difference:+d}')
    elif shutil.which('ddcutil'):
        maximum = int(maximum) if maximum else status()['maximum']
        run('ddcutil', 'setvcp', '10', str(round(maximum * value / 100)))
        return {'available': True, 'kind': 'ddc', 'name': 'Display brightness',
                'value': value, 'maximum': maximum}
    else:
        raise RuntimeError(tr('No brightness control available'))
    return status()


IDLE_ERRORS = (OSError, ValueError, KeyError, subprocess.SubprocessError)


def idle_targets():
    """Read exact hardware levels; unavailable DDC controls are optional."""
    device = backlight()
    if device and shutil.which('brightnessctl'):
        try:
            yield {'kind': 'backlight', 'device': device.name,
                   'level': int((device / 'brightness').read_text())}
        except IDLE_ERRORS:
            pass
    if shutil.which('ddcutil'):
        try:
            buses = re.findall(r'/dev/i2c-(\d+)', run('ddcutil', 'detect', '--brief'))
        except IDLE_ERRORS:
            return
        for bus in dict.fromkeys(buses):
            try:
                match = re.search(r'VCP 10 C (\d+) (\d+)',
                                  run('ddcutil', '--bus', bus, 'getvcp', '10', '--brief'))
                if match and int(match[2]) > 0:
                    yield {'kind': 'ddc', 'bus': bus, 'level': int(match[1])}
            except IDLE_ERRORS:
                continue


def idle_set(target, level):
    if target['kind'] == 'backlight':
        run('brightnessctl', '--device', target['device'], 'set', str(level))
    elif target['kind'] == 'ddc':
        run('ddcutil', '--bus', target['bus'], 'setvcp', '10', str(level))
    else:
        raise ValueError('Unknown brightness control')


def idle_brightness(action):
    """Serialize timeout/resume and retain failed restores for the next attempt."""
    runtime = Path(os.environ['XDG_RUNTIME_DIR']) / 'eitr-idle-brightness'
    runtime.mkdir(mode=0o700, exist_ok=True)
    with (runtime / 'lock').open('w') as guard:
        fcntl.flock(guard, fcntl.LOCK_EX)
        saved = runtime / 'levels.json'
        if action == 'dim' and saved.exists():
            return

        def save_levels(levels):
            temporary = runtime / 'levels.tmp'
            temporary.write_text(json.dumps(levels))
            temporary.replace(saved)

        targets = json.loads(saved.read_text()) if saved.exists() else []
        if action == 'dim':
            for target in idle_targets():
                targets.append(target)
                save_levels(targets)
                try:
                    idle_set(target, max(1, round(target['level'] * 0.3)))
                except IDLE_ERRORS:
                    continue
        else:
            pending = []
            for target in targets:
                try:
                    idle_set(target, target['level'])
                except IDLE_ERRORS:
                    pending.append(target)
            if pending:
                save_levels(pending)
            else:
                saved.unlink(missing_ok=True)


if __name__ == '__main__':
    if sys.argv[1:] in (['dim'], ['restore']):
        idle_brightness(sys.argv[1])
        sys.exit(0)
    try:
        result = set_brightness(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None) if len(sys.argv) > 2 and sys.argv[1] == 'set' else status()
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as error:
        result = {'available': False, 'kind': '', 'name': 'Brightness unavailable',
                  'value': 0, 'error': str(error)}
    print(json.dumps(result))
