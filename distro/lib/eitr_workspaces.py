"""Numbered workspace preferences and deterministic monitor assignments."""
from eitr_paths import config, state, read_settings

DEFAULTS = {'workspaceMode': 'shared', 'workspaceCount': 10, 'workspaceAlwaysShow': 5}


def preferences(data=None):
    data = read_settings(config('eitr/style.json')) if data is None else data
    mode = data.get('workspaceMode')
    count = data.get('workspaceCount')
    shown = data.get('workspaceAlwaysShow')
    count = count if type(count) is int and 5 <= count <= 10 else 10
    shown = shown if type(shown) is int and 2 <= shown <= count else min(5, count)
    return dict(workspaceMode=mode if mode in ('shared', 'split') else 'shared',
                workspaceCount=count, workspaceAlwaysShow=shown)


def assignments(monitors, primary, preference):
    ordered = sorted((monitor for monitor in monitors if not monitor.get('disabled', False)),
                     key=lambda monitor: (monitor['name'] != primary, monitor.get('x', 0), monitor['name']))
    count = preference['workspaceCount']
    shared = preference['workspaceMode'] == 'shared'
    result = []
    start = 1
    for slot, monitor in enumerate(ordered):
        length = count if shared else count // len(ordered) + (slot < count % len(ordered))
        for offset in range(length):
            number = offset + 1 if shared else start + offset
            result.append(dict(id=slot * 10 + number if shared else number, number=number,
                               monitor=monitor['name'], position=offset + 1))
        start += length
    return result


def destination(rows, monitor, number):
    local = [row for row in rows if row['monitor'] == monitor]
    return min(local or rows, key=lambda row: abs(row['number'] - number)) if rows else None


def migration(clients, monitors, previous, rows):
    names = {monitor['id']: monitor['name'] for monitor in monitors}
    old = {row['id']: row for row in previous}
    moves = []
    for client in clients:
        workspace = client.get('workspace', {})
        identifier = workspace.get('id', 0)
        if identifier < 1 or workspace.get('name', '').startswith('eitr-focus-'):
            continue
        prior = old.get(identifier)
        number = prior['number'] if prior else (identifier - 1) % 10 + 1
        target = destination(rows, names.get(client.get('monitor'), ''), number)
        if target and identifier != target['id']:
            moves.append((client['address'], target))
    return moves


def preview_count():
    """Walker's compact style samples never exceed the main display's range."""
    preference = preferences()
    rows = read_settings(state('eitr/workspaces.json')).get('rows', [])
    monitors = max(1, len({row['monitor'] for row in rows}))
    capacity = preference['workspaceCount']
    if preference['workspaceMode'] == 'split':
        capacity = (capacity + monitors - 1) // monitors
    return min(4, capacity, preference['workspaceAlwaysShow'])
