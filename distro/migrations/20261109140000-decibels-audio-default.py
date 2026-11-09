"""Decibels opens music files on desktops that have it but no working audio default.

New installations get it from the shipped mimeapps.list; existing ones keep any player
the person chose and only gain Decibels where the default is unset or points to an app
that is gone or cannot open files (GNOME Music, for example).
"""
import configparser
import os
from pathlib import Path
import subprocess

DECIBELS = 'org.gnome.Decibels.desktop'
AUDIO = ('audio/aac', 'audio/flac', 'audio/mp4', 'audio/mpeg', 'audio/ogg', 'audio/opus', 'audio/wav',
         'audio/x-flac', 'audio/x-m4a', 'audio/x-mp3', 'audio/x-opus+ogg', 'audio/x-vorbis+ogg', 'audio/x-wav')


def launcher(name):
    """The desktop file a launcher name refers to, searched like the desktop does."""
    roots = [Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share')]
    roots += [Path(folder) for folder in (os.environ.get('XDG_DATA_DIRS') or '/usr/local/share:/usr/share').split(':') if folder]
    return next((root / 'applications' / name for root in roots if (root / 'applications' / name).is_file()), None)


def opens_files(name):
    path = launcher(name) if name else None
    if path is None:
        return False
    parser = configparser.ConfigParser(interpolation=None, strict=False)
    try:
        parser.read(path, encoding='utf-8')
        return bool(parser['Desktop Entry'].get('MimeType', '').strip(';'))
    except (configparser.Error, KeyError, UnicodeError):
        return False


def saved_defaults():
    """The person's own choices; `xdg-mime query` would hide a missing app behind a fallback."""
    parser = configparser.ConfigParser(interpolation=None, strict=False, delimiters=('=',))
    parser.optionxform = str
    try:
        parser.read(Path(os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config') / 'mimeapps.list', encoding='utf-8')
    except (configparser.Error, UnicodeError):
        return None
    section = parser['Default Applications'] if parser.has_section('Default Applications') else {}
    return {mime: value.split(';')[0].strip() for mime, value in section.items()}


def main():
    defaults = saved_defaults()
    if defaults is None or launcher(DECIBELS) is None:
        return
    for mime in AUDIO:
        current = defaults.get(mime, '')
        if current != DECIBELS and not opens_files(current):
            subprocess.run(['xdg-mime', 'default', DECIBELS, mime], check=True)


if __name__ == '__main__':
    main()
