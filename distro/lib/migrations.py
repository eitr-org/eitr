"""Run each shipped settings migration once per user, in order, at login."""
import os
from pathlib import Path
import subprocess
import sys

from eitr_paths import code, state

NAME_LENGTH = 14  # YYYYMMDDHHMMSS, then -description.py


def shipped():
    directory = code('migrations')
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob('*.py')
                  if path.name[:NAME_LENGTH].isdigit() and path.name[NAME_LENGTH] == '-')


def marker(path):
    return state('eitr/migrations') / path.name


def mark_all():
    """Fresh installs and adopted homes already have the current settings shape."""
    for path in shipped():
        marker(path).parent.mkdir(parents=True, exist_ok=True)
        marker(path).touch()


def run_pending():
    """Stop at the first failure so later migrations never see a half-migrated state."""
    applied = []
    for path in shipped():
        if marker(path).exists():
            continue
        library = str(Path(__file__).resolve().parent)
        environment = dict(os.environ, PYTHONPATH=library + os.pathsep + os.environ.get('PYTHONPATH', ''))
        result = subprocess.run([sys.executable, str(path)], env=environment, check=False,
                                capture_output=True, text=True)
        log = state('eitr/migrations.log')
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a') as output:
            output.write(f'{path.name}: exit {result.returncode}\n{result.stdout}{result.stderr}')
        if result.returncode:
            subprocess.run(['notify-send', '-u', 'critical', 'EITR settings update failed',
                            f'{path.name} will retry at the next login. Details: {log}'], check=False)
            break
        marker(path).parent.mkdir(parents=True, exist_ok=True)
        marker(path).touch()
        applied.append(path.name)
    return applied


if __name__ == '__main__':
    if sys.argv[1:] == ['--mark-all']:
        mark_all()
    elif sys.argv[1:] == []:
        print('\n'.join(run_pending()))
    else:
        raise SystemExit('Usage: migrations.py [--mark-all]')
