#!/usr/bin/env python3
"""Register the assistant bridge, or serve its newline-delimited MCP transport."""
from pathlib import Path
import sys
for _eitr_parent in Path(__file__).resolve().parents:
    _eitr_lib = _eitr_parent / 'lib'
    if not (_eitr_lib / 'eitr_paths.py').is_file():
        _eitr_lib = _eitr_parent / 'distro/lib'
    if (_eitr_lib / 'eitr_paths.py').is_file():
        sys.path.insert(0, str(_eitr_lib))
        break

import fcntl
import os
import subprocess
from eitr_collaboration import LABELS, connected, disable, enable, enabled, safe_path, serve
from eitr_i18n import tr
from eitr_paths import code, state


def locked():
    lock = state('eitr/assistants.lock')
    safe_path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    stream = lock.open('a')
    os.chmod(lock, 0o600)
    fcntl.flock(stream, fcntl.LOCK_EX)
    return stream


def toggle():
    """Turning off is immediate; turning on explains everything in a terminal first."""
    with locked():
        if enabled():
            errors = disable()
            if errors:
                raise ValueError('\n'.join(errors))
            return 0
    if not connected():
        raise ValueError(tr('Sign in to an assistant before enabling collaboration.'))
    subprocess.Popen(['kitty', '-e', sys.executable, str(code('walker/scripts/actions/task-terminal.py')),
                      sys.executable, str(Path(__file__).resolve()), 'enable'],
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     start_new_session=True)
    return 0


def enable_interactively():
    identifiers = list(connected())
    if not identifiers:
        raise ValueError(tr('Sign in to an assistant before enabling collaboration.'))
    print(tr('Let assistants work together') + '\n')
    print(tr('This connects {assistants}. Each of them can then ask another one for a review, an explanation or a suggestion.',
             assistants=', '.join(LABELS[identifier] for identifier in identifiers)) + '\n')
    for line in (tr('Each hand-off uses the helper’s subscription and counts toward its limits.'),
                 tr('Your assistant asks you before every hand-off; nothing is sent on its own.'),
                 tr('Helpers only read: they cannot change files or run commands.'),
                 tr('The question and the files a helper reads are sent to that helper’s provider.'),
                 tr('Turn it off again from the same row in the AI menu.')):
        print('  • ' + line)
    try:
        answer = input('\n' + tr('Type yes to connect them (Enter cancels): '))
    except EOFError:
        answer = ''
    if answer.strip() != 'yes':
        print(tr('Nothing was changed.'))
        return 0
    with locked():
        errors = enable(identifiers)
    if errors:
        raise ValueError('\n'.join(errors))
    print(tr('Connected. Restart open assistant sessions to use it.'))
    return 0


def main(arguments):
    from eitr_policy import require
    if arguments != ['get']:
        require('assistants_together')
    if arguments == ['serve']:
        serve(sys.stdin, sys.stdout)
        return 0
    try:
        if arguments == ['get']:
            print('on' if enabled() else 'off')
            return 0
        if arguments == ['toggle']:
            return toggle()
        if arguments == ['enable']:
            return enable_interactively()
    except (OSError, ValueError) as error:
        message = tr('Assistant collaboration: {error}', error=str(error))
        print(message, file=sys.stderr)
        subprocess.run(['notify-send', '--app-name=Eitr', message], check=False)
        return 1
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
