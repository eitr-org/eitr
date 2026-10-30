#!/usr/bin/env python3
"""Remote access terminal workflows; system mutations belong to eitr-system."""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_terminal import wait_for_escape
from eitr_paths import code, config, state
from eitr_app import app_command
import importlib.util
import json
import os
from pathlib import Path
import pwd
import re
import subprocess
import sys
import urllib.parse

HELPER = '/usr/lib/eitr/eitr-system'
SERVICE = 'eitr-sunshine.service'
# Written once remote control is granted. The grant itself lives in root's state,
# which this user cannot read; a stale note only starts sharing with closed ports.
GRANTED = state('eitr/remote-sharing-granted')


def run(command, **options):
    return subprocess.run(command, check=True, **options)


def start_service(verb):
    """Start or restart sharing; on failure show the service's own log, which holds the reason."""
    try:
        run(['systemctl', '--user', verb, SERVICE])
    except subprocess.CalledProcessError:
        log = subprocess.run(['journalctl', '--user', '-u', SERVICE, '--since', '-1min', '-n', '15',
                              '--no-pager', '-o', 'cat'], capture_output=True, text=True, check=False).stdout
        if sys.stdin.isatty():
            print(log, end='')
            raise RuntimeError(tr('Sharing could not start; the reason is above.')) from None
        # A toggle has no terminal: the notification carries the last line of the log.
        reason = next((line for line in reversed(log.splitlines()) if line.strip()), '')
        raise RuntimeError(tr('Sharing could not start: {reason}', reason=reason)) from None


