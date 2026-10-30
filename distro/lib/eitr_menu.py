"""Canonical fixed menu rows and shortcut reference projections.

Provider metadata stays in Lua; row commands are data and are never run while
loading or indexing. Runtime-generated providers continue to own their rows.
"""
import json
from pathlib import Path
import re
import tomllib

from eitr_paths import code, config


def row_files(directory=None):
    root = Path(directory).parent if directory is not None else code('elephant')
    return sorted((root / 'menu-rows').glob('*.json'))


def effective_files(directory=None):
    roots = [Path(directory)] if directory is not None else [code('elephant/menus'), config('elephant/menus')]
    files = {}
    for root in roots:
        if root.is_dir():
            for path in root.iterdir():
                if path.suffix in {'.toml', '.lua'}:
                    files[path.stem] = path
    return sorted(files.values())


def definitions(directory=None):
    result = {}
    for path in effective_files(directory):
        if path.suffix == '.toml':
            data = tomllib.loads(path.read_text())
            result[data.get('name', path.stem)] = data
    for path in row_files(directory):
        result[path.stem] = {'entries': json.loads(path.read_text())}
    return result


def rows(menu):
    if not menu.replace('-', '').isalnum():
        raise ValueError('Invalid menu name')
    static = code(f'elephant/menus/{menu}.toml')
    if static.is_file():
        return tomllib.loads(static.read_text()).get('entries', [])
    scoped = code(f'elephant/menu-rows/{menu}.json')
    if scoped.is_file():
        return json.loads(scoped.read_text())
    raise ValueError(f'No menu named {menu}')


def parents(files, menus):
    result = {}
    for path in files:
        if path.suffix == '.lua':
            match = re.search(r'^\s*Parent\s*=\s*"([^"]+)"', path.read_text(), re.M)
            if match:
                result[path.stem] = match[1]
    for name, data in menus.items():
        if data.get('parent'):
            result[name] = data['parent']
    return result


def shortcut_reference():
    indexed = {row['text']: row for row in rows('shortcuts')}
    result = []
    for definition in json.loads(code('elephant/shortcut-reference.json').read_text()):
        entry = dict(definition)
        if 'row' in entry:
            row = indexed[entry['row']]
            entry['key'] = row['subtext']
            entry.setdefault('command', row['actions']['open'] + (' &' if entry.get('background') else ''))
        result.append(entry)
    return result


def shortcut_options():
    return '\n'.join(entry['heading'] if 'heading' in entry else
                     '  ' + entry['key'].ljust(26) + entry['description']
                     for entry in shortcut_reference())


def shortcut_command(selection):
    key = re.split(r'\s{2,}', selection.strip(), maxsplit=1)[0]
    return next((entry['command'] for entry in shortcut_reference()
                 if entry.get('key') == key), None)
