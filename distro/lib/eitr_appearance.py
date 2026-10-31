"""Generate machine-local terminal and compositor appearance."""
import os
from pathlib import Path
import subprocess
import tempfile

from eitr_paths import config, read_settings
from eitr_i18n import mark

OPACITY = {'solid': 1.0, 'light': 0.9, 'medium': 0.8, 'default': 0.75, 'strong': 0.7}
PADDING = {'none': 0, 'small': 4, 'comfortable': 8}
STRENGTH = {'light': (2, 1), 'medium': (3, 2), 'strong': (5, 3)}
DEFAULTS = {'opacity': 'default', 'padding': 'none', 'blur': 'on'}
CHOICES = {
    'opacity': [('solid', mark('Solid (100%)')), ('light', mark('Light (90%)')), ('medium', mark('Medium (80%)')),
                ('default', mark('Default (75%)')), ('strong', mark('Strong (70%)'))],
    'padding': [('none', mark('None')), ('small', mark('Small')), ('comfortable', mark('Comfortable'))],
    'blur': [('off', mark('Off')), ('on', mark('On'))],
    'blur-strength': [('light', mark('Gentle')), ('medium', mark('Medium')), ('strong', mark('Strong'))],
}


def terminal_settings(path=None):
    data = read_settings(path or config('eitr/terminal.json'))
    return {key: data.get(key) if isinstance(data.get(key), str) and data.get(key) in dict(CHOICES[key]) else default
            for key, default in DEFAULTS.items()}


def blur_strength():
    value = read_settings(config('quickshell/desktop-bar/bar-settings.json')).get('blur-strength')
    return value if isinstance(value, str) and value in STRENGTH else 'medium'


def write_output(relative, text):
    output = config(relative)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=output.parent, delete=False) as temporary:
        temporary.write(text)
    try:
        os.replace(temporary.name, output)
    finally:
        Path(temporary.name).unlink(missing_ok=True)


def generate_blur():
    size, passes = STRENGTH[blur_strength()]
    disabled = 'true' if terminal_settings()['blur'] == 'off' else 'false'
    write_output('hypr/appearance.lua',
                 'hl.config({ decoration = { blur = { size = %d, passes = %d } } })\n' % (size, passes)
                 + 'hl.window_rule({ name = "eitr-terminal-blur", match = { class = "^(kitty|com\\\\.mitchellh\\\\.ghostty|ghostty)$" }, no_blur = ' + disabled + ' })\n')


def reload_compositor():
    if os.environ.get('EITR_NO_SESSION') != '1':
        subprocess.run(['hyprctl', 'reload'], check=True, timeout=5, capture_output=True)
