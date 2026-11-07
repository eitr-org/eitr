#!/usr/bin/env python3
"""Installed MIME handlers and Eitr's shared terminal preference."""
import argparse
import configparser
import json
import os
from pathlib import Path
import shutil
import subprocess

import eitr_bootstrap
from eitr_paths import code
from eitr_i18n import mark, tr

KINDS = {
    'browser': (mark('Web browser'), ('x-scheme-handler/http', 'x-scheme-handler/https', 'text/html')),
    'files': (mark('File manager'), ('inode/directory',)),
    'editor': (mark('Text editor'), ('text/plain',)),
    'images': (mark('Image viewer'), ('image/png', 'image/jpeg')),
    'video': (mark('Video player'), ('video/mp4', 'video/x-matroska')),
    'music': (mark('Music player'), ('audio/mpeg', 'audio/flac')),
    'mail': (mark('Mail'), ('x-scheme-handler/mailto',)),
    'pdf': (mark('PDF viewer'), ('application/pdf',)),
}
TERMINAL = code('walker/scripts/actions/style/terminal.py')


def run(arguments):
    return subprocess.run(arguments, check=True, capture_output=True, text=True, timeout=10).stdout.strip()


def applications():
    roots = [Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share'))]
    roots += [Path(directory) for directory in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':') if directory]
    seen = set()
    result = {}
    for root in roots:
        directory = root / 'applications'
        for path in sorted(directory.rglob('*.desktop')):
            identifier = str(path.relative_to(directory)).replace('/', '-')
            if identifier in seen:
                continue
            seen.add(identifier)
            parser = configparser.ConfigParser(interpolation=None, strict=False)
            try:
                parser.read(path, encoding='utf-8')
                entry = parser['Desktop Entry']
                if entry.get('Type') != 'Application' or 'true' in (entry.get('Hidden', '').lower(), entry.get('NoDisplay', '').lower()):
                    continue
                if not entry.get('Exec') or (entry.get('TryExec') and not shutil.which(entry['TryExec'])):
                    continue
                result[identifier] = {'value': identifier, 'label': entry.get('Name', identifier),
                                      'mimes': entry.get('MimeType', '').split(';')}
            except (OSError, configparser.Error, KeyError, UnicodeError):
                continue
    return result


def summary():
    apps = applications()
    rows = []
    for kind, (label, mimes) in KINDS.items():
        current = run(['xdg-mime', 'query', 'default', mimes[0]])
        # Two desktop files with the same name (a native and a Flatpak build) show once,
        # keeping the current default when it is one of them.
        handlers = sorted((identifier for identifier, app in apps.items() if mimes[0] in app['mimes']),
                          key=lambda identifier: identifier != current)
        named = {}
        for identifier in handlers:
            named.setdefault(apps[identifier]['label'].casefold(), {'value': identifier, 'label': apps[identifier]['label']})
        choices = sorted(named.values(), key=lambda app: app['label'].casefold())
        rows.append({'kind': kind, 'label': tr(label), 'current': current,
                     'name': apps.get(current, {}).get('label', current), 'choices': choices})
    terminal = json.loads(run(['python3', str(TERMINAL), 'summary']))
    rows.append({'kind': 'terminal', 'label': tr('Terminal'), 'current': terminal['current'],
                 'name': terminal['current'], 'choices': [choice for choice in terminal['choices'] if choice['available']]})
    return {'items': rows}


def select(kind, identifier):
    if kind == 'terminal':
        terminal = json.loads(run(['python3', str(TERMINAL), 'summary']))
        if not any(choice['value'] == identifier and choice['available'] for choice in terminal['choices']):
            raise ValueError('Terminal is not installed')
        run(['python3', str(TERMINAL), 'set', 'terminal', identifier])
        return
    if kind not in KINDS:
        raise ValueError('Unknown application type')
    app = applications().get(identifier)
    mimes = KINDS[kind][1]
    if not app or mimes[0] not in app['mimes']:
        raise ValueError('Application does not handle this type')
    for mime in mimes:
        if mime in app['mimes']:
            run(['xdg-mime', 'default', identifier, mime])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('summary', 'set'))
    parser.add_argument('arguments', nargs='*')
    args = parser.parse_args()
    if args.action == 'summary' and not args.arguments:
        print(json.dumps(summary()))
    elif args.action == 'set' and len(args.arguments) == 2:
        select(*args.arguments)
    else:
        parser.error('Expected summary or set KIND DESKTOP_ID')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise SystemExit(str(error))
