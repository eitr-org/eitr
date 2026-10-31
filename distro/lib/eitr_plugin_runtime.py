"""Approved plugin services, hooks, commands and visual runtime state."""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import tempfile

import eitr_policy
from eitr_paths import config, state
from eitr_plugin_install import (
    PluginInstall as _PluginInstall,
    commit,
    official,
    short_author,
)
from eitr_plugin_manifest import (
    HOOK_EVENTS,
    command,
    identifier,
    manifest,
    object_keys,
    plugin_files,
    printable,
    string,
    unique_object,
)


HOOK_TIMEOUT = 30
UI_FAILURE_LIMIT = 3

def unit_content(root, spec):
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
    argv = command(root, spec['service'])
    return ('[Unit]\nDescription=Eitr plugin ' + spec['id'] + '\n\n[Service]\nType=simple\nExecStart='
            + ' '.join(quote(argument) for argument in argv)
            + '\nNoNewPrivileges=yes'
            # A device or network the service needs may not be ready yet when it starts.
            + '\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n')


class PluginRuntime:
    def unit(self, plugin_id):
        return self.units / f'eitr-plugin-{identifier(plugin_id)}.service'

    def systemctl(self, *arguments):
        subprocess.run(['systemctl', '--user', *arguments], check=True, capture_output=True, text=True)

    def service(self, plugin_id, spec=None, *, root=None):
        unit = self.unit(plugin_id)
        if unit.exists():
            self.systemctl('disable', '--now', unit.name)
            unit.unlink()
        if spec and 'service' in spec:
            self.units.mkdir(parents=True, exist_ok=True)
            unit.write_text(unit_content(root if root is not None else self.root(plugin_id), spec))
        self.systemctl('daemon-reload')
        if spec and 'service' in spec:
            self.systemctl('enable', '--now', unit.name)

    def stop(self, plugin_id):
        unit = self.unit(plugin_id)
        if not unit.exists():
            return
        try:
            self.systemctl('disable', '--now', unit.name)
        except (OSError, subprocess.SubprocessError):
            # Without a running user manager, disabling is removing its login link.
            (self.units / 'default.target.wants' / unit.name).unlink(missing_ok=True)

    def rows(self):
        blocked = self.enforce(blocking=False)
        rows = []
        for plugin_id, record in self.records().items():
            if plugin_id in blocked:
                continue
            root = self.root(plugin_id)
            try:
                if root.is_symlink() or commit(root) != record['commit']:
                    continue
                spec = manifest(root)
                for index, row in enumerate(spec['rows']):
                    rows.append(dict(id=plugin_id, index=index, title=row['title'], description=row['description'],
                                     author=short_author(spec), official=official(record['url']),
                                     icon=row.get('icon', '󰏖')))
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        return sorted(rows, key=lambda row: row['title'].casefold())

    def ui_state(self):
        path = state('eitr/plugin-ui.json')
        try:
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError('Invalid plugin UI state')
            for plugin_id, record in value.items():
                identifier(plugin_id)
                object_keys(record, ('failures', 'disabled'))
                if type(record['failures']) is not int or not 0 <= record['failures'] <= UI_FAILURE_LIMIT or type(record['disabled']) is not bool:
                    raise ValueError('Invalid plugin UI state')
            return value
        except FileNotFoundError:
            return {}

    def ui_failure(self, plugin_id, approved, message='Component load error'):
        identifier(plugin_id)
        with self.lock():
            if self.records()[plugin_id]['commit'] != approved:
                raise ValueError('Stale plugin UI failure')
            values = self.ui_state()
            previous = values.get(plugin_id, {})
            count = min(UI_FAILURE_LIMIT, previous.get('failures', 0) + 1)
            values[plugin_id] = dict(failures=count, disabled=count >= UI_FAILURE_LIMIT)
            self.write(state('eitr/plugin-ui.json'), values)
            log = state('eitr/plugin-ui.log')
            with log.open('a') as output:
                output.write(f'{plugin_id}: {printable(message)[:2048]} ({count}/{UI_FAILURE_LIMIT})\n')
            return values[plugin_id]

    def enable_ui(self, plugin_id):
        identifier(plugin_id)
        with self.lock():
            if plugin_id not in self.records():
                raise ValueError('Unknown plugin')
            values = self.ui_state()
            values.pop(plugin_id, None)
            self.write(state('eitr/plugin-ui.json'), values)

    def ui(self):
        """Approved declarations; widgets and bar items need a separate user placement."""
        blocked = self.blocked()
        failures = self.ui_state()
        result = []
        for plugin_id, record in self.records().items():
            if plugin_id in blocked:
                continue
            root = self.root(plugin_id)
            try:
                if root.is_symlink() or commit(root) != record['commit']:
                    continue
                list(plugin_files(root))
                spec = manifest(root)
                for kind in ('tiles', 'panels', 'widgets', 'barItems'):
                    for entry in spec.get('ui', {}).get(kind, []):
                        result.append(dict(plugin=plugin_id, pluginName=spec['name'], commit=record['commit'], kind=kind,
                                           placement={'widgets': 'desktop', 'barItems': 'bar'}.get(kind, 'control-center'), disabled=bool(failures.get(plugin_id, {}).get('disabled')),
                                           **entry, capabilities=spec.get('capabilities', []), source=(root / entry['qml']).as_uri()))
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        return result

    def placements(self):
        try:
            value = json.loads(config('eitr/plugin-placements.json').read_text(), object_pairs_hook=unique_object)
        except FileNotFoundError:
            return dict(version=2, widgets=[], barItems=[])
        object_keys(value, ('version', 'widgets', 'barItems'))
        if type(value['version']) is not int or value['version'] not in (1, 2):
            raise ValueError('Invalid plugin placement version')
        seen = set()
        for kind in ('widgets', 'barItems'):
            if not isinstance(value[kind], list) or len(value[kind]) > 256:
                raise ValueError('Invalid plugin placements')
            for placement in value[kind]:
                object_keys(placement, ('plugin', 'id') + (('monitor', 'x', 'y', 'width', 'height') if kind == 'widgets' else ()), ('aboveWindows', 'surface') if kind == 'widgets' else ())
                identifier(placement['plugin'])
                identifier(placement['id'])
                key = (kind, placement['plugin'], placement['id'], placement.get('monitor'))
                if key in seen:
                    raise ValueError('Duplicate plugin placement')
                seen.add(key)
                if kind == 'widgets':
                    if 'aboveWindows' in placement and (value['version'] == 1 or type(placement['aboveWindows']) is not bool):
                        raise ValueError('Invalid widget layer')
                    if 'surface' in placement and placement['surface'] not in ('panel', 'none'):
                        raise ValueError('Invalid widget surface')
                    placement.setdefault('aboveWindows', False)
                    string(placement['monitor'])
                    for field in ('x', 'y', 'width', 'height'):
                        if type(placement[field]) is not int or not 0 <= placement[field] <= 65536 or (field in ('width', 'height') and placement[field] < 24):
                            raise ValueError('Invalid widget geometry')
        value['version'] = 2
        return value

    def place(self, plugin_id, entry_id, monitor=None, *, remove=False, geometry=None, toggle_layer=False, surface=None):
        identifier(plugin_id)
        identifier(entry_id)
        with self.lock():
            values = self.placements()
            entry = next((entry for entry in self.ui() if entry['plugin'] == plugin_id and entry['id'] == entry_id and entry['kind'] in ('widgets', 'barItems')), None)
            if not entry and not remove:
                raise ValueError('Unknown plugin visual')
            kind = entry['kind'] if entry else ('widgets' if monitor is not None else 'barItems')
            if kind == 'widgets':
                string(monitor)
            def matches(placement):
                return placement['plugin'] == plugin_id and placement['id'] == entry_id and (kind != 'widgets' or placement['monitor'] == monitor)
            previous = next((placement for placement in values[kind] if matches(placement)), None)
            if toggle_layer and (kind != 'widgets' or previous is None):
                raise ValueError('Widget must be placed before changing layer')
            values[kind] = [placement for placement in values[kind] if not matches(placement)]
            if not remove:
                placement = dict(plugin=plugin_id, id=entry_id)
                if kind == 'widgets':
                    placement.update(previous or dict(monitor=monitor, aboveWindows=False, x=24, y=24, width=entry.get('defaultWidth', 192), height=entry.get('defaultHeight', 192)))
                    if surface is not None:
                        if surface not in ('panel', 'none'):
                            raise ValueError('Invalid widget surface')
                        placement['surface'] = surface
                    if toggle_layer:
                        placement['aboveWindows'] = not placement['aboveWindows']
                    if geometry is not None:
                        object_keys(geometry, ('x', 'y', 'width', 'height'))
                        for field, number in geometry.items():
                            if type(number) is not int or not 0 <= number <= 65536:
                                raise ValueError('Invalid widget geometry')
                        if geometry['width'] < 24 or geometry['height'] < 24:
                            raise ValueError('Widget geometry must be at least 24 pixels')
                        placement.update(geometry)
                values[kind].append(placement)
            if len(values[kind]) > 256:
                raise ValueError('Too many plugin placements')
            path = config('eitr/plugin-placements.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            self.write(path, values)

    def ui_data(self, plugin_id, entry_id):
        entry = next((entry for entry in self.ui() if entry['plugin'] == plugin_id and entry['id'] == entry_id), None)
        if not entry or entry['disabled'] or 'dataCommand' not in entry:
            raise ValueError('Plugin data command is unavailable')
        root = self.root(plugin_id)
        # A temporary file bounds memory even when a command writes excessive output.
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(command(root, entry['dataCommand']), cwd=root, start_new_session=True,
                                       stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.DEVNULL)
            try:
                status = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
                raise ValueError('Plugin data command timed out') from None
            output.seek(0)
            value = output.read(65537)
            if status or len(value) > 65536:
                raise ValueError('Plugin data command failed or exceeded 64 KiB')
            return value.decode('utf-8')

    def hooks(self, event):
        """Called in a detached dispatcher; each approved hook has its own timeout."""
        if event not in HOOK_EVENTS:
            raise ValueError('Unknown plugin event')
        if os.geteuid() == 0 or eitr_policy.load().get('plugins', True) is False:
            return
        if event == 'login':
            session = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE') or os.environ.get('XDG_SESSION_ID')
            runtime = os.environ.get('XDG_RUNTIME_DIR')
            if not session or not runtime:
                return
            marker = Path(runtime) / ('eitr-plugin-login-' + hashlib.sha256(session.encode()).hexdigest())
            try:
                descriptor = os.open(marker, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            except FileExistsError:
                return
            os.close(descriptor)
        log = state('eitr/plugin-hooks.log')
        log.parent.mkdir(parents=True, exist_ok=True)
        with log.open('a') as output:
            for plugin_id, record in self.records().items():
                try:
                    if self.refusal(record['url'], record['commit'], plugin_id):
                        continue
                    root = self.root(plugin_id)
                    if root.is_symlink() or commit(root) != record['commit']:
                        continue
                    spec = manifest(root)
                    hook = spec.get('hooks', {}).get(event)
                    if hook is None:
                        continue
                    environment = {key: value for key, value in os.environ.items() if not key.startswith('EITR_EVENT')
                                   and key not in ('EITR_THEME', 'EITR_WALLPAPER')}
                    environment['EITR_EVENT'] = event
                    context = {'theme-changed': 'EITR_THEME', 'wallpaper-changed': 'EITR_WALLPAPER'}.get(event)
                    if context and context in os.environ:
                        environment[context] = os.environ[context]
                    process = subprocess.Popen(command(root, hook), cwd=root, env=environment,
                                               start_new_session=True, stdin=subprocess.DEVNULL,
                                               stdout=output, stderr=output)
                    try:
                        status = process.wait(timeout=HOOK_TIMEOUT)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                        raise ValueError('timeout after 30 seconds') from None
                    if status:
                        raise ValueError(f'exited with {status}')
                except (OSError, ValueError, subprocess.SubprocessError) as error:
                    output.write(f'{plugin_id} {event}: {printable(str(error))}\n')
                    output.flush()

    def launch(self, plugin_id, index):
        if os.geteuid() == 0:
            raise ValueError('Plugins are per-user; do not run as root')
        record = self.records()[identifier(plugin_id)]
        refused = self.refusal(record['url'], record['commit'], plugin_id)
        if refused:
            self.enforce()
            if refused[0] == 'disabled':
                raise ValueError(refused[1])
            self.check(record['url'], record['commit'], plugin_id)
        root = self.root(plugin_id)
        if root.is_symlink() or commit(root) != record['commit']:
            raise ValueError('Plugin differs from its approved commit')
        spec = manifest(root)
        subprocess.Popen(command(root, spec['rows'][index]), cwd=root, start_new_session=True)


class Plugins(_PluginInstall, PluginRuntime):
    """Per-user approved installations and their runtime operations."""


def dispatch_hooks(event, **context):
    """Fire and forget: triggering actions never wait for plugin code."""
    from eitr_paths import code
    try:
        subprocess.Popen(['python3', str(code('walker/scripts/actions/install/plugins.py')), 'hooks', event],
                         env=dict(os.environ, **context), start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
