#!/usr/bin/env python3
"""Snapshot menu labels/actions outside Walker's typing path; never execute them."""

import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code, config as user_config
from eitr_i18n import tr
from eitr_i18n import select_locale, table
import subprocess
import tempfile
import time
import tomllib

CONFIG = user_config("elephant/menus")
RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'eitr-search'
INDEX = RUNTIME / 'index.json'
MAX_AGE = 60
EXCLUDED = {'clipboard', 'search-index', 'plugin-actions'}
CLOUD_MENUS = code('walker/scripts/menus/cloud/navigation-menus.json')


def effective_files(directory=None):
    directories = [directory] if directory is not None else [code('elephant/menus'), CONFIG]
    files = {}
    for root in directories:
        if root.is_dir():
            for path in root.iterdir():
                if path.suffix in {'.toml', '.lua'}:
                    files[path.stem] = path
    return sorted(files.values())


def providers(directory=None):
    # Resource pickers perform network requests; index only their parent actions.
    resource_menus = {name for name, spec in json.loads(CLOUD_MENUS.read_text()).items()
                      if spec.get('selector')}
    return ['menus:' + path.stem for path in effective_files(directory)
            if path.suffix in {'.toml', '.lua'} and path.stem not in EXCLUDED | resource_menus]


def row_files(directory=None):
    """Lua menus built on elephant/scoped-menu.lua keep their rows in elephant/menu-rows."""
    rows = (directory.parent if directory is not None else code('elephant')) / 'menu-rows'
    return sorted(rows.glob('*.json')) if rows.is_dir() else []


def definitions(directory=None):
    """{menu name: definition} for every menu whose rows are data: TOML menus, and the
    Lua menus whose rows are elephant/menu-rows/<name>.json (their Parent is in the Lua)."""
    result = {}
    for path in effective_files(directory):
        if path.suffix == '.toml':
            data = tomllib.loads(path.read_text())
            result[data.get('name', path.stem)] = data
    for path in row_files(directory):
        result[path.stem] = {'entries': json.loads(path.read_text())}
    return result


def parents(directory=None):
    """{menu name: parent menu} from the data menus and the Lua menus' Parent globals."""
    result = {}
    for path in effective_files(directory):
        if path.suffix == '.lua':
            match = re.search(r'^Parent\s*=\s*"([^"]+)"', path.read_text(), re.M)
            if match:
                result[path.stem] = match[1]
    for name, data in definitions(directory).items():
        if data.get('parent'):
            result[name] = data['parent']
    return result


def ancestors(name, parent_of):
    chain = []
    while name in parent_of and parent_of[name] not in chain and len(chain) < 32:
        name = parent_of[name]
        chain.append(name)
    return chain


def keyword_index(directory=None):
    messages = table('menus')
    result = {}
    for name, data in definitions(directory).items():
        for entry in data.get('entries', []):
            english = entry['text']
            translated = messages.get(english, english)
            keywords = entry.get('keywords', []) + [english, translated]
            if entry.get('subtext') != '>':
                keywords += [entry.get('subtext', '')]
            result[('menus:' + name, english)] = keywords
            result[('menus:' + name, translated)] = keywords
    return result


