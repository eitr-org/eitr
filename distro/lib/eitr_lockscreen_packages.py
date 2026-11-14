"""Official package catalog and installed lockscreen design state."""
import configparser
import json
from pathlib import Path
import subprocess

from eitr_choice_lists import LOCKSCREEN_DESIGNS
from eitr_i18n import tr
from eitr_paths import code_root, config, own

MANIFEST = Path('/usr/share/eitr/lockscreen-designs.d')
LOGIN = Path('/etc/sddm.conf.d/90-desktop-lockscreen.conf')


def manifests(directory=MANIFEST):
    result = {}
    for path in sorted(directory.glob('*.json')):
        value = json.loads(path.read_text())
        for identifier, theme in value.items():
            expected = 'desktop-lockscreen-' + identifier.replace('/', '-')
            if identifier not in {row['id'] for row in LOCKSCREEN_DESIGNS} or theme != expected or identifier in result:
                raise ValueError('Invalid installed lockscreen manifest')
            result[identifier] = theme
    return result


def installed_designs():
    themes = code_root() / 'quickshell/lockscreen/themes'
    return {row['id'] for row in LOCKSCREEN_DESIGNS if (themes / row['id'] / 'Main.qml').is_file()}


def current_designs():
    result = set()
    try:
        selected = config('lockscreen/selected').read_text().strip()
        if selected.startswith('user:'):
            identifier = selected.removeprefix('user:')
            if identifier and all(character in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in identifier):
                selected = json.loads((own('lockscreens') / identifier / 'lockscreen.json').read_text())['design']
        result.add(selected)
    except (OSError, ValueError, KeyError):
        pass
    parser = configparser.ConfigParser()
    parser.read(LOGIN)
    theme = parser.get('Theme', 'Current', fallback='')
    result.update(row['id'] for row in LOCKSCREEN_DESIGNS if theme == 'desktop-lockscreen-' + row['id'].replace('/', '-'))
    return result


def listing(installed_only=False):
    installed, current = installed_designs(), current_designs()
    previews = code_root() / 'quickshell/lockscreen/previews'
    rows = []
    for row in LOCKSCREEN_DESIGNS:
        identifier = row['id']
        if installed_only and identifier not in installed:
            continue
        preview = previews / (identifier.replace('/', '-') + '.png')
        if not preview.is_file():
            preview = code_root() / 'quickshell/lockscreen/themes' / identifier / 'preview.png'
        rows.append(dict(id=identifier, name=tr(row['label']), kind='builtin' if row['builtin'] else 'official',
                         installed=identifier in installed, current=identifier in current,
                         previewUrl=preview.as_uri(), removable=not row['builtin'] and identifier not in current))
    return rows


def names(value):
    allowed = {row['id'] for row in LOCKSCREEN_DESIGNS if not row['builtin']}
    if (not isinstance(value, list) or not value or len(value) > len(allowed)
            or any(not isinstance(identifier, str) or identifier not in allowed for identifier in value)
            or len(set(value)) != len(value)):
        raise ValueError('Invalid optional lockscreen designs')
    return ['eitr-lockscreen-' + identifier.replace('/', '-') for identifier in value]


def select(identifier):
    """Uses an installed design for the session and login, as Settings > Lockscreen does."""
    if not isinstance(identifier, str) or identifier not in installed_designs():
        raise ValueError('Invalid installed lockscreen design')
    result = subprocess.run(['python3', str(code_root() / 'quickshell/lockscreen/scripts/settings.py'), 'select', identifier],
                            capture_output=True, text=True, timeout=60)
    if result.returncode:
        raise ValueError(result.stderr.strip() or tr('The lockscreen could not be changed.'))


def root(action, identifiers):
    if action not in {'install', 'remove'}:
        raise ValueError('Invalid lockscreen action')
    names(identifiers)
    if action == 'remove' and current_designs().intersection(identifiers):
        raise ValueError(tr('The current lockscreen cannot be removed.'))
    try:
        subprocess.run(['/usr/bin/pkexec', '/usr/lib/eitr/eitr-system', 'lockscreen-' + action],
                       input=json.dumps(identifiers), text=True, capture_output=True, check=True, timeout=240)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(tr('System package operation failed or was cancelled.')) from error
