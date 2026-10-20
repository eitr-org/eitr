#!/usr/bin/env python3
"""Read and set a laptop backlight or the first DDC monitor brightness."""
import eitr_bootstrap
from eitr_i18n import tr

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


if __name__ == '__main__':
    try:
        result = set_brightness(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None) if len(sys.argv) > 2 and sys.argv[1] == 'set' else status()
    except (OSError, ValueError, subprocess.SubprocessError, RuntimeError) as error:
        result = {'available': False, 'kind': '', 'name': 'Brightness unavailable',
                  'value': 0, 'error': str(error)}
    print(json.dumps(result))
