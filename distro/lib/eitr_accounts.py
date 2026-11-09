"""Root account operations, accepting bounded requests only on stdin."""
import fcntl
import json
import os
from pathlib import Path
import subprocess

from eitr_i18n import tr
from eitr_users import human_users, is_administrator, valid_password, valid_username


def request_from(stream, fields):
    document = stream.read(32769)
    if len(document) > 32768:
        raise ValueError(tr('Account request is too large'))
    request = json.loads(document)
    if not isinstance(request, dict) or set(request) != {'username', *fields}:
        raise ValueError(tr('Invalid account request'))
    if not valid_username(request['username']):
        raise ValueError(tr('Invalid username'))
    return request


def target_user(username):
    account = next((account for account in human_users() if account.pw_name == username), None)
    if account is None:
        raise ValueError(tr('Only human accounts can be managed'))
    return account


def protect_last(account, message):
    if is_administrator(account) and not any(
            other.pw_name != account.pw_name and is_administrator(other) for other in human_users()):
        raise ValueError(message)


def ensure_logged_out(account, run):
    sessions = run(['loginctl', 'list-sessions', '--no-legend', '--no-pager'],
                   text=True, stdout=subprocess.PIPE, timeout=15).stdout
    for line in sessions.splitlines():
        fields = line.split()
        if len(fields) < 3 or not fields[1].isdigit():
            raise ValueError(tr('Cannot verify account login sessions'))
        if fields[1] == str(account.pw_uid):
            raise ValueError(tr('Account has an active login session'))


def apply(action, request, run, atomic):
    account = target_user(request['username'])
    username = account.pw_name
    sudoers = Path('/etc/sudoers.d') / ('eitr-user-' + username)
    if action == 'user-set-type':
        account_type = request['account_type']
        if account_type not in ('standard', 'administrator'):
            raise ValueError(tr('Invalid account type'))
        if account_type == 'administrator':
            policy = f'{username} ALL=(ALL) ALL\n'
            run(['visudo', '-cf', '-'], input=policy, text=True, stdout=subprocess.DEVNULL)
            # Membership comes last: a failed validation/write never grants wheel access.
            existed = sudoers.exists()
            atomic(sudoers, policy, mode=0o440, directory_mode=0o750)
            try:
                run(['usermod', '--append', '--groups', 'wheel', '--', username])
            except (OSError, subprocess.SubprocessError):
                if not existed:
                    sudoers.unlink(missing_ok=True)
                raise
        else:
            protect_last(account, tr('Cannot make the last administrator a standard account'))
            import grp
            wheel = grp.getgrnam('wheel')
            if account.pw_gid == wheel.gr_gid:
                raise ValueError(tr('Cannot demote an account with wheel as its primary group'))
            if username in wheel.gr_mem:
                run(['gpasswd', '--delete', username, 'wheel'])
            sudoers.unlink(missing_ok=True)
    elif action == 'user-set-password':
        if username == os.environ.get('SUDO_USER'):
            raise ValueError(tr('Use Change password for your own account'))
        if not valid_password(request['password']):
            raise ValueError(tr('Invalid password'))
        run(['chpasswd'], input=username + ':' + request['password'] + '\n', text=True)
    else:
        if type(request['delete_home']) is not bool:
            raise ValueError(tr('Invalid home folder choice'))
        if username == os.environ.get('SUDO_USER'):
            raise ValueError(tr('Cannot remove your own account'))
        protect_last(account, tr('Cannot remove the last administrator'))
        ensure_logged_out(account, run)
        run(['userdel', *(['--remove'] if request['delete_home'] else []), '--', username])
        sudoers.unlink(missing_ok=True)


def dispatch(action, stream, run, atomic):
    fields = {'user-set-type': {'account_type'}, 'user-set-password': {'password'},
              'user-remove': {'delete_home'}}
    if os.geteuid() != 0:
        raise ValueError(tr('Account management requires root'))
    request = request_from(stream, fields[action])
    # A shared lock protects last-administrator decisions across helper processes.
    with Path('/run/eitr-accounts.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        invoker = os.environ.get('SUDO_USER')
        if invoker and not is_administrator(target_user(invoker)):
            raise ValueError(tr('Only administrators can manage accounts'))
        apply(action, request, run, atomic)
