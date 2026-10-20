#!/usr/bin/python3 -I
"""Privileged selector: accepts only IDs in the root-owned installed manifest.

  desktop-login-select DESIGN        use that login design
  desktop-login-select --wallpaper   store the JPEG on stdin for the Theme Wallpaper
                                     design (the session prepares it; this only
                                     checks it is a JPEG and copies it)
"""
import sys
sys.path.insert(0, "/usr/share/eitr/lib")
from eitr_i18n import tr
import json
import os
from pathlib import Path
import sys
import tempfile

MANIFEST = Path('/usr/share/eitr/lockscreen-designs.json')
CONFIG = Path('/etc/sddm.conf.d/90-desktop-lockscreen.conf')
WALLPAPER = Path('/var/lib/eitr/login-wallpaper.jpg')
WALLPAPER_LIMIT = 25 * 1024 * 1024


def store_wallpaper():
    data = sys.stdin.buffer.read(WALLPAPER_LIMIT + 1)
    if len(data) > WALLPAPER_LIMIT or not data.startswith(b'\xff\xd8\xff') or not data.rstrip(b'\0').endswith(b'\xff\xd9'):
        raise SystemExit(tr('The login wallpaper must be a JPEG under 25 MB'))
    WALLPAPER.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.login-wallpaper-', dir=WALLPAPER.parent)
    try:
        with os.fdopen(fd, 'wb') as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), 0o644)
        os.replace(temporary, WALLPAPER)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if os.geteuid() != 0 or len(sys.argv) != 2:
        raise SystemExit('Usage: desktop-login-select DESIGN|--wallpaper (requires root)')
    if sys.argv[1] == '--wallpaper':
        store_wallpaper()
        return
    designs = json.loads(MANIFEST.read_text())
    theme = designs.get(sys.argv[1])
    if not isinstance(theme, str) or not theme.startswith('desktop-lockscreen-') or any(
        character not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in theme
    ):
        raise SystemExit('Unknown installed login design')
    if not (Path('/usr/share/sddm/themes') / theme / 'Main.qml').is_file():
        raise SystemExit(tr('Login design is not installed'))
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.desktop-lockscreen-', dir=CONFIG.parent)
    try:
        with os.fdopen(fd, 'w') as output:
            output.write('[Theme]\nCurrent=' + theme + '\n')
            output.flush()
            os.fsync(output.fileno())
            os.fchmod(output.fileno(), 0o644)
        os.replace(temporary, CONFIG)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


if __name__ == '__main__':
    main()
