#!/usr/bin/env python3
"""The current user's standard profile picture, and the system file chooser that picks one."""
import argparse
import json
import math
import os
from pathlib import Path
import pwd
import tempfile

import eitr_paths

FORMATS = {'PNG', 'JPEG', 'WEBP', 'GIF', 'BMP'}
SERVICE = 'org.freedesktop.Accounts'
TIMEOUT = 5000
LARGEST_SIDE = 12000
PREVIEW_SIDE = 1024
PORTAL = 'org.freedesktop.portal.Desktop'
PORTAL_PATH = '/org/freedesktop/portal/desktop'


def imaging():
    """Pillow, imported only when a picture is read: status() stays fast and dependency-free."""
    from PIL import Image, ImageOps, UnidentifiedImageError
    Image.MAX_IMAGE_PIXELS = LARGEST_SIDE * LARGEST_SIDE
    return Image, ImageOps, UnidentifiedImageError


def gio():
    import gi
    gi.require_version('Gio', '2.0')
    from gi.repository import Gio, GLib
    return Gio, GLib


def account():
    Gio, GLib = gio()
    bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
    user = pwd.getpwuid(os.getuid()).pw_name
    path = bus.call_sync(SERVICE, '/org/freedesktop/Accounts', SERVICE, 'FindUserByName',
                         GLib.Variant('(s)', (user,)), GLib.VariantType.new('(o)'),
                         Gio.DBusCallFlags.NONE, TIMEOUT, None).unpack()[0]
    return bus, path


def set_icon(filename):
    Gio, GLib = gio()
    bus, path = account()
    try:
        bus.call_sync(SERVICE, path, SERVICE + '.User', 'SetIconFile',
                      GLib.Variant('(s)', (filename,)), None,
                      Gio.DBusCallFlags.NONE, TIMEOUT, None)
    except Exception as error:
        raise RuntimeError(f'Login screen picture could not be updated: {error}') from error


def readable(filename):
    if not filename:
        return False
    path = Path(filename)
    return path.is_file() and os.access(path, os.R_OK)


def status():
    current = pwd.getpwuid(os.getuid())
    name = current.pw_gecos.split(',')[0].strip() or current.pw_name
    filename = None
    try:
        Gio, GLib = gio()
        bus, path = account()
        value = bus.call_sync(SERVICE, path, 'org.freedesktop.DBus.Properties', 'Get',
                              GLib.Variant('(ss)', (SERVICE + '.User', 'IconFile')),
                              GLib.VariantType.new('(v)'), Gio.DBusCallFlags.NONE, TIMEOUT, None).unpack()[0]
        if readable(value):
            filename = str(value)
    except Exception:
        pass
    face = Path.home() / '.face'
    if filename is None and readable(face):
        filename = str(face)
    return {'path': filename, 'initial': name[0].upper(), 'name': name}


def load_image(source):
    Image, ImageOps, UnidentifiedImageError = imaging()
    path = Path(source)
    if not path.is_file() or path.stat().st_size > 40 * 1024 * 1024:
        raise ValueError('Choose an image smaller than 40 MB')
    try:
        with Image.open(path) as image:
            if image.format not in FORMATS or max(image.size) > LARGEST_SIDE:
                raise ValueError(f'Choose a PNG, JPEG, WebP, GIF or BMP up to {LARGEST_SIDE} pixels per side')
            image.seek(0)
            return ImageOps.exif_transpose(image).convert('RGBA')
    except (UnidentifiedImageError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError('Invalid or oversized image') from error


def preview(source):
    """A small upright copy for the crop editor, and the sizes that map its crop back to the original."""
    Image = imaging()[0]
    image = load_image(source)
    width, height = image.size
    image.thumbnail((PREVIEW_SIDE, PREVIEW_SIDE), Image.Resampling.LANCZOS)
    target = eitr_paths.cache('eitr/avatar-preview.png')
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.avatar-preview-', dir=target.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            image.save(output, format='PNG')
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return {'path': str(Path(source).resolve()), 'preview': str(target), 'version': target.stat().st_mtime_ns,
            'width': width, 'height': height, 'previewWidth': image.width, 'previewHeight': image.height}


def crop_box(width, height, x=None, y=None, size=None):
    if size is None:
        size = min(width, height)
        x, y = (width - size) / 2, (height - size) / 2
    if any(value is None or not math.isfinite(value) for value in (x, y, size)) or size <= 0:
        raise ValueError('Invalid crop')
    size = min(size, width, height)
    x, y = max(0, min(x, width - size)), max(0, min(y, height - size))
    return x, y, x + size, y + size


def save(source, x=None, y=None, size=None):
    Image = imaging()[0]
    image = load_image(source)
    cropped = image.crop(crop_box(*image.size, x, y, size)).resize((512, 512), Image.Resampling.LANCZOS)
    clean = Image.new('RGBA', (512, 512))
    clean.paste(cropped)
    face = Path.home() / '.face'
    descriptor, temporary = tempfile.mkstemp(prefix='.face-', dir=face.parent)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            os.fchmod(output.fileno(), 0o644)
            clean.save(output, format='PNG')
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, face)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    try:
        set_icon(str(face))
    except Exception as error:
        raise RuntimeError(f'Picture saved for the lockscreen; login screen update failed: {error}') from error
    return status()


def remove():
    try:
        set_icon('')
    except Exception as error:
        raise RuntimeError(f'Picture retained; login screen update failed: {error}') from error
    (Path.home() / '.face').unlink(missing_ok=True)
    return status()


def pictures_folder():
    """The XDG Pictures folder when it exists, else the home folder."""
    try:
        GLib = gio()[1]
        folder = GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES)
    except (ImportError, ValueError, AttributeError):
        folder = None
    folder = Path(folder) if folder else Path.home() / 'Pictures'
    return folder if folder.is_dir() else Path.home()


def choose(title='Choose a picture'):
    """Ask the desktop portal's file chooser (xdg-desktop-portal-gtk on Eitr) for one image.

    Waits for the person to pick or cancel, without a deadline. Returns {'path': None} when
    the chooser was cancelled."""
    Gio, GLib = gio()
    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    token = f'eitr_avatar_{os.getpid()}'
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
        'filters': GLib.Variant('a(sa(us))', [('Images', [(1, 'image/*')])]),
        'current_folder': GLib.Variant('ay', os.fsencode(str(pictures_folder())) + b'\0'),
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
        raise ValueError('The chosen picture is not a local file')
    return {'path': path}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('status', 'remove'):
        commands.add_parser(name)
    commands.add_parser('choose').add_argument('title', nargs='?', default='Choose a picture')
    commands.add_parser('preview').add_argument('file')
    save_parser = commands.add_parser('save')
    save_parser.add_argument('file')
    save_parser.add_argument('crop', nargs='*', type=float)
    try:
        arguments = parser.parse_args(argv)
        if arguments.command == 'save':
            if len(arguments.crop) not in (0, 3):
                raise ValueError('Expected X Y SIZE')
            result = save(arguments.file, *arguments.crop)
        elif arguments.command == 'choose':
            result = choose(arguments.title)
        elif arguments.command == 'preview':
            result = preview(arguments.file)
        else:
            result = globals()[arguments.command]()
        print(json.dumps({'ok': True, 'result': result}))
        return 0
    except Exception as error:
        print(json.dumps({'ok': False, 'error': str(error)}))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