def software():
    spec = importlib.util.spec_from_file_location('remote_software', code('walker/scripts/actions/install/software.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def root(action):
    path = Path(HELPER)
    if not path.is_file() or path.stat().st_uid != 0 or path.stat().st_mode & 0o022:
        raise RuntimeError(tr('The root-owned Eitr helper is not installed; update the eitr-desktop package.'))
    run(['sudo', HELPER, 'remote-' + action, pwd.getpwuid(os.getuid()).pw_name])


def confirm(message):
    return input(message + ' [y/N] ').strip().lower() in ('y', 'yes')


def open_page(url):
    # Detached and silent: the browser's own log would bury this terminal's questions.
    subprocess.Popen(app_command(['xdg-open', url]), stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, start_new_session=True)


def settings(pair=False):
    open_page('https://localhost:47990' + ('/pin' if pair else ''))


def host(action):
    if action == 'setup':
        for unit in ('sunshine.service', 'sunshine-kms.service'):
            if any(subprocess.run(['systemctl', '--user', state, '--quiet', unit], capture_output=True).returncode == 0
                   for state in ('is-active', 'is-enabled')):
                raise RuntimeError(tr('Stop and disable the existing Sunshine user service before using Eitr sharing. Its settings will be kept.'))
        if not Path('/usr/bin/sunshine').is_file():
            software().recipe('remote-access', 'sunshine')
        root('setup')
    elif action == 'start':
        # After the first start, the toggle just starts the service: its firewall
        # steps use the narrow no-password sudo rule, and the grant is remembered.
        if GRANTED.exists():
            start_service('start')
            return
        if not sys.stdin.isatty():
            reopen_in_terminal()
            return
        print(tr('Sharing hands over full control of this signed-in desktop. Only enable it on a trusted home network.'))
        print(tr('Set a Sunshine username and password in the local settings page before pairing any device.'))
        if not confirm(tr('Start sharing this PC?')):
            return
        start_service('start')
        settings()
        if not confirm(tr('Have you set Sunshine’s username and password in the browser?')):
            run(['systemctl', '--user', 'stop', SERVICE])
            return
        root('arm')
        GRANTED.parent.mkdir(parents=True, exist_ok=True)
        GRANTED.touch()
        start_service('restart')
    elif action == 'stop':
        run(['systemctl', '--user', 'disable', '--now', SERVICE])
        root('close')
    elif action == 'login':
        # The toggle or menu row is the confirmation.
        run(['systemctl', '--user', 'enable', SERVICE])
    elif action == 'no-login':
        run(['systemctl', '--user', 'disable', SERVICE])
    elif action == 'undo':
        if confirm(tr('Stop sharing and restore the original system permissions?')):
            run(['systemctl', '--user', 'disable', '--now', SERVICE])
            root('undo')
            GRANTED.unlink(missing_ok=True)
    elif action in ('settings', 'pair'):
        if action == 'pair':
            if not confirm(tr('Have you set Sunshine’s username and password in the browser?')):
                settings()
                return
            print(tr('Set Sunshine’s password first. Enter the PIN shown by Moonlight only for a device you trust.'))
        settings(action == 'pair')
    elif action == 'status':
        subprocess.run(['systemctl', '--user', 'status', '--no-pager', SERVICE], check=False)


def launch_host():
    """Security overrides cannot be relaxed in the web UI; retain the user's config."""
    os.execvp('sunshine', ['sunshine', 'origin_web_ui_allowed=pc', 'upnp=off', 'port=47989', 'capture=kms'])


def auth_url(line):
    for value in re.findall(r'https://[^\s]+', line):
        parsed = urllib.parse.urlsplit(value)
        if parsed.hostname in ('login.tailscale.com', 'controlplane.tailscale.com') and not parsed.username and parsed.port in (None, 443):
            return value
    return None


def user():
    return pwd.getpwuid(os.getuid()).pw_name


def is_operator():
    """Away Access Setup makes this user Tailscale's operator, so it switches without sudo."""
    result = subprocess.run(['tailscale', 'debug', 'prefs'], capture_output=True, text=True)
    try:
        return result.returncode == 0 and json.loads(result.stdout).get('OperatorUser') == user()
    except ValueError:
        return False


def reopen_in_terminal():
    """Toggles run without a terminal; a step that needs one (a password, a sign-in)
    starts this same action again in a task terminal."""
    subprocess.Popen([str(code('walker/bin/menu-path/kitty')), '-e', 'python3',
                      str(code('walker/scripts/actions/task-terminal.py')), 'python3',
                      str(Path(__file__).resolve()), *sys.argv[1:]], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ensure_operator():
    """Make this user the operator once, with the administrator password; True when it already is.
    Without a terminal for that password, the step opens in one."""
    if is_operator():
        return True
    if not sys.stdin.isatty():
        reopen_in_terminal()
        return False
    print(tr('Tailscale needs your administrator password once to let this account switch it.'))
    run(['sudo', 'tailscale', 'set', '--operator=' + user()])
    return True


def login():
    # Tailscale can wait for browser authentication: stream its URL immediately.
    # login resets every setting it is not given, so the operator is passed along.
    with subprocess.Popen(['tailscale', 'login', '--operator=' + user()], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, bufsize=1) as process:
        opened = set()
        for line in process.stdout:
            print(line, end='', flush=True)
            url = auth_url(line)
            if url and url not in opened:
                open_page(url)
                opened.add(url)
        if process.wait():
            raise RuntimeError(tr('Tailscale sign-in failed. Try again from Access This PC Remotely.'))


def status():
    result = run(['tailscale', 'status', '--json'], capture_output=True, text=True)
    data = json.loads(result.stdout)
    print(tr('Tailscale state: {state}', state=data.get('BackendState', 'Unknown')))
    print(tr('This PC: {addresses}', addresses=', '.join(data.get('TailscaleIPs', [])) or tr('No Tailscale address')))
    for peer in (data.get('Peer') or {}).values():
        if not peer.get('Online'):
            continue
        name = peer.get('HostName', '')
        path = (tr('Direct') if peer.get('CurAddr') else tr('Relayed') if peer.get('Relay') else tr('Idle; ping to check')) if peer.get('Active') else tr('Idle; ping to check')
        print(f'{name}: {path}')
    if data.get('BackendState') == 'NeedsLogin':
        print(tr('Choose Sign In to open the browser.'))


def tailscale_control(action):
    if not ensure_operator():
        return
    # up also needs the operator named, or it refuses to drop the non-default setting.
    flags = ['--operator=' + user()] if action == 'up' else []
    result = subprocess.run(['tailscale', action, *flags], capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or tr('Tailscale could not change state.'))


def away(action, peer=None):
    if action == 'setup':
        software().recipe('remote-access', 'tailscale')
        root('tailscale')
    elif action == 'undo':
        root('tailscale-undo')
    elif action == 'login':
        if ensure_operator():
            login()
    elif action == 'connect':
        data = json.loads(run(['tailscale', 'status', '--json'], capture_output=True, text=True).stdout)
        if data.get('BackendState') == 'NeedsLogin':
            if not sys.stdin.isatty():
                reopen_in_terminal()
                return
            if not ensure_operator():
                return
            login()
        tailscale_control('up')
    elif action == 'disconnect':
        tailscale_control('down')
    elif action == 'status':
        status()
    elif action == 'ping':
        peer = peer or input(tr('Peer Tailscale address or name: ')).strip()
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]{0,252}', peer):
            raise ValueError(tr('Invalid peer address.'))
        run(['tailscale', 'ping', '--c', '3', '--', peer])


# Turning remote access off always works, even when a policy disables it.
STOPPING = {('host', 'stop'), ('host', 'no-login'), ('host', 'undo'), ('away', 'disconnect'), ('away', 'undo')}


def main(arguments):
    if tuple(arguments[:2]) not in STOPPING:
        from eitr_policy import require
        require('remote_access')
    if arguments == ['serve']:
        launch_host()
    elif len(arguments) == 2 and arguments[0] == 'host':
        if arguments[1] not in ('setup', 'start', 'stop', 'login', 'no-login', 'undo', 'settings', 'pair', 'status'):
            raise ValueError('Unknown sharing action')
        host(arguments[1])
    elif len(arguments) == 2 and arguments[0] == 'away':
        if arguments[1] not in ('setup', 'undo', 'login', 'connect', 'disconnect', 'status', 'ping'):
            raise ValueError('Unknown away-access action')
        away(arguments[1])
    else:
        raise ValueError('Expected host or away and an action')
    if len(arguments) == 2 and arguments[1] == 'status':
        wait_for_escape()


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        subprocess.run(['notify-send', tr('Remote Access'), str(error)], check=False)
        raise SystemExit(str(error))
