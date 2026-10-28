"""Follow the Eitr theme rename and repair retired wallpaper selections."""
import json
import os
from pathlib import Path

from eitr_paths import cache, config, data


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
    return 'eitr'


THEME = selected_theme()
RUNESTONE = 'eitr-runestone'
RETIRED = {
    '02-odin-allfather', '03-mimir-well-of-wisdom', '04-huginn-muninn',
    '05-valkyrie', '06-odin', '08-jormungandr',
}


def renamed(value):
    if value == 'norse':
        return 'eitr'
    if isinstance(value, str):
        value = value.replace('/themes/norse/', '/themes/eitr/')
        path = Path(value)
        if '/themes/eitr/' in value and path.parent.name in ('backgrounds', 'backgrounds-ultrawide'):
            if path.stem == f'01-{RUNESTONE}':
                return str(path.with_name(f'02-{RUNESTONE}' + path.suffix))
            if path.stem == '07-fenrir' and THEME == 'ragnarok':
                return value.replace('/themes/eitr/', '/themes/ragnarok/').replace('07-fenrir', '05-fenrir')
            if path.stem in RETIRED or path.stem == '07-fenrir':
                return str(path.parent.parent / f'backgrounds/02-{RUNESTONE}.png')
        return value
    return value


def update_json(path, fields):
    try:
        values = json.loads(path.read_text())
    except FileNotFoundError:
        return
    changed = dict(values)
    for field in fields:
        if field in changed:
            changed[field] = renamed(changed[field])
    if changed != values:
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(changed, indent=2) + '\n')
        os.replace(temporary, path)


update_json(config('eitr/appearance.json'), ('theme', 'wallpaper'))
for path in data('eitr/themes').glob('*/own-theme.json'):
    update_json(path, ('previous',))
for name in ('current-theme', 'current-wallpaper'):
    # Older theme and wallpaper helpers also wrote directly to ~/.cache.
    for path in {cache(name), Path.home() / '.cache' / name}:
        if path.is_file():
            current = path.read_text()
            updated = renamed(current.strip())
            if updated != current.strip():
                temporary = path.with_suffix('.tmp')
                temporary.write_text(updated + '\n')
                os.replace(temporary, path)
for path in {cache('current-wallpaper-image'), Path.home() / '.cache/current-wallpaper-image'}:
    if path.is_symlink():
        target = os.readlink(path)
        if renamed(target) != target:
            temporary = path.with_suffix('.tmp')
            temporary.symlink_to(renamed(target))
            os.replace(temporary, path)
old = data('eitr/wallpapers/themes/norse')
new = data('eitr/wallpapers/themes/eitr')
if old.is_dir() and not new.exists():
    old.rename(new)
