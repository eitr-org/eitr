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


def toggle():
    lock = state('eitr/assistants.lock')
    safe_path(lock)
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a') as stream:
        os.chmod(lock, 0o600)
        fcntl.flock(stream, fcntl.LOCK_EX)
        if enabled():
            errors = disable()
        else:
            identifiers = list(connected())
            if not identifiers:
                raise ValueError(tr('Sign in to Claude or Codex before enabling collaboration.'))
            question = tr('Connect {assistants}? Each hand-off uses that assistant’s subscription and counts toward its limits. Ask before every hand-off.',
                          assistants=', '.join(LABELS[identifier] for identifier in identifiers))
            confirmation = tr('Confirm')
            result = subprocess.run([str(code('walker/bin/walker')), '--dmenu', '--placeholder', question,
                                     '--width', '800', '--minheight', '100'],
                                    input=tr('Cancel') + '\n' + confirmation + '\n', text=True, capture_output=True)
            if result.returncode or result.stdout.strip() != confirmation:
                return 0
            errors = enable(identifiers)
        if errors:
            raise ValueError('\n'.join(errors))
    return 0


def main(arguments):
    if arguments == ['serve']:
        serve(sys.stdin, sys.stdout)
        return 0
    try:
        if arguments == ['get']:
            print('on' if enabled() else 'off')
            return 0
        if arguments == ['toggle']:
            return toggle()
    except (OSError, ValueError) as error:
        message = tr('Assistant collaboration: {error}', error=str(error))
        print(message, file=sys.stderr)
        subprocess.run(['notify-send', '--app-name=Eitr', message], check=False)
        return 1
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
