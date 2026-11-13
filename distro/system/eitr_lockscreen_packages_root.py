"""Allowlisted lockscreen transactions and one-time upgrade migration."""
import configparser
import json
import os
from pathlib import Path
import pwd
import subprocess
import tempfile

from eitr_choice_lists import LOCKSCREEN_DESIGNS
from eitr_lockscreen_packages import names

LOGIN = Path('/etc/sddm.conf.d/90-desktop-lockscreen.conf')
MARKER = Path('/var/lib/eitr/lockscreen-packages-migrated')
SAVED = Path('/var/lib/eitr/login-design-before-split')


def in_use():
    parser = configparser.ConfigParser()
    parser.read(LOGIN)
    theme = parser.get('Theme', 'Current', fallback='')
    result = {row['id'] for row in LOCKSCREEN_DESIGNS
              if theme == 'desktop-lockscreen-' + row['id'].replace('/', '-')}
    # Protect every account's selection; never execute or import user-owned code.
    for account in pwd.getpwall():
        home = Path(account.pw_dir)
        try:
            # Regular files only: a pipe or device placed there would block this root process.
            selected_path = home / '.config/lockscreen/selected'
            if not selected_path.is_file():
                continue
            selected = selected_path.read_text().strip()
            if selected.startswith('user:'):
                identifier = selected[5:]
                if not identifier or any(character not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for character in identifier):
                    continue
                manifest = home / '.local/share/eitr/lockscreens' / identifier / 'lockscreen.json'
                if not manifest.is_file():
                    continue
                selected = json.loads(manifest.read_text())['design']
            result.add(selected)
        except (OSError, ValueError, KeyError):
            continue
    return result


def install(packages):
    config = subprocess.check_output(['/usr/bin/pacman-conf'], text=True, timeout=30)
    lines, allowed, repositories = [], False, set()
    for line in config.splitlines():
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            allowed = section in {'options', 'eitr', 'eitr-testing'}
            if allowed and section != 'options':
                repositories.add(section)
        if allowed:
            lines.append(line)
    if '[options]' not in lines or not repositories:
        raise ValueError('No Eitr package repository is configured')
    with tempfile.TemporaryDirectory(prefix='eitr-lockscreens-') as directory:
        path = Path(directory) / 'pacman.conf'
        path.write_text('\n'.join(lines) + '\n')
        subprocess.run(['/usr/bin/pacman', '--config', str(path), '-S', '--needed', '--noconfirm', '--', *packages], check=True)


def migrate():
    if MARKER.exists():
        return
    install(names([row['id'] for row in LOCKSCREEN_DESIGNS if not row['builtin']]))
    if SAVED.exists():
        theme = SAVED.read_text().strip()
        design = next((row['id'] for row in LOCKSCREEN_DESIGNS
                       if theme == 'desktop-lockscreen-' + row['id'].replace('/', '-')), None)
        if design is not None:
            subprocess.run(['/usr/lib/eitr/desktop-login-select', design], check=True)
        SAVED.unlink()
    MARKER.parent.mkdir(parents=True, exist_ok=True)
    MARKER.touch(mode=0o644)


def dispatch(action, stream):
    if os.geteuid() != 0:
        raise ValueError('Lockscreen package management requires root')
    if action == 'migrate':
        migrate()
        return
    identifiers = json.loads(stream.read(4097))
    packages = names(identifiers)
    if action == 'install':
        install(packages)
    elif action == 'remove':
        if in_use().intersection(identifiers):
            raise ValueError('The current lockscreen cannot be removed')
        subprocess.run(['/usr/bin/pacman', '-R', '--noconfirm', '--', *packages], check=True)
    else:
        raise ValueError('Invalid lockscreen package action')
