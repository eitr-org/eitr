#!/usr/bin/env python3
"""Read desktop sharing (Sunshine) status and expose its menu's existing actions.
Tailscale is a plugin with its own status and panel."""
import eitr_bootstrap
from eitr_i18n import tr, table
from eitr_menu import rows
import json
import shutil
import subprocess
import sys


def query(arguments):
    return subprocess.run(arguments, capture_output=True, text=True, timeout=3, check=False)


# Each menu's setup folder; Streaming (remote-access) holds Sunshine's rows directly.
SETUP_MENUS = {'remote-access': 'remote-share-setup'}


def menu_actions(menu):
    messages = table('menus')
    sources = [(menu, row) for row in rows(menu)]
    if menu in SETUP_MENUS:
        sources += [(SETUP_MENUS[menu], row) for row in rows(SETUP_MENUS[menu])]
    return [{'menu': owner, 'source': row['text'], 'title': messages.get(row['text'], row['text']),
             'description': messages.get(row.get('subtext', ''), row.get('subtext', '')),
             'icon': row.get('icon', '')}
            for owner, row in sources if row.get('actions') and row['text'] != 'Sharing Status']


def streaming_status():
    state = {'installed': bool(shutil.which('sunshine')), 'moonlightInstalled': bool(shutil.which('moonlight')), 'running': False,
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
        return {'allowed': False, 'streaming': {}}
    return {'allowed': True, 'streaming': {**streaming_status(), 'actions': menu_actions('remote-access')}}


if __name__ == '__main__':
    if sys.argv[1:] == ['availability']:
        from eitr_policy import allowed
        result = {'allowed': allowed('remote_access')}
    else:
        result = status()
    print(json.dumps(result, ensure_ascii=False))
