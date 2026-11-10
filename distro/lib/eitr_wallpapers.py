"""Machine-local display wallpapers and temporary, owner-scoped desktop previews."""
import fcntl
import json
import os
from pathlib import Path
import subprocess
from contextlib import contextmanager
from eitr_paths import config, cache, read_settings, write_settings, theme_paths
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


def per_display():
    return read_settings(settings()).get('perDisplay') is True


def focused_monitor():
    return next((monitor['name'] for monitor in query('monitors') if monitor.get('focused')), '')


def target():
    if not per_display():
        return ''
    monitor = focused_monitor()
    if not monitor:
        raise ValueError(tr('A connected display is required'))
    return monitor


def save(assignments, enabled=None):
    write_settings(settings(), {'perDisplay': per_display() if enabled is None else enabled,
                                'assignments': assignments})


def set_per_display(enabled):
    with locked():
        save(prune(), enabled)
        write_settings(runtime() / 'preview.json', {'path': ''})


def clear_assignments():
    with locked():
        save({})
        write_settings(runtime() / 'preview.json', {'path': ''})


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
    clean = {}
    for monitor, path in data.items():
        # Read old display keys, silently discard old workspace/global entries.
        if monitor.startswith('['):
            try:
                monitor, number = json.loads(monitor)
                if number != 0 or not isinstance(monitor, str):
                    continue
            except (ValueError, TypeError):
                continue
        if monitor and monitor != 'global' and available(path):
            clean[monitor] = path
    if clean != data:
        save(clean)
    return clean


def preview():
    data = read_settings(runtime() / 'preview.json')
    return data if (available(data.get('path'))
                    and Path('/proc/' + str(data.get('pid', 0))).exists()) else {}


def previewing(owner, path):
    """Whether this owner's preview already shows path on every display."""
    current = preview()
    return bool(owner) and current.get('owner') == owner and not current.get('monitor') \
        and Path(current.get('path', '')).resolve() == Path(path).resolve()


def resolve(monitor, default, assignments=None, temporary=None):
    assignments = prune() if assignments is None else assignments
    temporary = preview() if temporary is None else temporary
    enabled = per_display()
    if temporary and temporary.get('monitor', '') == (monitor['name'] if enabled else ''):
        return temporary['path']
    selected = assignments.get(monitor['name']) if enabled else None
    return selected if available(selected) else default


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


def reconcile(transition, default='', monitors=None, output=''):
    """Serialize output changes, read current monitors after acquiring the lock,
    and touch only outputs whose effective image changed. Never restart Hyprpaper."""
    with locked():
        monitors = query('monitors') if monitors is None else monitors
        selected = images(transition, default, monitors)
        active = None if os.environ.get('EITR_NO_SESSION') == '1' else transition['active_wallpapers']()
        failures = []
        if active is not None:
            for name, path in selected.items():
                if name == '*' or (output and name != output) or active.get(name) == path:
                    continue
                try:
                    result = subprocess.run(['hyprctl', 'hyprpaper', 'wallpaper', name + ',' + path],
                                            check=True, capture_output=True, text=True, timeout=3)
                    if isinstance(result.stdout, str) and any(word in result.stdout.lower() for word in ('error', 'failed')):
                        failures.append(name)
                except (OSError, subprocess.SubprocessError):
                    failures.append(name)
        return selected, active, failures


def change(action, monitor, path, owner):
    with locked():
        if action == 'preview':
            if not available(path):
                raise ValueError(tr('Wallpaper file not found'))
            write_settings(runtime() / 'preview.json', dict(monitor=monitor, path=path, owner=owner, pid=os.getppid()))
        elif action == 'cancel':
            current = read_settings(runtime() / 'preview.json')
            if current.get('owner') == owner or owner == 'startup':
                write_settings(runtime() / 'preview.json', dict(path=''))
        elif action == 'apply':
            if not available(path):
                raise ValueError(tr('Wallpaper file not found'))
            data = prune()
            data[monitor] = canonical(path)
            save(data)
            if read_settings(runtime() / 'preview.json').get('owner') == owner:
                write_settings(runtime() / 'preview.json', dict(path=''))


def summary():
    return dict(monitor=focused_monitor(), perDisplay=per_display(),
                assignments=[dict(monitor=monitor, path=path) for monitor, path in prune().items()])
