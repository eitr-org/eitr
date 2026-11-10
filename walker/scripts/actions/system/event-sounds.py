#!/usr/bin/env python3
"""Optional event sounds for Walker: get KEY prints on/off; set KEY on|off saves it.

The desktop bar's EventSounds service watches eitr/sounds.json and plays nothing
for a key that is not true, so a change here applies without restarting the bar.
"""
import eitr_bootstrap  # noqa: F401
import sys
from eitr_paths import config, read_settings, write_settings

SETTINGS = config('eitr/sounds.json')
KEYS = ('notifications', 'charger')


def enabled(key):
    return read_settings(SETTINGS).get(key) is True


def main(arguments):
    if len(arguments) == 2 and arguments[0] == 'get' and arguments[1] in KEYS:
        print('on' if enabled(arguments[1]) else 'off')
        return 0
    if len(arguments) == 3 and arguments[0] == 'set' and arguments[1] in KEYS and arguments[2] in ('on', 'off'):
        write_settings(SETTINGS, {arguments[1]: arguments[2] == 'on'})
        return 0
    print('Usage: event-sounds.py get notifications|charger | set notifications|charger on|off', file=sys.stderr)
    return 2


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except (OSError, ValueError) as error:
        sys.exit(str(error))
