#!/usr/bin/env python3
"""Generate the read-only settings schema used by login's Lua and QML readers."""
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'distro/lib'))
from eitr_appearance import DEFAULTS as TERMINAL_DEFAULTS, CHOICES
from eitr_workspaces import DEFAULTS as WORKSPACE_DEFAULTS


def generate():
    bar = runpy.run_path(str(ROOT / 'quickshell/desktop-bar/scripts/bar-settings.py'))
    desktop = runpy.run_path(str(ROOT / 'quickshell/desktop-bar/scripts/desktop-style.py'))
    corners, styles = desktop['definitions']()
    defaults = dict(corners=corners, gaps='default', **desktop['LAYOUT_DEFAULTS'], **WORKSPACE_DEFAULTS)
    options = {key: [choice['id'] for choice in values] for key, values in desktop['LAYOUT_CHOICES'].items()}
    options.update(corners=list(styles), gaps=[choice['id'] for choice in desktop['WINDOW_GAPS']],
                   scrollFollowFocus=['yes', 'no'], scrollFullscreen=['yes', 'no'],
                   workspaceMode=['shared', 'split'], workspaceCount=list(range(5, 11)),
                   workspaceAlwaysShow=list(range(2, 11)))
    return {
        'bar-settings.py': dict(path='quickshell/desktop-bar/bar-settings.json', defaults=bar['DEFAULTS'],
                                options={key: sorted(values) for key, values in bar['OPTIONS'].items()}),
        'desktop-style.py': dict(path='eitr/style.json', defaults=defaults, options=options),
        'terminal.py': dict(path='eitr/terminal.json', defaults=TERMINAL_DEFAULTS,
                            options={key: [choice[0] for choice in CHOICES[key]] for key in TERMINAL_DEFAULTS}),
    }


if __name__ == '__main__':
    target = ROOT / 'quickshell/desktop-bar/login-settings.json'
    text = json.dumps(generate(), indent=2) + '\n'
    if '--check' in sys.argv:
        sys.exit(0 if target.read_text() == text else 'Run python3 tools/login-settings.py')
    target.write_text(text)
