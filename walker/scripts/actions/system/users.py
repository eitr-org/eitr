#!/usr/bin/env python3
"""Collect a reviewed account request or list human accounts without changes."""
import eitr_bootstrap
from eitr_i18n import mark, tr
from eitr_users import human_users, valid_full_name, valid_password, valid_username
from eitr_wizard import Step, collect
from eitr_terminal import read_key
import argparse
import getpass
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


def manage(arguments):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['set-type', 'set-password', 'remove'])
    parser.add_argument('username')
    parser.add_argument('--account-type', choices=['standard', 'administrator'])
    parser.add_argument('--delete-home', action='store_true')
    args = parser.parse_args(arguments)
    if not valid_username(args.username):
        raise ValueError(tr('Invalid username'))
    if (args.action == 'set-type') != bool(args.account_type) or (args.delete_home and args.action != 'remove'):
        raise ValueError(tr('Invalid account request'))
    values = {'username': args.username}
    if args.action == 'set-type':
        values['account_type'] = args.account_type
        summary = tr('Change {username} to {account_type}.', username=args.username,
                     account_type=tr('Administrator') if args.account_type == 'administrator' else tr('Standard'))
    elif args.action == 'remove':
        values['delete_home'] = args.delete_home
        summary = tr('Remove {username}: {home}.', username=args.username,
                     home=tr('Delete home folder') if args.delete_home else tr('Keep home folder'))
    else:
        summary = tr('Set password for {username}.', username=args.username)
    print(summary)
    if args.action == 'set-password':
        print(tr('Their login keyring will keep its old password.'))
    print(tr('Press Enter to continue or Esc to cancel.'))
    if read_key() not in ('\r', '\n'):
        return
    if args.action == 'set-password':
        password = getpass.getpass(tr('New password') + ': ')
        repeated = getpass.getpass(tr('Repeat new password') + ': ')
        if password != repeated:
            raise ValueError(tr('The new passwords do not match.'))
        if not valid_password(password):
            raise ValueError(tr('Use at least 8 characters, without line breaks.'))
        values['password'] = password
    subprocess.run(['sudo', HELPER, 'user-' + args.action], input=json.dumps(values), text=True, check=True)


def main():
    if sys.argv[1:] == ['--entries']:
        print(json.dumps(entries()))
        return
    if sys.argv[1:]:
        manage(sys.argv[1:])
        return
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
