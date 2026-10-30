#!/usr/bin/env python3
"""Read and set the power-profiles-daemon profile; laptops only."""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_battery import system_batteries

import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

POWER_SUPPLY = Path('/sys/class/power_supply')
PROFILES = ('power-saver', 'balanced', 'performance')
# `powerprofilesctl list` prints "* balanced:" for the active profile and
# "  performance:" for the others, each followed by indented details.
PROFILE_LINE = re.compile(r'^([* ]) ([a-z-]+):$')


def has_battery():
    return bool(system_batteries(POWER_SUPPLY))


def unavailable():
    return {'available': False, 'active': '', 'profiles': []}


def status():
    if not has_battery() or not shutil.which('powerprofilesctl'):
        return unavailable()
    try:
        listing = subprocess.run(['powerprofilesctl', 'list'], capture_output=True, text=True,
                                 timeout=5, check=True).stdout
    except (OSError, subprocess.SubprocessError):
        return unavailable()
    profiles, active = [], ''
    for line in listing.splitlines():
        match = PROFILE_LINE.match(line)
        if match and match.group(2) in PROFILES:
            profiles.append(match.group(2))
            if match.group(1) == '*':
                active = match.group(2)
    if not profiles:
        return unavailable()
    return {'available': True, 'active': active, 'profiles': [name for name in PROFILES if name in profiles]}


def set_profile(name):
    current = status()
    if name not in current['profiles']:
        raise ValueError(tr('Unsupported power profile: {name}', name=f'{name}'))
    subprocess.run(['powerprofilesctl', 'set', name], capture_output=True, text=True, timeout=5, check=True)
    return status()


def main(argv):
    if argv[1:] == ['status']:
        print(json.dumps(status()))
    elif len(argv) == 3 and argv[1] == 'set':
        print(json.dumps(set_profile(argv[2])))
    else:
        print('Usage: power-profile.py status | set power-saver|balanced|performance', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
