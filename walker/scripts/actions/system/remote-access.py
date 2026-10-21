#!/usr/bin/env python3
"""Remote access terminal workflows; system mutations belong to eitr-system."""
import eitr_bootstrap
from eitr_i18n import tr
from eitr_paths import code, config
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


def run(command, **options):
    return subprocess.run(command, check=True, **options)


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


def settings(pair=False):
    run(['xdg-open', 'https://localhost:47990' + ('/pin' if pair else '')])


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
        print(tr('Sharing hands over full control of this signed-in desktop. Only enable it on a trusted home network.'))
        print(tr('Set a Sunshine username and password in the local settings page before pairing any device.'))
        if not confirm(tr('Start sharing this PC?')):
            return
        run(['systemctl', '--user', 'start', SERVICE])
        settings()
        if not confirm(tr('Have you set Sunshine’s username and password in the browser?')):
            run(['systemctl', '--user', 'stop', SERVICE])
            return
        root('arm')
        run(['systemctl', '--user', 'restart', SERVICE])
    elif action == 'stop':
        run(['systemctl', '--user', 'disable', '--now', SERVICE])
        root('close')
    elif action == 'login':
        if confirm(tr('Start sharing automatically at login? This grants remote desktop control whenever you sign in.')):
            run(['systemctl', '--user', 'enable', SERVICE])
    elif action == 'no-login':
        run(['systemctl', '--user', 'disable', SERVICE])
    elif action == 'undo':
        if confirm(tr('Stop sharing and restore the original system permissions?')):
            run(['systemctl', '--user', 'disable', '--now', SERVICE])
            root('undo')
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


def login():
    # Tailscale can wait for browser authentication: stream its URL immediately.
    with subprocess.Popen(['sudo', 'tailscale', 'login'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, bufsize=1) as process:
        opened = set()
        for line in process.stdout:
            print(line, end='', flush=True)
            url = auth_url(line)
            if url and url not in opened:
                run(['xdg-open', url])
                opened.add(url)
        if process.wait():
            raise RuntimeError(tr('Tailscale sign-in failed. Try again from Access away from home.'))


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


def away(action, peer=None):
    if action == 'setup':
        software().recipe('remote-access', 'tailscale')
        root('tailscale')
    elif action == 'undo':
        root('tailscale-undo')
    elif action == 'login':
        login()
    elif action == 'connect':
        data = json.loads(run(['tailscale', 'status', '--json'], capture_output=True, text=True).stdout)
        if data.get('BackendState') == 'NeedsLogin':
            login()
        run(['sudo', 'tailscale', 'up'])
    elif action == 'disconnect':
        run(['sudo', 'tailscale', 'down'])
    elif action == 'status':
        status()
    elif action == 'ping':
        peer = peer or input(tr('Peer Tailscale address or name: ')).strip()
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:-]{0,252}', peer):
            raise ValueError(tr('Invalid peer address.'))
        run(['tailscale', 'ping', '--c', '3', '--', peer])


def main(arguments):
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


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        subprocess.run(['notify-send', tr('Remote Access'), str(error)], check=False)
        raise SystemExit(str(error))
