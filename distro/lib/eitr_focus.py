"""Focus desktop controller. Native groups own tabs; the strip only observes them."""
import argparse
import fcntl
import json
import math
import os
import re
import subprocess
import sys
import shlex
from pathlib import Path

from eitr_paths import code, config, state, read_settings, write_settings
from eitr_i18n import mark as menu_mark, table

PREFIX = 'eitr-focus-'
OVERRIDES = {
    'general.gaps_in': 'css', 'general.gaps_out': 'css', 'general.border_size': 'int', 'general.layout': 'str',
    'decoration.rounding': 'int', 'decoration.blur.enabled': 'bool', 'decoration.shadow.enabled': 'bool',
    'animations.enabled': 'bool', 'group.auto_group': 'bool', 'group.group_on_movetoworkspace': 'bool',
    'group.groupbar.enabled': 'bool',
}
FOCUS_KEYS = [
    *[{'key': f'SUPER + {number}', 'label': menu_mark('Select tab {number}'), 'number': number,
       'action': f'tab {number}'} for number in range(1, 10)],
    {'key': 'SUPER + Tab', 'label': menu_mark('Next tab'), 'action': 'next'},
    {'key': 'SUPER + SHIFT + Tab', 'label': menu_mark('Previous tab'), 'action': 'previous'},
    {'key': 'SUPER + backslash', 'label': menu_mark('Split side by side'), 'action': 'horizontal'},
    {'key': 'SUPER + minus', 'label': menu_mark('Split stacked'), 'action': 'vertical'},
    {'key': 'SUPER + SHIFT + backslash', 'label': menu_mark('Return pane to a tab'), 'action': 'join'},
    {'key': 'SUPER + h', 'label': menu_mark('Focus left'), 'direction': 'l'},
    {'key': 'SUPER + j', 'label': menu_mark('Focus down'), 'direction': 'd'},
    {'key': 'SUPER + k', 'label': menu_mark('Focus up'), 'direction': 'u'},
    {'key': 'SUPER + l', 'label': menu_mark('Focus right'), 'direction': 'r'},
    {'key': 'SUPER + SHIFT + h', 'label': menu_mark('Resize narrower'), 'layout': 'narrower'},
    {'key': 'SUPER + SHIFT + j', 'label': menu_mark('Resize taller'), 'layout': 'taller'},
    {'key': 'SUPER + SHIFT + k', 'label': menu_mark('Resize shorter'), 'layout': 'shorter'},
    {'key': 'SUPER + SHIFT + l', 'label': menu_mark('Resize wider'), 'layout': 'wider'},
]


def snapshot(hypr):
    values = {}
    for name, kind in OVERRIDES.items():
        value = hypr.option(name.replace('.', ':'))
        if kind == 'css':
            parts = [float(part) for part in value['css'].split()]
            if len(parts) != 4:
                raise ValueError('Expected four compositor gap values')
            values[name] = dict(zip(('top', 'right', 'bottom', 'left'), parts))
        elif kind == 'bool':
            values[name] = bool(value['int'])
        else:
            values[name] = value[kind]
    write_settings(state('eitr/focus-session.json'), {
        'session': os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', ''), 'options': values, 'pending': True,
        'corners': read_settings(config('eitr/style.json')).get('corners')})


def lua_value(value):
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, (int, float)):
        if not math.isfinite(value):
            raise ValueError('Invalid compositor value')
        return str(value)
    if isinstance(value, dict):
        return '{' + ','.join('[' + lua(key) + ']=' + lua_value(item) for key, item in value.items()) + '}'
    return lua(value)


def restore_options(hypr):
    saved = read_settings(state('eitr/focus-session.json'))
    if saved.get('session') == os.environ.get('HYPRLAND_INSTANCE_SIGNATURE', '') and saved.get('pending'):
        values = {name: value for name, value in saved.get('options', {}).items() if name in OVERRIDES}
        if saved.get('corners') != read_settings(config('eitr/style.json')).get('corners'):
            values.pop('decoration.rounding', None)
        hypr.evaluate('hl.config(' + lua_value(values) + ')')
    write_settings(state('eitr/focus-session.json'), {'pending': False})




