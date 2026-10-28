"""Switch retired Graphite selections through the standard theme application."""
import json
import os
from pathlib import Path
import subprocess

from eitr_paths import cache, code, config


def selected_theme():
    try:
        values = json.loads(config('eitr/appearance.json').read_text())
        if values.get('theme'):
            return values['theme']
    except FileNotFoundError:
        pass
    for path in (cache('current-theme'), Path.home() / '.cache/current-theme'):
        if path.is_file():
            return path.read_text().strip()
    return None


if selected_theme() == 'graphite':
    subprocess.run(['bash', str(code('walker/scripts/actions/style/apply.sh')), 'eitr'],
                   env=dict(os.environ, EITR_NO_SESSION='1'), check=True)