def snapshot(output, keywords=None, parent_of=None, menus=None):
    """Rows of the query OUTPUT. Each row lists its menu's ancestors, so a menu can
    search the menus below it; a data menu's submenu row names that submenu."""
    messages = table('menus')
    submenus = {('menus:' + name, title): entry['submenu']
                for name, data in (menus or {}).items() for entry in data.get('entries', []) if entry.get('submenu')
                for title in (entry['text'], messages.get(entry['text'], entry['text']))}
    rows = {}
    for line in output.splitlines():
        response = json.loads(line)
        item = response.get('item')
        if not item or not item.get('text') or not item.get('identifier'):
            continue
        provider = item.get('provider', '')
        if not provider.startswith('menus:') or provider.removeprefix('menus:') in EXCLUDED:
            continue
        menu = provider.removeprefix('menus:')
        key = hashlib.sha256((provider + '\0' + item['identifier']).encode()).hexdigest()
        actions = item.get('actions', [])
        row = dict(key=key, provider=provider, identifier=item['identifier'],
                   text=item['text'], subtext=item.get('subtext', ''),
                   icon=item.get('icon', ''),
                   actions=[action for action in actions if action == 'open'] if provider == 'menus:apps' else actions,
                   keywords=(keywords or {}).get((provider, item['text']), []),
                   menus=ancestors(menu, parent_of or {}))
        # Generated menus' submenus may depend on the selected row's value; those keep
        # their activation through this helper.
        if (provider, item['text']) in submenus:
            row['submenu'] = submenus[(provider, item['text'])]
        rows[key] = row
    return list(rows.values())


def read_index():
    try:
        data = json.loads(INDEX.read_text())
        return data if isinstance(data, dict) and isinstance(data.get('rows'), list) else {}
    except (OSError, ValueError):
        return {}


def fresh(data):
    if not data or data.get('locale') != select_locale() or time.time() - data.get('updated', 0) > MAX_AGE:
        return False
    newest = max((path.stat().st_mtime for path in [*effective_files(), *row_files()]), default=0)
    return data['updated'] >= newest


def refresh():
    RUNTIME.mkdir(mode=0o700, parents=True, exist_ok=True)
    with (RUNTIME / 'refresh.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        output = subprocess.run(['elephant', 'query', '--async=false', '--json',
                                 ','.join(providers()) + ';;10000'],
                                capture_output=True, text=True, check=True, timeout=15).stdout
        menus = definitions()
        rows = snapshot(output, keyword_index(), parents(), menus)
        if not rows:
            raise ValueError('Menu index returned no entries')
        fd, temporary = tempfile.mkstemp(prefix='.index-', dir=RUNTIME)
        try:
            with os.fdopen(fd, 'w') as handle:
                json.dump({'updated': time.time(), 'locale': select_locale(), 'rows': rows}, handle)
            os.replace(temporary, INDEX)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)


def prepare():
    current = read_index()
    if fresh(current):
        return
    if not current:
        # A cold first launch prepares the catalog once, not on each keystroke.
        refresh()
    else:
        subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'refresh'],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, start_new_session=True)


def activate(key, action):
    row = next((row for row in read_index().get('rows', []) if row['key'] == key), None)
    if not row or action not in row['actions']:
        raise ValueError(tr('Search entry expired; reopen Main to refresh'))
    if row['provider'] == 'menus:apps' and action != 'open':
        raise ValueError(tr('Global app search only supports launching'))
    result = subprocess.run(['elephant', 'query', '--async=false', '--json',
                             row['provider'] + ';;10000'],
                            capture_output=True, text=True, check=True, timeout=15)
    current = snapshot(result.stdout)
    if not any(item['identifier'] == row['identifier'] and action in item['actions']
               for item in current):
        raise ValueError(tr('Search entry changed; reopen Main to refresh'))
    fields = [row['provider'], row['identifier'], action, '', '']
    if any(';' in field for field in fields):
        raise ValueError(tr('Unsupported action identifier'))
    # Elephant owns the commands and submenu routing; the index stores no shell code.
    subprocess.run(['elephant', 'activate', ';'.join(fields)], check=True, timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'refresh', 'activate'])
    parser.add_argument('values', nargs='*')
    args = parser.parse_args()
    try:
        if args.operation == 'activate':
            if len(args.values) != 2:
                parser.error('activate requires an entry key and action')
            activate(*args.values)
        elif args.operation == 'prepare':
            prepare()
        else:
            refresh()
    except (OSError, ValueError, subprocess.SubprocessError):
        print(tr('Could not refresh or activate menu search; existing menus remain available.'), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
