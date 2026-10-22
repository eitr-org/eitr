"""Per-user, explicitly approved Git plugins. Plugin commands are always argv."""
import contextlib
import datetime
import fcntl
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from eitr_paths import config, data, state

SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')


def object_keys(value, required, optional=()):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        raise ValueError('Invalid plugin manifest fields')


def string(value, limit=256):
    if not isinstance(value, str) or not value.strip() or len(value) > limit or any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ValueError('Invalid plugin text')
    return value


def identifier(value):
    if not isinstance(value, str) or len(value) > 64 or not SLUG.fullmatch(value):
        raise ValueError('Invalid plugin id')
    return value


def command(root, entry):
    relative = PurePosixPath(string(entry['run']))
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] == '.git':
        raise ValueError('Plugin command must stay inside its folder')
    target = (root / relative).resolve(strict=True)
    if not target.is_relative_to(root.resolve()) or not target.is_file() or not os.access(target, os.X_OK):
        raise ValueError('Plugin command must be an executable inside its folder')
    arguments = entry.get('arguments', [])
    if not isinstance(arguments, list) or len(arguments) > 64:
        raise ValueError('Plugin arguments must be a list of fixed strings')
    for argument in arguments:
        if not isinstance(argument, str) or len(argument) > 4096 or any(ord(character) < 32 or ord(character) == 127 for character in argument):
            raise ValueError('Invalid plugin argument')
    return [str(target), *arguments]


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def manifest(root):
    path = root / 'eitr-plugin.json'
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Invalid plugin manifest file')
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    object_keys(value, ('id', 'name', 'description', 'author', 'version', 'rows'), ('service',))
    identifier(value['id'])
    for field in ('name', 'author', 'version'):
        string(value[field])
    string(value['description'], 72)
    if not isinstance(value['rows'], list) or not 1 <= len(value['rows']) <= 20:
        raise ValueError('A plugin must declare 1..20 rows')
    for row in value['rows']:
        object_keys(row, ('title', 'description', 'run'), ('icon', 'arguments'))
        string(row['title'], 72)
        string(row['description'], 72)
        if 'icon' in row:
            string(row['icon'], 64)
        command(root, row)
    if 'service' in value:
        object_keys(value['service'], ('run',), ('arguments',))
        command(root, value['service'])
    return value


# Private repositories use the person's own SSH keys and ~/.ssh/config aliases:
# git@host:owner/repo.git or ssh://git@host/owner/repo.git.
SSH_SHORT = re.compile(r'[A-Za-z0-9_][A-Za-z0-9_.-]*@[A-Za-z0-9][A-Za-z0-9.-]*:[A-Za-z0-9_][A-Za-z0-9_./-]*\Z')


def repository_url(value, *, allow_file=False):
    string(value, 4096)
    parsed = urlsplit(value)
    if parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password and not parsed.fragment and not parsed.query:
        return value
    if (parsed.scheme == 'ssh' and parsed.hostname and not parsed.password and not parsed.fragment and not parsed.query
            and not parsed.hostname.startswith('-') and parsed.path.startswith('/') and '..' not in parsed.path.split('/')):
        return value
    if '://' not in value and SSH_SHORT.fullmatch(value) and '..' not in value.split(':', 1)[1].split('/'):
        return value
    if allow_file and parsed.scheme == 'file' and not parsed.netloc and parsed.path.startswith('/'):
        return value
    raise ValueError('Plugin repository must be an HTTPS or SSH Git URL without credentials')


def git(root, *arguments, allow_file=False):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
                       GIT_ALLOW_PROTOCOL='https:ssh:file' if allow_file else 'https:ssh',
                       # A passphrase prompt would break the install screen; keys come from the agent.
                       GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                                    '-c', 'submodule.recurse=false', '-c', 'credential.helper=',
                                    *arguments], cwd=root, env=environment, text=True, stderr=subprocess.PIPE, timeout=120).strip()


