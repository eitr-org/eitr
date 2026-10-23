#!/usr/bin/env python3
"""Open an assistant login URL privately in the default browser when supported."""
import configparser
import os
from pathlib import Path
import shlex
import subprocess
import sys


def browser_command(url):
    if not url.startswith(('https://', 'http://')):
        raise ValueError('Expected a login URL')
    result = subprocess.run(['xdg-settings', 'get', 'default-web-browser'],
                            capture_output=True, text=True, check=False)
    desktop = result.stdout.strip()
    if desktop and Path(desktop).name == desktop:
        roots = [Path(os.environ.get('XDG_DATA_HOME') or Path.home() / '.local/share'),
                 *[Path(directory) for directory in os.environ.get('XDG_DATA_DIRS', '/usr/local/share:/usr/share').split(':')]]
        for root in roots:
            parser = configparser.ConfigParser(interpolation=None)
            parser.read(root / 'applications' / desktop)
            command = shlex.split(parser.get('Desktop Entry', 'Exec', fallback=''))
            if not command:
                continue
            browser = desktop.lower() + ' ' + ' '.join(command).lower()
            flag = ('--private-window' if 'firefox' in browser else '--inprivate' if 'edge' in browser
                    else '--incognito' if any(name in browser for name in ('chrome', 'chromium', 'brave', 'vivaldi')) else None)
            if flag:
                return [command[0], *[argument for argument in command[1:] if '%' not in argument and not argument.startswith('@@')], flag, url]
    return ['xdg-open', url]


def open_private(url):
    environment = dict(os.environ)
    # xdg-open can consult BROWSER in its fallback path; avoid calling ourselves.
    environment.pop('BROWSER', None)
    return subprocess.run(browser_command(url), env=environment, check=False).returncode


if __name__ == '__main__':
    sys.exit(open_private(sys.argv[-1]))
