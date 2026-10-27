#!/usr/bin/env python3
"""Reviewed VPN installation and import; never display configuration contents."""
import json
from pathlib import Path
import subprocess
import sys

import software
from eitr_i18n import tr
from eitr_vpn import NAME, wireguard_summary
from eitr_terminal import read_key
from eitr_wizard import collect, Step


def networkmanager_active():
    return subprocess.run(['systemctl', 'is-active', '--quiet', 'NetworkManager.service'],
                          capture_output=True).returncode == 0


def main(kind):
    active = networkmanager_active()
    if kind == 'networkmanager' and not active:
        print(tr('VPN profiles need NetworkManager. Choose it in System > Connectivity > Network Backend, then reboot.'))
        print(tr('Enter: open Network Backend · Esc: close'), flush=True)
        if read_key() in ('\r', '\n'):
            subprocess.run([str(software.WALKER), '-m', 'menus:network-backend'], check=True)
        return
    item = software.catalog()['vpn'][kind]
    if not software.installed(item):
        software.install('pacman', item['packages'])
    label = tr('Import a WireGuard configuration…') if kind == 'wireguard' else tr('Import a VPN file…')
    steps = [Step('action', tr('Action'), options=[(label, 'import'), (tr('Connect'), 'up'),
                    (tr('Disconnect'), 'down')]), Step('name', tr('Name'), validator=lambda profile_name: bool(NAME.fullmatch(profile_name)))]
    if kind == 'networkmanager':
        steps.append(Step('format', tr('Format'), default='openvpn',
                     options=[('OpenVPN', 'openvpn'), ('OpenConnect', 'openconnect')]))
    choice = collect(label, steps)
    if choice['action'] != 'import':
        payload = {'name': choice['name'], 'backend': 'networkmanager' if active else 'wg-quick'}
        invoke('vpn-' + choice['action'], payload)
        return
    answer = collect(label, [Step('file', tr('Configuration file'), description=tr('Enter the full path to the configuration file.'))])
    path = Path(answer['file']).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size > 1024 * 1024:
        raise ValueError('Select a regular VPN configuration smaller than 1 MiB.')
    with path.open() as stream:
        content = stream.read(1024 * 1024 + 1)
    if len(content.encode()) > 1024 * 1024:
        raise ValueError('VPN configuration is too large.')
    name = choice['name']
    if kind == 'wireguard':
        if path.suffix != '.conf':
            raise ValueError('Select a .conf file.')
        summary = wireguard_summary(name, content)
        protocol = 'wireguard'
    else:
        protocol = choice['format']
        summary = name + ' · ' + protocol
    reviewed = collect(label, [Step('profile', tr('Profile'), options=[(summary, 'accept')]),
        Step('connect', tr('Connect after import'), default=False,
             options=[(tr('No'), False), (tr('Yes'), True)])])
    invoke('vpn-import', {'name': name, 'kind': protocol, 'content': content,
           'backend': 'networkmanager' if active else 'wg-quick', 'connect': reviewed['connect']})


def invoke(action, payload):
    result = subprocess.run(['sudo', '/usr/lib/eitr/eitr-system', action],
                            input=json.dumps(payload), text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError(tr('VPN operation failed. Configuration details are hidden.'))


if __name__ == '__main__':
    try:
        main(sys.argv[1])
    except (KeyboardInterrupt, software.InstallCancelled):
        pass
    except ValueError as error:
        # Local validation messages name the problem, never configuration contents.
        print(str(error), file=sys.stderr)
        sys.exit(1)
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print(tr('VPN operation failed. Configuration details are hidden.'), file=sys.stderr)
        sys.exit(1)
