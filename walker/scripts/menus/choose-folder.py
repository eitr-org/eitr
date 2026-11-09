#!/usr/bin/env python3
"""Folder chooser for the AI and project menus, shown as the Walker menu menus:choose-folder.

`start` saves a request (icon, the menu Back returns to at the top and the command
that continues with the chosen folder) and opens the menu; the menu's rows call `enter`,
`up` and `pick`. `pick` runs the saved command with EITR_CHOSEN_FOLDER set. Folders are
passed hex-encoded so a folder's name never reaches a shell or a menu policy match.
"""
import argparse
import json
import os
from pathlib import Path
import sys

CODE_ROOT = Path(os.environ.get('EITR_CODE_ROOT', '/usr/share/eitr'))
MENU = 'menus:choose-folder'


def request_path():
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR') or f'/run/user/{os.getuid()}')
    return runtime / 'eitr' / 'choose-folder.json'


def root_folder():
    return Path(os.environ.get('DEV_DIR') or Path.home()).expanduser().resolve()


def load():
    try:
        request = json.loads(request_path().read_text())
    except (OSError, ValueError):
        sys.exit(1)
    if not isinstance(request, dict) or not isinstance(request.get('then'), list):
        sys.exit(1)
    return request


def save(request):
    target = request_path()
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temporary = target.with_suffix('.tmp')
    temporary.write_text(json.dumps(request))
    temporary.chmod(0o600)
    temporary.replace(target)


def inside(request, encoded):
    """The decoded folder, only when it is an existing folder inside the chooser's root."""
    try:
        folder = Path(bytes.fromhex(encoded).decode()).resolve()
    except (ValueError, UnicodeDecodeError):
        sys.exit(1)
    root = Path(request['root'])
    if not folder.is_dir() or (folder != root and root not in folder.parents):
        sys.exit(1)
    return folder


def show(request):
    save(request)
    os.execv(str(CODE_ROOT / 'walker/bin/walker'), ['walker', '--provider', MENU])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    start = commands.add_parser('start')
    start.add_argument('--icon', default='')
    start.add_argument('--back', default='')
    start.add_argument('then', nargs=argparse.REMAINDER)
    for name in ('enter', 'pick'):
        commands.add_parser(name).add_argument('folder')
    commands.add_parser('up')
    arguments = parser.parse_args()

    if arguments.command == 'start':
        then = arguments.then[1:] if arguments.then[:1] == ['--'] else arguments.then
        if not then:
            parser.error('start needs the command that continues with the folder')
        root = root_folder()
        if not root.is_dir():
            sys.exit(1)
        show(dict(icon=arguments.icon, back=arguments.back,
                  root=str(root), current=str(root), then=then))
    request = load()
    if arguments.command == 'enter':
        show(dict(request, current=str(inside(request, arguments.folder))))
    if arguments.command == 'up':
        current = Path(request['current'])
        if current == Path(request['root']):
            if request['back']:
                os.execv(str(CODE_ROOT / 'walker/bin/walker'), ['walker', '--provider', request['back']])
            return 0
        show(dict(request, current=str(current.parent)))
    folder = inside(request, arguments.folder)
    os.execvpe(request['then'][0], request['then'], {**os.environ, 'EITR_CHOSEN_FOLDER': str(folder)})


if __name__ == '__main__':
    sys.exit(main())
