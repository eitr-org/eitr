"""Machine-local wallpaper scopes and temporary, owner-scoped desktop previews."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
from contextlib import contextmanager
from eitr_paths import config, cache, state, read_settings, write_settings, theme_paths
from eitr_workspaces import preferences
from eitr_i18n import tr


def settings():
    return config('eitr/wallpapers.json')


def runtime():
    return Path(os.environ.get('XDG_RUNTIME_DIR', str(cache()))) / 'eitr-wallpaper'


@contextmanager
def locked():
    runtime().mkdir(parents=True, exist_ok=True, mode=0o700)
    with (runtime() / 'assignments.lock').open('w') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        yield


def query(kind):
    if os.environ.get('EITR_NO_SESSION') == '1':
        return []
    try:
        result = subprocess.run(['hyprctl', kind, '-j'], capture_output=True, text=True, timeout=3, check=True)
        value = json.loads(result.stdout)
        return value if isinstance(value, list) else []
    except (OSError, ValueError, subprocess.SubprocessError):
        return []


def workspace_number(monitor):
    identifier = monitor.get('activeWorkspace', {}).get('id', 0)
    if identifier < 1:
        return 0
    plan = read_settings(state('eitr/workspaces.json')).get('rows', [])
    row = next((row for row in plan if row.get('id') == identifier and row.get('monitor') == monitor['name']), None)
    if row:
        return row['number']
    return (identifier - 1) % 10 + 1 if preferences()['workspaceMode'] == 'shared' else identifier


def key(scope, monitor='', number=0):
    if scope == 'global':
        return 'global'
    if scope not in ('monitor', 'workspace') or not monitor:
        raise ValueError(tr('A connected display is required'))
    if scope == 'workspace' and not 1 <= number <= 10:
        raise ValueError(tr('A numbered workspace is required'))
    return json.dumps([monitor, number if scope == 'workspace' else 0], ensure_ascii=False)


def available(path):
    return isinstance(path, str) and bool(path) and Path(path).is_file()


def saved_global(default=''):
    path = read_settings(config('eitr/appearance.json')).get('wallpaper', '')
    if not available(path):
        try:
            path = (cache() / 'current-wallpaper').read_text().strip()
        except OSError:
            path = ''
    return path if available(path) else default


def canonical(path):
    """Pin a selection from the replaceable current-theme copy to its source art."""
    candidate = Path(path).resolve()
    current = config('theme/current').resolve()
    if candidate.is_relative_to(current):
        try:
            theme = (cache() / 'current-theme').read_text().strip()
        except OSError:
            theme = ''
        source = theme_paths().get(theme)
        if source:
            original = source / candidate.relative_to(current)
            if original.is_file():
                return str(original.resolve())
    return str(candidate)


def prune():
    data = read_settings(settings()).get('assignments', {})
    clean = {scope: path for scope, path in data.items() if available(path)}
    if clean != data:
        write_settings(settings(), {'assignments': clean})
    return clean


def preview():
    data = read_settings(runtime() / 'preview.json')
    return data if (available(data.get('path'))
                    and Path('/proc/' + str(data.get('pid', 0))).exists()) else {}


def resolve(monitor, default, assignments=None, temporary=None):
    assignments = prune() if assignments is None else assignments
    temporary = preview() if temporary is None else temporary
    scopes = [key('workspace', monitor['name'], workspace_number(monitor))] if workspace_number(monitor) else []
    scopes += [key('monitor', monitor['name']), 'global']
    # A preview represents the candidate at its chosen scope, preserving precedence.
    choices = dict(assignments)
    if temporary:
        choices[temporary['scope']] = temporary['path']
    return next((choices[scope] for scope in scopes if available(choices.get(scope))), default)


def images(transition, default, monitors=None, temporary=None, global_override=False):
    monitors = query('monitors') if monitors is None else monitors
    assignments = prune()
    default = default if global_override else saved_global(default)
    result = {}
    for monitor in monitors:
        selected = resolve(monitor, default, assignments, temporary)
        if available(selected):
            result[monitor['name']] = transition['for_monitor'](selected, monitor)
    if default:
        result['*'] = default
    return result


def reconcile(transition, default='', monitors=None):
    """Serialize output changes, read current workspaces after acquiring the lock,
    and touch only outputs whose effective image changed. Never restart Hyprpaper."""
    with locked():
        monitors = query('monitors') if monitors is None else monitors
        selected = images(transition, default, monitors)
        active = None if os.environ.get('EITR_NO_SESSION') == '1' else transition['active_wallpapers']()
        failures = []
        if active is not None:
            for name, path in selected.items():
                if name == '*' or active.get(name) == path:
                    continue
                try:
                    result = subprocess.run(['hyprctl', 'hyprpaper', 'wallpaper', name + ',' + path],
                                            check=True, capture_output=True, text=True, timeout=3)
                    if isinstance(result.stdout, str) and any(word in result.stdout.lower() for word in ('error', 'failed')):
                        failures.append(name)
                except (OSError, subprocess.SubprocessError):
                    failures.append(name)
        return selected, active, failures


def change(action, scope, path, owner):
    with locked():
        if action == 'preview':
            if not available(path):
                raise ValueError(tr('Wallpaper file not found'))
            write_settings(runtime() / 'preview.json', dict(scope=scope, path=path, owner=owner, pid=os.getppid()))
        elif action == 'cancel':
            current = read_settings(runtime() / 'preview.json')
            if current.get('owner') == owner or owner == 'startup':
                write_settings(runtime() / 'preview.json', dict(path=''))
        else:
            data = prune()
            if action == 'clear':
                data.pop(scope, None)
            else:
                if not available(path):
                    raise ValueError(tr('Wallpaper file not found'))
                data[scope] = canonical(path)
            write_settings(settings(), {'assignments': data})
            if read_settings(runtime() / 'preview.json').get('owner') == owner:
                write_settings(runtime() / 'preview.json', dict(path=''))


def summary(monitor_name=''):
    monitors = query('monitors')
    monitor = next((monitor for monitor in monitors if monitor['name'] == monitor_name), None)
    monitor = monitor or next((monitor for monitor in monitors if monitor.get('focused')), monitors[0] if monitors else {})
    name = monitor.get('name', '')
    number = workspace_number(monitor) if name else 0
    entries = []
    for scope, path in prune().items():
        if scope == 'global':
            continue
        try:
            display, workspace = json.loads(scope)
        except (ValueError, TypeError):
            continue
        entries.append(dict(key=scope, monitor=display, number=workspace, path=path))
    return dict(monitor=name, number=number, assignments=entries)