def network_status(interfaces=Path('/sys/class/net')):
    for interface in interfaces.iterdir():
        if interface.name == 'lo' or (interface / 'wireless').exists() or not (interface / 'device').exists():
            continue
        try:
            if (interface / 'operstate').read_text().strip() == 'up':
                return {'text': '󰈀'}
        except OSError:
            continue
    result = subprocess.run(['bash', str(code('quickshell/desktop-bar/scripts/wifi-status.sh'))],
                            capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout) if result.returncode == 0 else {'text': ''}


def shortcut_entries(translated=False):
    messages = table("menus") if translated else {}
    return [{'Text': messages.get(entry['label'], entry['label']).replace('{number}', str(entry.get('number', ''))),
             'Subtext': entry['key'].replace('SHIFT', 'Shift').replace('backslash', '\\').replace('minus', '-'),
             'Icon': '󰍹', 'Actions': {'open': 'true'}} for entry in FOCUS_KEYS]


def bindings():
    helper = 'python3 ' + shlex.quote(str(code('quickshell/desktop-bar/scripts/focus-mode.py')))
    lines = []
    for entry in FOCUS_KEYS:
        key = lua(entry['key'])
        if 'direction' in entry:
            dispatcher = 'hl.dsp.focus({direction=' + lua(entry['direction']) + '})'
        elif 'layout' in entry:
            dispatcher = 'hl.dsp.layout(' + lua(entry['layout']) + ')'
        else:
            dispatcher = 'hl.dsp.exec_cmd(' + lua(helper + ' ' + entry['action']) + ')'
        lines.extend(['hl.unbind(' + key + ')', 'hl.bind(' + key + ', ' + dispatcher +
                      (', {repeating=true})' if 'layout' in entry else ')')])
    return '\n'.join(lines)


def enabled():
    return read_settings(config('eitr/focus.json')).get('enabled') is True


def lua(value):
    # Fixed-width byte escapes work in both Lua 5.1 and LuaJIT, including Unicode names.
    return '"' + ''.join(chr(byte) if 32 <= byte < 127 and chr(byte) not in ('"', '\\')
                         else f'\\{byte:03d}' for byte in value.encode('utf-8')) + '"'


class Hypr:
    def run(self, *arguments):
        result = subprocess.run(['hyprctl', *arguments], capture_output=True, text=True, timeout=15)
        if result.returncode or result.stdout.lstrip().startswith(('error', 'Error')):
            raise RuntimeError(result.stderr.strip() or result.stdout.strip() or 'hyprctl failed')
        return result.stdout

    def query(self, kind):
        return json.loads(self.run('-j', kind))

    def ensure_bar(self):
        # eitr-shell uses Quickshell's no-duplicate flag; an existing bar stays intact.
        subprocess.run(['eitr-shell', 'desktop-bar', '--daemonize'], check=True,
                       capture_output=True, text=True, timeout=20)

    def option(self, name):
        return json.loads(self.run('-j', 'getoption', name))

    def evaluate(self, expression):
        return self.run('eval', expression)

    def window(self, address, expression):
        if not re.fullmatch(r'0x[0-9a-fA-F]+', address):
            raise ValueError('Invalid window address')
        return self.evaluate('local window = hl.get_window(' + lua('address:' + address)
                             + '); if window and window.mapped then ' + expression + ' end')


def clients_by_monitor(clients):
    monitors = {}
    for client in clients:
        if client.get('mapped', True):
            monitors.setdefault(client['monitor'], []).append(client)
    return monitors