def clone(url, destination, *, allow_file=False):
    repository_url(url, allow_file=allow_file)
    git(None, 'clone', '--template=', '--no-recurse-submodules', '--', url, str(destination), allow_file=allow_file)


def commit(root):
    return git(root, 'rev-parse', 'HEAD')


def unit_content(root, spec):
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
    argv = command(root, spec['service'])
    return ('[Unit]\nDescription=Eitr plugin ' + spec['id'] + '\n\n[Service]\nType=simple\nExecStart='
            + ' '.join(quote(argument) for argument in argv)
            # A device or network the service needs may not be ready yet when it starts.
            + '\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n')


class Plugins:
    def __init__(self, *, allow_file=False):
        self.folder = data('eitr/plugins')
        self.state = state('eitr/plugins.json')
        self.units = config('systemd/user')
        self.allow_file = allow_file

    @contextlib.contextmanager
    def lock(self):
        if os.geteuid() == 0:
            raise ValueError('Plugins are per-user; do not run as root')
        self.state.parent.mkdir(parents=True, exist_ok=True)
        with self.state.with_suffix('.lock').open('w') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def records(self):
        if not self.state.exists():
            return {}
        value = json.loads(self.state.read_text())
        if not isinstance(value, dict):
            raise ValueError('Invalid plugin state')
        for plugin_id, record in value.items():
            identifier(plugin_id)
            object_keys(record, ('url', 'id', 'commit', 'installed'))
            if record['id'] != plugin_id or not re.fullmatch(r'[0-9a-f]{40,64}', record['commit']):
                raise ValueError('Invalid plugin state')
        return value

    def save(self, records):
        descriptor, temporary = tempfile.mkstemp(dir=self.state.parent, prefix='.plugins-')
        try:
            with os.fdopen(descriptor, 'w') as handle:
                json.dump(records, handle, indent=2)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.state)
        finally:
            Path(temporary).unlink(missing_ok=True)
        # The search index contains labels only; remove it so the next open rebuilds it.
        runtime = os.environ.get('XDG_RUNTIME_DIR')
        if runtime:
            with contextlib.suppress(OSError):
                (Path(runtime) / 'eitr-search/index.json').unlink(missing_ok=True)

    def unit(self, plugin_id):
        return self.units / f'eitr-plugin-{identifier(plugin_id)}.service'

    def systemctl(self, *arguments):
        subprocess.run(['systemctl', '--user', *arguments], check=True, capture_output=True, text=True)

    def service(self, plugin_id, spec=None):
        unit = self.unit(plugin_id)
        if unit.exists():
            self.systemctl('disable', '--now', unit.name)
            unit.unlink()
        if spec and 'service' in spec:
            self.units.mkdir(parents=True, exist_ok=True)
            unit.write_text(unit_content(self.folder / plugin_id, spec))
        self.systemctl('daemon-reload')
        if spec and 'service' in spec:
            self.systemctl('enable', '--now', unit.name)

    def prepare(self, url, temporary):
        candidate = temporary / 'candidate'
        clone(url, candidate, allow_file=self.allow_file)
        spec = manifest(candidate)
        return candidate, spec

    def add(self, url, approve):
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            candidate, spec = self.prepare(url, Path(temporary))
            plugin_id = spec['id']
            target = self.folder / plugin_id
            if plugin_id in records or target.exists() or target.is_symlink() or self.unit(plugin_id).exists():
                raise ValueError('Plugin id or service already exists')
            approved = commit(candidate)
            if not approve(candidate, spec, url):
                return False
            self.folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copytree(candidate, target, symlinks=True)
                if manifest(target) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in spec:
                    self.service(plugin_id, spec)
                records[plugin_id] = dict(url=url, id=plugin_id, commit=approved,
                                         installed=datetime.datetime.now(datetime.timezone.utc).isoformat())
                self.save(records)
            except BaseException:
                if self.unit(plugin_id).exists():
                    with contextlib.suppress(OSError, subprocess.SubprocessError):
                        self.service(plugin_id)
                if target.exists():
                    shutil.rmtree(target)
                raise
            return True

    def update(self, plugin_id, approve):
        identifier(plugin_id)
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            record = records[plugin_id]
            target = self.folder / plugin_id
            if target.is_symlink() or commit(target) != record['commit']:
                raise ValueError('Installed plugin differs from its approved commit')
            # Fetch into a disposable clone: hooks and unapproved worktree never run.
            candidate, spec = self.prepare(record['url'], Path(temporary))
            git(candidate, 'fetch', '--no-recurse-submodules', 'origin', allow_file=self.allow_file)
            new_commit = commit(candidate)
            if new_commit == record['commit']:
                return False
            if spec['id'] != plugin_id:
                raise ValueError('Plugin id cannot change during update')
            subjects = git(candidate, 'log', '--format=%h %s', record['commit'] + '..' + new_commit)
            changed = git(candidate, 'diff', '--name-status', record['commit'], new_commit)
            if not approve(spec, record['commit'], new_commit, subjects, changed):
                return False
            replacement = self.folder / ('.' + plugin_id + '-new')
            backup = self.folder / ('.' + plugin_id + '-previous')
            if replacement.exists() or backup.exists():
                raise ValueError('An interrupted plugin update needs recovery')
            old_spec = manifest(target)
            try:
                shutil.copytree(candidate, replacement, symlinks=True)
                if manifest(replacement) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in old_spec:
                    self.systemctl('stop', self.unit(plugin_id).name)
                target.rename(backup)
                replacement.rename(target)
                if 'service' in spec or 'service' in old_spec:
                    self.service(plugin_id, spec)
                self.save({**records, plugin_id: {**record, 'commit': new_commit}})
            except BaseException:
                if backup.exists():
                    if self.unit(plugin_id).exists():
                        with contextlib.suppress(OSError, subprocess.SubprocessError):
                            self.systemctl('stop', self.unit(plugin_id).name)
                    if target.exists():
                        shutil.rmtree(target)
                    backup.rename(target)
                    if 'service' in old_spec or 'service' in spec:
                        with contextlib.suppress(OSError, subprocess.SubprocessError):
                            self.service(plugin_id, old_spec)
                if replacement.exists():
                    shutil.rmtree(replacement)
                raise
            shutil.rmtree(backup)
            return True

    def remove(self, plugin_id, approve):
        identifier(plugin_id)
        with self.lock():
            records = self.records()
            record = records[plugin_id]
            if not approve(record):
                return False
            target = self.folder / plugin_id
            if target.is_symlink():
                raise ValueError('Plugin folder must not be a symlink')
            if self.unit(plugin_id).exists():
                self.service(plugin_id)
            if target.exists():
                shutil.rmtree(target)
            del records[plugin_id]
            self.save(records)
            return True

    def rows(self):
        rows = []
        for plugin_id, record in self.records().items():
            root = self.folder / plugin_id
            try:
                if root.is_symlink() or commit(root) != record['commit']:
                    continue
                spec = manifest(root)
                for index, row in enumerate(spec['rows']):
                    rows.append(dict(id=plugin_id, index=index, title=row['title'], description=row['description'], icon=row.get('icon', '󰏖')))
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        return sorted(rows, key=lambda row: row['title'].casefold())

    def launch(self, plugin_id, index):
        if os.geteuid() == 0:
            raise ValueError('Plugins are per-user; do not run as root')
        record = self.records()[identifier(plugin_id)]
        root = self.folder / plugin_id
        if root.is_symlink() or commit(root) != record['commit']:
            raise ValueError('Plugin differs from its approved commit')
        spec = manifest(root)
        subprocess.Popen(command(root, spec['rows'][index]), cwd=root, start_new_session=True)
