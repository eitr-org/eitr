"""Shared account validation and deferred desktop initialization."""
import fcntl
import os
from pathlib import Path
import pwd
import re
import subprocess


def valid_username(value):
    return isinstance(value, str) and value != "root" and bool(re.fullmatch(r"[a-z_][a-z0-9_-]{0,31}", value))


def valid_full_name(value):
    return isinstance(value, str) and len(value) <= 256 and all(character.isprintable() and character not in ":," for character in value)


def valid_password(value):
    return isinstance(value, str) and 8 <= len(value) <= 4096 and not any(character in value for character in "\n\r\0")


def human_users():
    return sorted((account for account in pwd.getpwall() if 1000 <= account.pw_uid < 65534),
                  key=lambda account: account.pw_name.casefold())


def seed_first_login():
    if os.geteuid() == 0:
        raise ValueError("Desktop initialization must run as the account owner")
    home = Path(pwd.getpwuid(os.getuid()).pw_dir)
    if Path.home() != home:
        raise ValueError("HOME does not match the account")
    pending = home / '.local/state/eitr/seed-pending'
    if not pending.exists():
        return
    with pending.open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if not pending.exists():
            return
        environment = dict(os.environ, HOME=str(home), EITR_NO_SESSION='1')
        for name in tuple(environment):
            if name.startswith(('XDG_', 'EITR_')):
                environment.pop(name)
        environment['EITR_NO_SESSION'] = '1'
        subprocess.run(['eitr-config', 'adopt-layout', '--apply'], env=environment, check=True)
        subprocess.run(['bash', '/usr/share/eitr/distro/install.sh', '--seed-user'],
                       env=environment, check=True)
        pending.unlink()


if __name__ == '__main__':
    seed_first_login()
