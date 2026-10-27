"""Narrow root VPN actions. Secrets enter on stdin and never reach diagnostics."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from eitr_vpn import NAME, import_arguments, wireguard_summary

DIRECTORY = Path('/etc/wireguard')
NM_DIRECTORY = Path('/etc/NetworkManager/system-connections')


def run(arguments):
    result = subprocess.run(arguments, capture_output=True, text=True)
    if result.returncode:
        raise ValueError('VPN operation failed.')
    return result.stdout


def trusted_directory():
    return not DIRECTORY.is_symlink() and DIRECTORY.stat().st_uid == 0 and not DIRECTORY.stat().st_mode & 0o022


def import_nm_wireguard(path, name):
    import gi
    gi.require_version('NM', '1.0')
    from gi.repository import NM
    connection = NM.conn_wireguard_import(str(path))
    setting = connection.get_setting_connection()
    setting.set_property('id', name)
    setting.set_property('autoconnect', False)
    identifier = setting.get_uuid()
    keyfile = NM.keyfile_write(connection, NM.KeyfileHandlerFlags.NONE)
    data, _length = keyfile.to_data()
    directory = NM_DIRECTORY
    if directory.is_symlink() or directory.stat().st_uid != 0 or directory.stat().st_mode & 0o022:
        raise ValueError('Unsafe NetworkManager directory.')
    target = directory / ('eitr-' + identifier + '.nmconnection')
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(data)
    try:
        run(['nmcli', 'connection', 'load', str(target)])
    except ValueError:
        target.unlink()
        raise
    return identifier


def dispatch(action):
    payload = json.loads(sys.stdin.read(1024 * 1024 + 1))
    name = payload['name']
    if not NAME.fullmatch(name):
        raise ValueError('Invalid VPN name.')
    active = subprocess.run(['systemctl', 'is-active', '--quiet', 'NetworkManager.service'],
                            capture_output=True).returncode == 0
    if payload['backend'] != ('networkmanager' if active else 'wg-quick'):
        raise ValueError('Network backend changed; review again.')
    if action in ('up', 'down'):
        if active:
            connection_type = run(['nmcli', '-g', 'connection.type', 'connection', 'show', 'id', name]).strip()
            if connection_type not in ('wireguard', 'vpn'):
                raise ValueError('Only VPN connections are supported.')
            run(['nmcli', 'connection', action, 'id', name])
        else:
            path = DIRECTORY / (name + '.conf')
            if path.is_symlink() or not path.is_file() or path.stat().st_uid != 0:
                raise ValueError('Invalid VPN profile.')
            wireguard_summary(name, path.read_text())
            run(['systemctl', 'start' if action == 'up' else 'stop', 'wg-quick@' + name + '.service'])
        return
    if action != 'import':
        raise ValueError('Invalid VPN action.')
    content = payload['content']
    if len(content.encode()) > 1024 * 1024:
        raise ValueError('VPN configuration too large.')
    kind = payload['kind']
    if kind == 'wireguard':
        wireguard_summary(name, content)
    if active:
        with tempfile.TemporaryDirectory(prefix='eitr-vpn-') as temporary:
            path = Path(temporary) / (name + ('.conf' if kind == 'wireguard' else '.ovpn'))
            path.write_text(content)
            path.chmod(0o600)
            if kind == 'wireguard':
                identifier = import_nm_wireguard(path, name)
                if payload.get('connect') is True:
                    run(['nmcli', 'connection', 'up', 'uuid', identifier])
                return
            output = run(import_arguments(kind, path))
            identifiers = re.findall(r'\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b', output)
            if len(identifiers) != 1:
                raise ValueError('VPN import did not return an identifier.')
            identifier = identifiers[0]
            run(['nmcli', 'connection', 'modify', 'uuid', identifier, 'connection.id', name,
                 'connection.autoconnect', 'no'])
            if payload.get('connect') is True:
                run(['nmcli', 'connection', 'up', 'uuid', identifier])
    else:
        if kind != 'wireguard':
            raise ValueError('NetworkManager is required.')
        DIRECTORY.mkdir(mode=0o700, exist_ok=True)
        if not trusted_directory():
            raise ValueError('Unsafe WireGuard directory.')
        path = DIRECTORY / (name + '.conf')
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(content)
        if payload.get('connect') is True:
            run(['systemctl', 'start', 'wg-quick@' + name + '.service'])
