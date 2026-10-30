#!/usr/bin/env python3
"""Discover SDDM's current seat without changing sessions; switch only on request."""
import argparse
import configparser
from pathlib import Path
import shlex
import json
import os
import pwd
import subprocess
import xml.etree.ElementTree as ET

SERVICE = 'org.freedesktop.DisplayManager'
INTERFACE = SERVICE + '.Seat'


def bus(*arguments):
    return subprocess.run(['busctl', '--system', '--timeout=3', *arguments],
                          check=True, capture_output=True, text=True).stdout


def property_value(path, interface, name):
    result = shlex.split(bus('get-property', SERVICE, path, interface, name))
    if result[0] == 'ao' and int(result[1]) == len(result[2:]):
        return result[2:]
    if result[0] == 'b':
        return result[1] == 'true'
    raise ValueError('Unexpected D-Bus property signature')


def discover():
    seats = property_value('/org/freedesktop/DisplayManager', SERVICE, 'Seats')
    requested = os.environ.get('XDG_SEAT_PATH', '')
    seat = requested if requested in seats else seats[0] if len(seats) == 1 else ''
    if not seat:
        return ''
    interface = ET.fromstring(bus('--xml-interface', 'introspect', SERVICE, seat, INTERFACE))
    method = interface.find(".//method[@name='SwitchToGreeter']")
    if method is None or method.findall('arg'):
        return ''
    return seat if property_value(seat, INTERFACE, 'CanSwitch') is True else ''


def status():
    current = pwd.getpwuid(os.getuid())
    settings = configparser.ConfigParser(interpolation=None, strict=False)
    settings.read([*sorted(Path('/usr/lib/sddm/sddm.conf.d').glob('*.conf')),
                   *sorted(Path('/etc/sddm.conf.d').glob('*.conf')), Path('/etc/sddm.conf')])
    minimum = settings.getint('Users', 'MinimumUid', fallback=1000)
    maximum = settings.getint('Users', 'MaximumUid', fallback=60513)
    hidden = settings.get('Users', 'HideUsers', fallback='').split(',')
    shells = settings.get('Users', 'HideShells', fallback='').split(',')
    users = [user for user in pwd.getpwall()
             if minimum <= user.pw_uid <= maximum and user.pw_name not in hidden and user.pw_shell not in shells]
    seat = ''
    if len(users) > 1:
        try:
            seat = discover()
        except (OSError, subprocess.SubprocessError, ValueError, KeyError, ET.ParseError):
            pass
    return {'name': current.pw_gecos.split(',')[0] or current.pw_name,
            'available': bool(seat), 'seat': seat}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--switch', action='store_true')
    arguments = parser.parse_args()
    result = status()
    if arguments.switch:
        if not result['available']:
            raise SystemExit('Switch user is unavailable')
        bus('call', SERVICE, result['seat'], INTERFACE, 'SwitchToGreeter')
    else:
        print(json.dumps(result))


if __name__ == '__main__':
    main()
