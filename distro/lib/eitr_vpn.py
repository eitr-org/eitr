"""VPN validation shared by the review screen and privileged importer."""
import re

NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,14}\Z')


def wireguard_summary(name, content):
    if not NAME.fullmatch(name):
        raise ValueError('Use a profile name of 1–15 letters, digits, underscores or hyphens.')
    section = None
    peers = 0
    endpoints = []
    allowed = {'Interface': {'PrivateKey', 'Address', 'DNS', 'ListenPort', 'MTU', 'Table', 'FwMark'},
               'Peer': {'PublicKey', 'PresharedKey', 'AllowedIPs', 'Endpoint', 'PersistentKeepalive'}}
    for raw in content.splitlines():
        line = raw.split('#', 1)[0].strip()
        if not line:
            continue
        if line in ('[Interface]', '[Peer]'):
            section = line[1:-1]
            peers += section == 'Peer'
            continue
        key, separator, value = line.partition('=')
        if not separator or section not in allowed or key.strip() not in allowed[section]:
            raise ValueError('Unsupported WireGuard configuration; executable hooks are not allowed.')
        if key.strip() == 'Endpoint':
            endpoint = value.strip()
            if not re.fullmatch(r'(?:[A-Za-z0-9._-]{1,253}|\[[0-9A-Fa-f:]+\]):[0-9]{1,5}', endpoint) or not 1 <= int(endpoint.rsplit(':', 1)[1]) <= 65535:
                raise ValueError('Invalid WireGuard endpoint.')
            endpoints.append(endpoint)
    if '[Interface]' not in content or not peers:
        raise ValueError('A WireGuard interface and at least one peer are required.')
    return f'{name} · {", ".join(endpoints) or "—"} · {peers}'


def import_arguments(kind, filename):
    if kind not in ('wireguard', 'openvpn', 'openconnect'):
        raise ValueError('Unsupported VPN format.')
    return ['nmcli', 'connection', 'import', 'type', kind, 'file', str(filename)]
