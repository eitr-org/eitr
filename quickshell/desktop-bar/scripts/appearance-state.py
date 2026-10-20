#!/usr/bin/env python3
"""Persist appearance selections separately from disposable compatibility caches."""
import argparse
import os
from pathlib import Path
import sys

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break
from eitr_paths import cache, config, read_settings, write_settings
from eitr_i18n import tr


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['adopt', 'restore', 'theme', 'wallpaper'])
    parser.add_argument('value', nargs='?')
    arguments = parser.parse_args()
    preference = config('eitr/appearance.json')
    if arguments.action in {'theme', 'wallpaper'}:
        if not arguments.value:
            raise ValueError(tr('A selection is required'))
        write_settings(preference, {arguments.action: arguments.value})
        return
    if arguments.action == 'adopt' and not preference.exists():
        selected = {}
        for field in ('theme', 'wallpaper'):
            try:
                selected[field] = cache('current-' + field).read_text().strip()
            except FileNotFoundError:
                pass
        write_settings(preference, selected)
    values = read_settings(preference)
    cache().mkdir(parents=True, exist_ok=True)
    for field in ('theme', 'wallpaper'):
        value = values.get(field)
        if isinstance(value, str) and value:
            target = cache('current-' + field)
            temporary = target.with_suffix('.new')
            temporary.write_text(value + '\n')
            temporary.replace(target)
    wallpaper = values.get('wallpaper')
    if isinstance(wallpaper, str) and Path(wallpaper).is_file():
        target = cache('current-wallpaper-image')
        temporary = target.with_suffix('.new')
        temporary.unlink(missing_ok=True)
        temporary.symlink_to(wallpaper)
        temporary.replace(target)


if __name__ == '__main__':
    main()
