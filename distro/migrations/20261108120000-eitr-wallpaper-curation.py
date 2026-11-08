"""Follow the curated Eitr wallpaper order without applying desktop settings."""
import os
from pathlib import Path
import re
import tempfile

from eitr_paths import cache, config, data, read_settings, write_settings

RENAMES = {
    'eitr': {'01-primordial-drop': '03-primordial-drop',
             '02-eitr-runestone': '04-eitr-runestone',
             '03-elivagar': '01-rune-seal',
             '04-venom-rootlight': '01-rune-seal'},
    'eitr-light': {'01-primordial-drop': '03-primordial-drop',
                   '02-elivagar': '01-gates-of-yggdrasil',
                   '03-venom-rootlight': '01-gates-of-yggdrasil'},
}


def selected_theme():
    selected = read_settings(config('eitr/appearance.json')).get('theme')
    if selected:
        return selected
    for marker in (cache('current-theme'), Path.home() / '.cache/current-theme'):
        if marker.is_file():
            return marker.read_text().strip()
    return 'eitr'


def renamed(value, theme, renames=RENAMES):
    if isinstance(value, dict):
        return {key: renamed(item, theme, renames) for key, item in value.items()}
    if isinstance(value, list):
        return [renamed(item, theme, renames) for item in value]
    if not isinstance(value, str):
        return value
    path = Path(value)
    if path.parent.name not in ('backgrounds', 'backgrounds-ultrawide'):
        return value
    if path.suffix not in ('.jpg', '.png'):
        return value
    owner = path.parent.parent
    identifier = owner.name if owner.parent.name == 'themes' else None
    if owner == config('theme/current'):
        identifier = theme
    replacement = renames.get(identifier, {}).get(path.stem)
    if replacement is None:
        return value
    suffix = path.suffix if replacement == '04-eitr-runestone' else '.jpg'
    return str(path.with_name(replacement + suffix))


def atomic_text(path, text):
    descriptor, temporary = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w') as output:
            output.write(text)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def main(renames=RENAMES):
    """Rewrite saved wallpaper paths named in renames; later migrations reuse this."""
    theme = selected_theme()
    paths = [config('eitr/appearance.json'), *data('eitr/lockscreens').glob('*/lockscreen.json')]
    for path in paths:
        if path.is_file():
            values = read_settings(path)
            updated = renamed(values, theme, renames)
            if values != updated:
                write_settings(path, updated)
    for directory in {cache(), Path.home() / '.cache'}:
        marker = directory / 'current-wallpaper'
        if marker.is_file():
            current = marker.read_text()
            updated = renamed(current.strip(), theme, renames)
            if updated != current.strip():
                atomic_text(marker, updated + '\n')
        link = directory / 'current-wallpaper-image'
        if link.is_symlink():
            current = os.readlink(link)
            updated = renamed(current, theme, renames)
            if updated != current:
                temporary = link.with_suffix('.new')
                temporary.unlink(missing_ok=True)
                temporary.symlink_to(updated)
                os.replace(temporary, link)
        monitors = directory / 'eitr/hyprpaper-monitors.conf'
        if monitors.is_file():
            current = monitors.read_text()
            updated = re.sub(r'(?m)^(\s*path\s*=\s*)([^\n]+)',
                             lambda match: match[1] + renamed(match[2], theme, renames), current)
            if current != updated:
                atomic_text(monitors, updated)


if __name__ == '__main__':
    main()
