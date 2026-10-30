#!/usr/bin/env python3
"""Snapshot menu labels/actions outside Walker's typing path; never execute them."""

import argparse
import fcntl
import hashlib
import json
import os
import re
from pathlib import Path

import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / "lib"
    if not (_eitr_lib / "eitr_paths.py").is_file():
        _eitr_lib = _eitr_parent / "distro/lib"
    if (_eitr_lib / "eitr_paths.py").is_file():
        sys.path.insert(0, str(_eitr_lib))
        break
from eitr_paths import code
from eitr_battery import system_batteries
from eitr_i18n import tr
from eitr_i18n import select_locale, table
import subprocess
import tempfile
import time
from eitr_menu import definitions, row_files, effective_files, parents as menu_parents

RUNTIME = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')) / 'eitr-search'
INDEX = RUNTIME / 'index.json'
MAX_AGE = 60
EXCLUDED = {'clipboard', 'search-index', 'plugin-actions', 'plugin-visuals'}
CLOUD_MENUS = code('walker/scripts/menus/cloud/navigation-menus.json')



# Keyboard layouts are a long list that crowds every search; the Keyboard row that
# opens them stays findable.
UNSEARCHED = {'keyboard', 'keyboard-add'}


def below_cloud_accounts(files):
    """Menus under a cloud account: its services, resources and logs. Global search
    keeps the account lists (aws-profiles, *-contexts); what lies below them is
    searched only inside the opened menu."""
    cloud = set(json.loads(CLOUD_MENUS.read_text()))
    parents = menu_parents(files, {})
    below = set()
    for name in parents:
        current, seen = name, set()
        while current and current not in seen:
            if current in cloud:
                below.add(name)
                break
            seen.add(current)
            current = parents.get(current)
    return below | cloud


def providers(directory=None):
    files = effective_files(directory)
    excluded = EXCLUDED | UNSEARCHED | below_cloud_accounts(files)
    return ['menus:' + path.stem for path in files
            if path.suffix in {'.toml', '.lua'} and path.stem not in excluded]


def parents(directory=None):
    return menu_parents(effective_files(directory), definitions(directory))


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
    responses = [json.loads(line) for line in output.splitlines()]
    fixed = {('menus:' + name, title)
             for name, data in (menus or {}).items() for entry in data.get('entries', [])
             for title in (entry['text'], messages.get(entry['text'], entry['text']))}
    titles = {entry['submenu']: messages.get(entry['text'], entry['text'])
              for name, data in (menus or {}).items() for entry in data.get('entries', [])
              if entry.get('submenu') and (parent_of or {}).get(entry['submenu'], name) == name}
    # Dynamic folder labels (such as installed assistants) come from the same
    # snapshot, not another provider read or a second list of menu names.
    folder_titles = {}
    for response in responses:
        item = response.get('item') or {}
        destination = re.match(r'^menus:([^:]+):', item.get('identifier', ''))
        if destination and item.get('text'):
            parent = (parent_of or {}).get(destination[1])
            if parent is None or item.get('provider') == 'menus:' + parent:
                folder_titles.setdefault(destination[1], set()).add(item['text'])
    for destination, labels in folder_titles.items():
        if len(labels) == 1:
            titles[destination] = next(iter(labels))
    rows = {}
    battery_available = bool(system_batteries())
    for response in responses:
        item = response.get('item')
        if not item or not item.get('text') or not item.get('identifier'):
            continue
        provider = item.get('provider', '')
        if not provider.startswith('menus:') or provider.removeprefix('menus:') in EXCLUDED:
            continue
        menu = provider.removeprefix('menus:')
        if not battery_available and (menu == 'battery-limit' or submenus.get((provider, item['text'])) == 'battery-limit'):
            continue
        key = hashlib.sha256((provider + '\0' + item['identifier']).encode()).hexdigest()
        actions = item.get('actions', [])
        row = dict(key=key, provider=provider, identifier=item['identifier'],
                   text=item['text'], subtext=item.get('subtext', ''),
                   icon=item.get('icon', ''),
                   actions=[action for action in actions if action == 'open'] if provider == 'menus:apps' else actions,
                   keywords=(keywords or {}).get((provider, item['text']), []),
                   menus=ancestors(menu, parent_of or {}))
        if (provider, item['text']) not in fixed:
            row['path'] = [{'menu': ancestor, 'title': titles.get(ancestor, '')}
                           for ancestor in reversed([menu, *row['menus']])]
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
    newest = max((path.stat().st_mtime for path in [*effective_files(), *row_files(),
                 code('elephant/shortcut-reference.json')]), default=0)
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


def warm(attempts=60, delay=0.5):
    """Build the index right after Elephant starts (its service runs this), so the
    first Walker after a boot finds it ready instead of building it while you wait."""
    for _ in range(attempts):
        if subprocess.run(['elephant', 'query', '--async=false', '--json', 'menus:main;;1'],
                          capture_output=True, timeout=15).returncode == 0:
            break
        time.sleep(delay)
    if not fresh(read_index()):
        refresh()


def activate(key, action):
    from eitr_policy import row_allowed
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
    if not row_allowed(row):
        raise ValueError("Disabled by organization policy")
    # Elephant owns the commands and submenu routing; the index stores no shell code.
    subprocess.run(['elephant', 'activate', ';'.join(fields)], check=True, timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=['prepare', 'refresh', 'warm', 'activate'])
    parser.add_argument('values', nargs='*')
    args = parser.parse_args()
    try:
        if args.operation == 'activate':
            if len(args.values) != 2:
                parser.error('activate requires an entry key and action')
            activate(*args.values)
        elif args.operation == 'prepare':
            prepare()
        elif args.operation == 'warm':
            warm()
        else:
            refresh()
    except (OSError, ValueError, subprocess.SubprocessError):
        print(tr('Could not refresh or activate menu search; existing menus remain available.'), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
