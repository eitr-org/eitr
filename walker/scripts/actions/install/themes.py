#!/usr/bin/env python3
"""JSON theme package operations; no interactive or terminal UI."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').is_file():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(library))
        break

from eitr_theme_packages import Themes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('index', 'install'):
        command = commands.add_parser(name)
        command.add_argument('url')
        if name == 'install':
            command.add_argument('ids', nargs='+')
    for name in ('update', 'remove', 'hide', 'unhide'):
        commands.add_parser(name).add_argument('id')
    for name in ('list', 'check'):
        commands.add_parser(name)
    arguments = parser.parse_args()
    backend = Themes()
    try:
        if arguments.command == 'install':
            result = backend.install(arguments.url, arguments.ids)
        elif arguments.command == 'index':
            result = backend.index(arguments.url)
        elif arguments.command in ('update', 'remove', 'hide', 'unhide'):
            result = getattr(backend, arguments.command)(arguments.id)
        else:
            result = getattr(backend, 'installed' if arguments.command == 'list' else 'check')()
        print(json.dumps(dict(ok=True, result=result)))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        message = 'Git operation failed' if isinstance(error, subprocess.SubprocessError) else str(error)
        print(json.dumps(dict(ok=False, error=message)))
        return 1


if __name__ == '__main__':
    sys.exit(main())