def spread_plan(clients):
    """Two windows per normal workspace, with distinct workspaces per monitor."""
    plan = []
    workspace = 1
    for monitor, windows in clients_by_monitor(clients).items():
        for index, window in enumerate(windows):
            plan.append((window['address'], monitor, workspace + index // 2))
        workspace += max(1, (len(windows) + 1) // 2)
    return plan


def normalize(hypr, client):
    hypr.window(client['address'], '''
        hl.dispatch(hl.dsp.window.fullscreen_state({window=window, internal=0, client=0}));
        hl.dispatch(hl.dsp.window.pin({window=window, action="unset"}));
        hl.dispatch(hl.dsp.window.float({window=window, action="unset"}));
    ''')


def gather(hypr):
    """Idempotent reconciliation, preserving existing native split groups."""
    clients = hypr.query('clients')
    for monitor in hypr.query('monitors'):
        workspace = PREFIX + str(monitor['id'])
        special = monitor.get('specialWorkspace', {}).get('name', '')
        if special.startswith('special:'):
            hypr.evaluate('hl.dispatch(hl.dsp.focus({monitor=' + lua(monitor['name']) + '})); '
                          'hl.dispatch(hl.dsp.workspace.toggle_special(' + lua(special[8:]) + '))')
        windows = clients_by_monitor(clients).get(monitor['id'], [])
        resident = [window for window in windows if window.get('workspace', {}).get('name') == workspace]
        anchor = next((window for window in resident if window.get('grouped')), None)
        if anchor is None and resident:
            anchor = resident[0]
            hypr.window(anchor['address'], 'if not window.group then hl.dispatch(hl.dsp.group.toggle({window=window})) end')
        placed = False
        for client in windows:
            if client in resident and (client.get("grouped") or client is anchor):
                continue
            normalize(hypr, client)
            hypr.window(client['address'], 'if window.group then window.group:remove(window) end; '
                        'hl.dispatch(hl.dsp.window.move({window=window, workspace=' + lua('name:' + workspace) + ', follow=false}))')
            if not placed:
                hypr.evaluate('hl.dispatch(hl.dsp.workspace.move({workspace=' + lua('name:' + workspace)
                              + ', monitor=' + str(monitor['id']) + '}))')
                placed = True
            if anchor:
                hypr.window(client['address'], 'local anchor=hl.get_window(' + lua('address:' + anchor['address'])
                            + '); if anchor and anchor.mapped and anchor.group then anchor.group:add(window) end')
            else:
                hypr.window(client['address'], 'if not window.group then hl.dispatch(hl.dsp.group.toggle({window=window})) end')
                anchor = client
        if monitor.get('activeWorkspace', {}).get('name') != workspace:
            hypr.evaluate('hl.dispatch(hl.dsp.focus({monitor=' + lua(monitor['name']) + '})); '
                          'hl.dispatch(hl.dsp.focus({workspace=' + lua('name:' + workspace) + '}))')


def spread(hypr):
    clients = hypr.query('clients')
    hypr.evaluate('hl.config({group={group_on_movetoworkspace=false}})')
    for address, monitor, workspace in spread_plan(clients):
        hypr.window(address, 'if window.group then window.group:remove(window) end; '
                    'hl.dispatch(hl.dsp.window.fullscreen_state({window=window, internal=0, client=0})); '
                    'hl.dispatch(hl.dsp.window.move({window=window, workspace=' + str(workspace) + ', follow=false}))')
        hypr.evaluate('hl.dispatch(hl.dsp.workspace.move({workspace=' + str(workspace)
                      + ', monitor=' + str(monitor) + '}))')
    for monitor in hypr.query('monitors'):
        destination = next((workspace for _, monitor_id, workspace in spread_plan(clients)
                            if monitor_id == monitor['id']), monitor['id'] + 1)
        hypr.evaluate('hl.dispatch(hl.dsp.focus({monitor=' + lua(monitor['name']) + '})); '
                      'hl.dispatch(hl.dsp.focus({workspace=' + str(destination) + '}))')


def change(action, hypr):
    previous = enabled()
    desired = action == 'on'
    if desired and not previous:
        snapshot(hypr)
    write_settings(config('eitr/focus.json'), {'enabled': desired})
    # Reload restores the user's base config, local overrides and normal bindings.
    # Preference is written first so a crash can always be recovered with "off".
    hypr.run('reload', 'config-only')
    active = hypr.query('activewindow').get('address')
    if desired:
        gather(hypr)
    elif previous or any(client.get('workspace', {}).get('name', '').startswith(PREFIX)
                         for client in hypr.query('clients')):
        merge_policy = hypr.option('group:group_on_movetoworkspace')['int']
        spread(hypr)
        hypr.evaluate('hl.config({group={group_on_movetoworkspace=' + ('true' if merge_policy else 'false') + '}})')
    if not desired:
        restore_options(hypr)
    if active:
        hypr.window(active, 'hl.dispatch(hl.dsp.focus({window=window}))')
    hypr.ensure_bar()


def tab_action(action, value, hypr):
    if not enabled():
        return
    active = hypr.query('activewindow')
    windows = clients_by_monitor(hypr.query('clients')).get(active.get('monitor'), [])
    if not windows:
        return
    index = next((index for index, client in enumerate(windows) if client['address'] == active.get('address')), 0)
    if action == 'tab':
        index = int(value) - 1
        if index < 0 or index >= len(windows):
            return
    elif action in ('next', 'previous'):
        index = (index + (1 if action == 'next' else -1)) % len(windows)
    if action in ('tab', 'next', 'previous'):
        hypr.window(windows[index]['address'], 'hl.dispatch(hl.dsp.focus({window=window}))')
    elif action in ('horizontal', 'vertical'):
        visible = [window for window in windows if not window.get('hidden', False)]
        if len(visible) >= 4:
            return
        members = active.get('grouped', [])
        candidate = next((window for window in windows[index+1:] + windows[:index]
                          if window['address'] in members and window['address'] != active.get('address')), None)
        if candidate:
            hypr.window(candidate['address'], 'if window.group then window.group:remove(window) end; '
                        'hl.dispatch(hl.dsp.group.toggle({window=window})); hl.dispatch(hl.dsp.focus({window=window})); '
                        'hl.dispatch(hl.dsp.layout(' + lua(action) + '))')
    elif action == 'join':
        # Fold the split back into one native group, keeping the focused window selected.
        for client in windows:
            hypr.window(client['address'], 'local anchor=hl.get_window(' + lua('address:' + active['address']) + '); '
                        'if anchor and anchor.mapped then if not anchor.group then hl.dispatch(hl.dsp.group.toggle({window=anchor})) end; '
                        'if window.group ~= anchor.group then if window.group then window.group:remove(window) end; '
                        'anchor.group:add(window) end end')
        hypr.window(active['address'], 'hl.dispatch(hl.dsp.focus({window=window}))')



def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['on', 'off', 'status', 'get', 'set', 'reconcile', 'network', 'tab',
                                           'next', 'previous', 'horizontal', 'vertical', 'join', 'bindings', 'entries'])
    parser.add_argument('values', nargs='*')
    arguments = parser.parse_args(argv)
    action = arguments.action
    if action == 'network':
        print(json.dumps(network_status()))
        return 0
    if action == 'bindings':
        print(bindings())
        return 0
    if action == 'entries':
        print(json.dumps(shortcut_entries(translated=True)))
        return 0
    if action in ('get', 'status'):
        print('on' if enabled() else 'off')
        return 0
    if action == 'set':
        if arguments.values not in (['focus', 'on'], ['focus', 'off']):
            parser.error('expected set focus on|off')
        action = arguments.values[1]
    if action == 'tab' and (len(arguments.values) != 1 or not arguments.values[0].isdigit()):
        parser.error('expected tab NUMBER')
    lock = state('eitr/focus.lock')
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        hypr = Hypr()
        if action in ('on', 'off'):
            change(action, hypr)
        elif action == 'reconcile':
            if enabled():
                active = hypr.query('activewindow').get('address')
                gather(hypr)
                if active:
                    hypr.window(active, 'hl.dispatch(hl.dsp.focus({window=window}))')
        else:
            tab_action(action, arguments.values[0] if arguments.values else '', hypr)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        sys.exit(1)
