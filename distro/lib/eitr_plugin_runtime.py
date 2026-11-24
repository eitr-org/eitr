"""Approved plugin services, hooks, commands and visual runtime state."""
from contextlib import suppress
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import tempfile

import eitr_policy
from eitr_paths import cache, state
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
)
from eitr_plugin_placements import PluginPlacements
from eitr_plugin_bundled import BundledPlugins


HOOK_TIMEOUT = 30
UI_FAILURE_LIMIT = 3

def plugin_environment():
    """The desktop's environment for a plugin command, which never writes bytecode into its reviewed folder."""
    return dict(os.environ, PYTHONDONTWRITEBYTECODE='1')


def unit_content(root, spec):
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
    argv = command(root, spec['service'])
    return ('[Unit]\nDescription=Eitr plugin ' + spec['id'] + '\n\n[Service]\nType=simple\nExecStart='
            + ' '.join(quote(argument) for argument in argv)
            + '\nNoNewPrivileges=yes\nEnvironment=PYTHONDONTWRITEBYTECODE=1'
            # A device or network the service needs may not be ready yet when it starts.
            + '\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n')


def prune_ui_revisions(folder, current=None):
    """Keep the most recently served other revision for a bar still using its URLs."""
    older = [path for path in folder.iterdir() if path != current and not path.is_symlink()
             and path.is_dir() and re.fullmatch(r'[0-9a-f]{40,64}', path.name)]
    for revision in sorted(older, key=lambda path: path.stat().st_mtime_ns, reverse=True)[1:]:
        shutil.rmtree(revision)


def stage_ui(folder, revision, root, files):
    if folder.parent.is_symlink() or folder.is_symlink():
        raise ValueError('Invalid plugin UI cache directory')
    target = folder / revision
    if target.is_symlink():
        raise ValueError('Invalid plugin UI revision directory')
    if not target.is_dir():
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.stage-', dir=folder) as temporary:
            staging = Path(temporary)
            for original in files:
                if not original.is_file():
                    raise ValueError('Plugin UI staging requires regular files')
                destination = staging / original.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                try:
                    os.link(original, destination)
                except OSError:
                    shutil.copy2(original, destination)
            staging.rename(target)
    os.utime(target)
    with suppress(OSError):
        prune_ui_revisions(folder, target)
    return target


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

    def ui(self, *, stage=True):
        """Approved declarations; stage their source URLs for visual consumers."""
        if not stage:
            return self._ui_entries()
        with self.lock():
            return self._ui_entries(cache('eitr/plugin-ui'))

    def _ui_entries(self, ui_cache=None):
        records = self.records()
        blocked = self.blocked()
        failures = self.ui_state()
        result = []
        for plugin_id, record in records.items():
            if plugin_id in blocked:
                continue
            root = self.root(plugin_id, record=record)
            try:
                if root.is_symlink() or commit(root) != record['commit']:
                    continue
                files = list(plugin_files(root))
                spec = manifest(root)
                if not any(spec.get('ui', {}).values()):
                    continue
                source_root = stage_ui(ui_cache / plugin_id, record['commit'], root, files) if ui_cache is not None else None
                for kind in ('tiles', 'panels', 'widgets', 'barItems'):
                    for entry in spec.get('ui', {}).get(kind, []):
                        visual = dict(plugin=plugin_id, pluginName=spec['name'], bundled=bool(record.get('bundled')),
                                      commit=record['commit'], kind=kind,
                                      placement={'widgets': 'desktop', 'barItems': 'bar'}.get(kind, 'control-center'),
                                      disabled=bool(failures.get(plugin_id, {}).get('disabled')),
                                      **entry, capabilities=spec.get('capabilities', []))
                        if source_root is not None:
                            visual['source'] = (source_root / entry['qml']).as_uri()
                        result.append(visual)
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        if ui_cache is not None and not ui_cache.is_symlink() and ui_cache.is_dir():
            with suppress(OSError):
                for folder in ui_cache.iterdir():
                    if folder.name not in records and not folder.is_symlink() and folder.is_dir():
                        prune_ui_revisions(folder)
        return result

    def ui_data(self, plugin_id, entry_id):
        entry = next((entry for entry in self.ui(stage=False) if entry['plugin'] == plugin_id and entry['id'] == entry_id), None)
        if not entry or entry['disabled'] or 'dataCommand' not in entry:
            raise ValueError('Plugin data command is unavailable')
        root = self.root(plugin_id)
        # A temporary file bounds memory even when a command writes excessive output.
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(command(root, entry['dataCommand']), cwd=root, start_new_session=True,
                                       env=plugin_environment(), stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.DEVNULL)
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
        """Run approved event hooks with a timeout for each hook."""
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
                    environment['PYTHONDONTWRITEBYTECODE'] = '1'
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
        subprocess.Popen(command(root, spec['rows'][index]), cwd=root, env=plugin_environment(), start_new_session=True)


class Plugins(BundledPlugins, _PluginInstall, PluginRuntime, PluginPlacements):
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
