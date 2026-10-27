#!/usr/bin/env python3
"""Collect a reviewed account request or list human accounts without changes."""
import eitr_bootstrap
from eitr_i18n import mark, tr
from eitr_users import human_users, valid_full_name, valid_password, valid_username
from eitr_wizard import Step, collect
import json
from pathlib import Path
import pwd
import subprocess
import sys

HELPER = '/usr/lib/eitr/eitr-system'


def available_username(value):
    if not valid_username(value):
        return False
    try:
        pwd.getpwnam(value)
    except KeyError:
        return not (Path('/home') / value).exists() and not (Path('/home') / value).is_symlink()
    return False


def steps():
    return [Step('username', mark('Username'), validator=available_username,
                 description=mark('Use lowercase letters, digits, underscores or hyphens; start with a letter or underscore. Maximum 32 characters.')),
            Step('full_name', mark('Full name'), optional=True, validator=valid_full_name,
                 description=mark('Optional display name.')),
            Step('account_type', mark('Account type'), default='standard',
                 options=[(mark('Standard'), 'standard'), (mark('Administrator'), 'administrator')],
                 description=mark('Administrators can use sudo. Standard accounts cannot.')),
            Step('password', mark('Password'), secret=True, password=True, validator=valid_password)]


def entries():
    return [{'Text': account.pw_name, 'Subtext': tr('User account') + ' · UID ' + str(account.pw_uid),
             'Icon': '󰀄', 'Actions': {}} for account in human_users()]


def main():
    if sys.argv[1:] == ['--entries']:
        print(json.dumps(entries()))
        return
    if sys.argv[1:]:
        raise ValueError('Unexpected argument')
    if not Path(HELPER).is_file():
        raise RuntimeError(tr('The root-owned Eitr helper is not installed; update the eitr-desktop package.'))
    values = collect(tr('Create User…'), steps())
    subprocess.run(['sudo', HELPER, 'user-create'], input=json.dumps(values), text=True, check=True)
    print(tr('Account created. Desktop setup runs at its first Hyprland login; shell setup may need internet access.'))


if __name__ == '__main__':
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        sys.exit(0)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
