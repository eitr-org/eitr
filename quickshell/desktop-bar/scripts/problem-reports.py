#!/usr/bin/env python3
"""The welcome's crash-notification switch shares the Control Center preference."""
import eitr_bootstrap
from eitr_paths import config, state
from eitr_crashes import settings, set_enabled
import json
import sys


def status():
    return {'offer': settings()['enabled'],
            'asked': config('eitr/crash-help.json').is_file() or state('eitr/problem-reports.json').is_file()}


def choose(answer):
    set_enabled(answer == 'on')
    return status()


def main(argv):
    if argv == ['status']:
        result = status()
    elif len(argv) == 2 and argv[0] == 'set' and argv[1] in ('on', 'off'):
        result = choose(argv[1])
    else:
        return 2
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
