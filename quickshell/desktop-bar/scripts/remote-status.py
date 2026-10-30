#!/usr/bin/env python3
"""Read local remote-access status and expose the menus' existing actions."""
import eitr_bootstrap
from eitr_i18n import tr, table
from eitr_menu import rows
import json
import shutil
import subprocess
import sys


def query(arguments):
    return subprocess.run(arguments, capture_output=True, text=True, timeout=3, check=False)


def menu_actions(menu):
    messages = table('menus')
    setup = menu + '-setup'
    sources = [(menu, row) for row in rows(menu)]
    if menu in ('remote-away', 'remote-share'):
        sources += [(setup, row) for row in rows(setup)]
    return [{'menu': owner, 'source': row['text'], 'title': messages.get(row['text'], row['text']),
             'description': messages.get(row.get('subtext', ''), row.get('subtext', '')),
             'icon': row.get('icon', '')}
            for owner, row in sources if row.get('actions') and row['text'] not in ('Sharing Status', 'Connection Status', 'Log In')]


def tailscale_status():
    state = {'installed': bool(shutil.which('tailscale')), 'connected': False, 'signedOut': False,
             'addresses': [], 'peers': [], 'facts': []}
    if not state['installed']:
        return {**state, 'status': tr('Tailscale is not installed.')}
    try:
        response = query(['tailscale', 'status', '--json'])
        if response.returncode:
            raise ValueError('Status unavailable')
        data = json.loads(response.stdout)
        backend = data.get('BackendState')
        state['connected'] = backend == 'Running'
        state['signedOut'] = backend == 'NeedsLogin'
        state['status'] = (tr('Connected') if backend == 'Running' else tr('Signed out') if backend == 'NeedsLogin'
                           else tr('Disconnected') if backend == 'Stopped' else tr('Tailscale status unavailable.'))
        state['addresses'] = data.get('TailscaleIPs') or []
        local = data.get('Self') or {}
        state['facts'] = [
            {'label': tr('Device'), 'value': local.get('HostName') or tr('Unavailable')},
            {'label': tr('Tailscale IP'), 'value': ', '.join(state['addresses']) or tr('Unavailable')},
            {'label': tr('Network'), 'value': (data.get('CurrentTailnet') or {}).get('Name') or tr('Unavailable')},
        ]
        state['peers'] = sorted([
            {'name': peer.get('HostName') or peer.get('DNSName', ''),
             'connection': (tr('Direct') if peer.get('CurAddr') else tr('Relayed') if peer.get('Relay')
                            else tr('Idle; ping to check')) if peer.get('Active') else tr('Idle; ping to check')}
            for peer in (data.get('Peer') or {}).values() if peer.get('Online')], key=lambda peer: peer['name'].casefold())
    except (OSError, ValueError, TypeError, AttributeError, subprocess.SubprocessError):
        state['status'] = tr('Tailscale status unavailable.')
    return state


def streaming_status():
    state = {'installed': bool(shutil.which('sunshine')), 'running': False,
             'facts': [{'label': tr('Host'), 'value': 'Sunshine'},
                       {'label': tr('Client'), 'value': 'Moonlight'}]}
    if not state['installed']:
        return {**state, 'status': tr('Sunshine is not installed.')}
    try:
        response = query(['systemctl', '--user', 'show', 'eitr-sunshine.service',
                          '--property=ActiveState', '--property=UnitFileState'])
        if response.returncode:
            raise ValueError('Service unavailable')
        properties = dict(line.split('=', 1) for line in response.stdout.splitlines() if '=' in line)
        state['running'] = properties.get('ActiveState') == 'active'
        state['startAtLogin'] = properties.get('UnitFileState') == 'enabled'
        state['facts'] = [
            {'label': tr('Host'), 'value': 'Sunshine'},
            {'label': tr('Client'), 'value': 'Moonlight'},
            {'label': tr('Capture'), 'value': 'KMS'},
            {'label': tr('Settings'), 'value': 'https://localhost:47990'},
        ]
        state['status'] = tr('Sharing this desktop') if state['running'] else tr('Sharing stopped')
    except (OSError, ValueError, subprocess.SubprocessError):
        state['status'] = tr('Sharing status unavailable.')
    return state


def status():
    from eitr_policy import allowed
    if not allowed('remote_access'):
        return {'allowed': False, 'tailscale': {}, 'streaming': {}}
    return {'allowed': True, 'tailscale': {**tailscale_status(), 'actions': menu_actions('remote-away')},
            'streaming': {**streaming_status(), 'actions': menu_actions('remote-share')
                          + [row for row in menu_actions('remote-access') if row['source'] == 'Connect to another PC']}}


if __name__ == '__main__':
    if sys.argv[1:] == ['availability']:
        from eitr_policy import allowed
        result = {'allowed': allowed('remote_access')}
    else:
        result = status()
    print(json.dumps(result, ensure_ascii=False))
