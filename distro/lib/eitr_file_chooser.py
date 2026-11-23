#!/usr/bin/env python3
"""The desktop portal's file chooser (xdg-desktop-portal-gtk on Eitr) for one local file."""
import argparse
import json
import os
from pathlib import Path

PORTAL = 'org.freedesktop.portal.Desktop'
PORTAL_PATH = '/org/freedesktop/portal/desktop'
TIMEOUT = 5000


def gio():
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib
    return Gio, GLib


def choose_file(title, label, mime, folder, libraries):
    """Ask the desktop portal's file chooser (xdg-desktop-portal-gtk on Eitr) for one local file.

    Waits for the person to pick or cancel, without a deadline. Returns {'path': None} when
    the chooser was cancelled."""
    Gio, GLib = libraries
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    token = f'eitr_chooser_{os.getpid()}'
    sender = bus.get_unique_name().lstrip(':').replace('.', '_')
    expected = f'{PORTAL_PATH}/request/{sender}/{token}'
    loop = GLib.MainLoop()
    outcome = {}

    def responded(_connection, _sender, _path, _interface, _signal, parameters):
        code, results = parameters.unpack()
        outcome.update(code=code, uris=list(results.get('uris', [])))
        loop.quit()

    def listen(handle):
        return bus.signal_subscribe(PORTAL, 'org.freedesktop.portal.Request', 'Response', handle,
                                    None, Gio.DBusSignalFlags.NONE,
                                    responded)

    subscription = listen(expected)
    options = {
        'handle_token': GLib.Variant('s', token),
        'modal': GLib.Variant('b', True),
        'multiple': GLib.Variant('b', False),
        'filters': GLib.Variant('a(sa(us))', [(label, [(1, mime)])]),
        'current_folder': GLib.Variant('ay', os.fsencode(str(folder)) + b'\0'),
    }
    try:
        handle = bus.call_sync(PORTAL, PORTAL_PATH, 'org.freedesktop.portal.FileChooser', 'OpenFile',
                               GLib.Variant('(ssa{sv})', ('', title, options)), GLib.VariantType.new('(o)'),
                               Gio.DBusCallFlags.NONE, TIMEOUT, None).unpack()[0]
        if handle != expected:
            bus.signal_unsubscribe(subscription)
            subscription = listen(handle)
        loop.run()
    finally:
        bus.signal_unsubscribe(subscription)
    if outcome.get('code') != 0 or not outcome.get('uris'):
        return {'path': None}
    path = Gio.File.new_for_uri(outcome['uris'][0]).get_path()
    if not path:
        raise ValueError('The chosen file is not a local file')
    return {'path': path}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    audio = commands.add_parser('audio', help='pick one audio file, starting in the home folder')
    audio.add_argument('title')
    audio.add_argument('label', help='name of the file filter')
    try:
        arguments = parser.parse_args(argv)
        result = choose_file(arguments.title, arguments.label, 'audio/*', Path.home(), gio())
        print(json.dumps({'ok': True, 'result': result}))
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
