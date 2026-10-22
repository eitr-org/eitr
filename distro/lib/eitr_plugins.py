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

import eitr_policy
from eitr_i18n import tr
from eitr_paths import config, data, state

SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
COMMIT = re.compile(r'[0-9a-f]{40}(?:[0-9a-f]{24})?\Z')
# Shipped in the signed eitr-desktop package, beside lib/ (distro/ in a checkout).
BLOCKLIST = Path(__file__).resolve().parents[1] / 'plugin-blocklist.json'
REPORT_URL = 'https://github.com/eitr-org/eitr/issues/new?template=malicious-plugin.yml'


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


def normalized_url(value):
    """One spelling per repository: host and path, without scheme, user, port, .git or case."""
    if '://' not in value and SSH_SHORT.fullmatch(value):
        host, path = value.split('@', 1)[1].split(':', 1)
    else:
        parsed = urlsplit(value)
        host, path = parsed.hostname or '', parsed.path
    path = path.strip('/').removesuffix('.git').rstrip('/')
    return (host + '/' + path).casefold()


def printable(text):
    return ''.join(character if character.isprintable() else '?' for character in text)


def short_author(spec, limit=24):
    author = printable(spec['author'])
    return author if len(author) <= limit else author[:limit - 1] + '…'


def git(root, *arguments, allow_file=False):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
                       GIT_ALLOW_PROTOCOL='https:ssh:file' if allow_file else 'https:ssh',
                       # A passphrase prompt would break the install screen; keys come from the agent.
                       GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    return subprocess.check_output(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                                    '-c', 'submodule.recurse=false', '-c', 'credential.helper=',
                                    *arguments], cwd=root, env=environment, text=True, stdin=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, timeout=120).strip()


def clone(url, destination, *, allow_file=False):
    repository_url(url, allow_file=allow_file)
    git(None, 'clone', '--template=', '--no-recurse-submodules', '--', url, str(destination), allow_file=allow_file)


def commit(root):
    return git(root, 'rev-parse', 'HEAD')


def plugin_files(root):
    """Every file outside Git's metadata; a symlink anywhere is refused."""
    root = Path(root)
    for folder, directories, files in os.walk(root):
        current = Path(folder)
        if current == root:
            directories[:] = [name for name in directories if name != '.git']
        for name in directories + files:
            path = current / name
            if path.is_symlink():
                raise ValueError(tr('Plugins may not contain symlinks: {path}', path=printable(str(path.relative_to(root)))))
        yield from (current / name for name in files)


def executable_files(root):
    return sorted(str(path.relative_to(root)) for path in plugin_files(root) if path.stat().st_mode & 0o111)


def binary_files(root):
    # Git's own rule: a NUL byte in the first 8000 bytes means binary.
    binary = []
    for path in plugin_files(root):
        with path.open('rb') as stream:
            if b'\0' in stream.read(8000):
                binary.append(str(path.relative_to(root)))
    return sorted(binary)


def service_text(spec):
    service = spec['service']
    return printable(' '.join([service['run'], *service.get('arguments', [])]))


def add_flags(root, spec):
    flags = []
    if 'service' in spec:
        flags.append(tr('Starts a background service at every login: {command}', command=service_text(spec)))
    flags.extend(tr('Binary file: {path}', path=printable(path)) for path in binary_files(root))
    return flags


def update_changes(candidate, target, old, new, old_spec, spec):
    """What an update changes and the risks worth a second look, read from the Git history."""
    subjects = [printable(line) for line in git(candidate, 'log', '--format=%h %s', old + '..' + new).splitlines()]
    counts = {}
    for item in git(candidate, 'diff', '--numstat', '-z', '--no-renames', '--no-ext-diff', '--no-textconv', old, new).split('\0'):
        if item:
            added, removed, path = item.split('\t', 2)
            counts[path] = (added, removed)
    raw = git(candidate, 'diff', '--raw', '-z', '--no-renames', '--no-abbrev', old, new).split('\0')
    files = []
    for header, path in zip(raw[0::2], raw[1::2]):
        old_mode, new_mode, _, _, status = header.lstrip(':').split(' ')
        added, removed = counts.get(path, ('0', '0'))
        files.append(dict(path=printable(path), status=status, old_mode=old_mode, new_mode=new_mode,
                          added=added, removed=removed, binary=added == '-'))
    flags = []
    if old_spec.get('service') != spec.get('service'):
        if 'service' not in old_spec:
            flags.append(tr('Background service added: {command}', command=service_text(spec)))
        elif 'service' not in spec:
            flags.append(tr('Background service removed'))
        else:
            flags.append(tr('Background service changed: {command}', command=service_text(spec)))
    if any(change['path'] == 'eitr-plugin.json' for change in files):
        flags.append(tr('Manifest changed: {path}', path='eitr-plugin.json'))
    for change in files:
        if change['new_mode'] == '100755':
            if change['status'] == 'A':
                flags.append(tr('New executable file: {path}', path=change['path']))
            elif change['old_mode'] != '100755':
                flags.append(tr('File became executable: {path}', path=change['path']))
            else:
                flags.append(tr('Changed executable file: {path}', path=change['path']))
        if change['binary']:
            flags.append(tr('Binary file: {path}', path=change['path']))
    approved_author = git(target, 'show', '-s', '--format=%ae', 'HEAD').casefold()
    authors = []
    for line in git(candidate, 'log', '--format=%ae%x09%an', old + '..' + new).splitlines():
        email, _, name = line.partition('\t')
        author = printable(f'{name} <{email}>')
        if email.casefold() != approved_author and author not in authors:
            authors.append(author)
    flags.extend(tr('Commit by a different author than the approved one: {author}', author=author) for author in authors)
    return dict(spec=spec, old_spec=old_spec, old=old, new=new, subjects=subjects, files=files, flags=flags, root=candidate)


def blocklist(path=None):
    """The kill switch shipped, and signed, with eitr-desktop. Anything unexpected refuses plugins."""
    try:
        value = json.loads(Path(path or BLOCKLIST).read_text(), object_pairs_hook=unique_object)
        object_keys(value, ('version', 'entries'))
        if type(value['version']) is not int or value['version'] != 1 or not isinstance(value['entries'], list):
            raise ValueError('Unsupported plugin blocklist')
        entries = []
        for entry in value['entries']:
            object_keys(entry, ('reason', 'date'), ('url', 'commit', 'id'))
            kinds = [kind for kind in ('url', 'commit', 'id') if kind in entry]
            if len(kinds) != 1:
                raise ValueError('A blocklist entry names exactly one url, commit or id')
            string(entry['reason'], 300)
            if not isinstance(entry['date'], str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', entry['date']):
                raise ValueError('Blocklist dates use YYYY-MM-DD')
            datetime.date.fromisoformat(entry['date'])
            kind, match = kinds[0], entry[kinds[0]]
            if kind == 'url':
                match = normalized_url(repository_url(match))
            elif kind == 'commit' and (not isinstance(match, str) or not COMMIT.fullmatch(match)):
                raise ValueError('Blocklist commits are full lowercase hashes')
            elif kind == 'id':
                identifier(match)
            entries.append((kind, match, entry['reason']))
        return entries
    except (OSError, ValueError, TypeError) as error:
        raise ValueError(tr('The plugin blocklist could not be read; plugins are refused until it is fixed.')) from error


def blocked_reason(entries, url=None, commit=None, plugin_id=None):
    wanted = dict(url=normalized_url(url) if url else None, commit=commit, id=plugin_id)
    return next((reason for kind, match, reason in entries if wanted[kind] == match), None)


def policy_reason(url):
    value = eitr_policy.load().get('plugins', True)
    if value is False:
        return tr('Plugins are turned off by your organization.')
    if isinstance(value, dict) and normalized_url(url) not in {normalized_url(item) for item in value.get('allow', [])}:
        return tr('Your organization allows plugins only from its approved repositories.')
    return None


def unit_content(root, spec):
    def quote(value):
        return '"' + value.replace('\\', '\\\\').replace('"', '\\"').replace('%', '%%').replace('$', '$$') + '"'
    argv = command(root, spec['service'])
    return ('[Unit]\nDescription=Eitr plugin ' + spec['id'] + '\n\n[Service]\nType=simple\nExecStart='
            + ' '.join(quote(argument) for argument in argv)
            + '\nNoNewPrivileges=yes'
            # A device or network the service needs may not be ready yet when it starts.
            + '\nRestart=on-failure\nRestartSec=5\n\n[Install]\nWantedBy=default.target\n')


class Plugins:
    def __init__(self, *, allow_file=False, notify=None):
        self.folder = data('eitr/plugins')
        self.state = state('eitr/plugins.json')
        self.notices = state('eitr/plugins-blocked.json')
        self.units = config('systemd/user')
        self.allow_file = allow_file
        # notify(plugin_id, name, kind, reason) tells the person about a blocked plugin; True once shown.
        self.notify = notify

    @contextlib.contextmanager
    def lock(self, blocking=True):
        if os.geteuid() == 0:
            raise ValueError('Plugins are per-user; do not run as root')
        self.state.parent.mkdir(parents=True, exist_ok=True)
        with self.state.with_suffix('.lock').open('w') as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX if blocking else fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                yield False
                return
            yield True

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

    def write(self, path, value):
        descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix='.plugins-')
        try:
            with os.fdopen(descriptor, 'w') as handle:
                json.dump(value, handle, indent=2)
                handle.write('\n')
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            Path(temporary).unlink(missing_ok=True)

    def save(self, records):
        self.write(self.state, records)
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

    def refusal(self, url, commit=None, plugin_id=None):
        """('policy' or 'blocklist', reason) when this repository, commit or id may not be used."""
        reason = policy_reason(url)
        if reason:
            return 'policy', reason
        reason = blocked_reason(blocklist(), url, commit, plugin_id)
        return ('blocklist', reason) if reason else None

    def check(self, url, commit=None, plugin_id=None):
        refused = self.refusal(url, commit, plugin_id)
        if refused:
            kind, reason = refused
            raise ValueError(reason if kind == 'policy' else tr('This plugin is on the Eitr blocklist: {reason}', reason=reason))

    def blocked(self):
        """Installed plugins that may no longer run, by id."""
        result = {}
        for plugin_id, record in self.records().items():
            refused = self.refusal(record['url'], record['commit'], plugin_id)
            if refused:
                result[plugin_id] = refused
        return result

    def spec(self, plugin_id):
        try:
            return manifest(self.folder / plugin_id)
        except (OSError, ValueError):
            return None

    def stop(self, plugin_id):
        unit = self.unit(plugin_id)
        if not unit.exists():
            return
        try:
            self.systemctl('disable', '--now', unit.name)
        except (OSError, subprocess.SubprocessError):
            # Without a running user manager, disabling is removing its login link.
            (self.units / 'default.target.wants' / unit.name).unlink(missing_ok=True)

    def enforce(self, blocking=True):
        """Stop the services of blocked plugins, keep their files and tell the person once."""
        blocked = self.blocked()
        with self.lock(blocking) as locked:
            if not locked:
                return blocked
            try:
                notices = json.loads(self.notices.read_text())
                if not isinstance(notices, dict):
                    notices = {}
            except (OSError, ValueError):
                notices = {}
            updated = {}
            for plugin_id, (kind, reason) in blocked.items():
                notice = notices.get(plugin_id)
                if not isinstance(notice, dict) or notice.get('reason') != reason:
                    self.stop(plugin_id)
                    notice = dict(kind=kind, reason=reason, notified=False)
                if not notice.get('notified') and self.notify:
                    spec = self.spec(plugin_id)
                    if self.notify(plugin_id, printable(spec['name']) if spec else plugin_id, kind, reason):
                        notice = {**notice, 'notified': True}
                updated[plugin_id] = notice
            if updated != notices:
                self.write(self.notices, updated)
        return blocked

    def prepare(self, url, temporary):
        candidate = temporary / 'candidate'
        clone(url, candidate, allow_file=self.allow_file)
        list(plugin_files(candidate))
        spec = manifest(candidate)
        return candidate, spec

    def add(self, url, consent, approve):
        """consent(url) accepts the risk before anything is downloaded; approve() the exact commit."""
        repository_url(url, allow_file=self.allow_file)
        self.check(url)
        if not consent(url):
            return False
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            candidate, spec = self.prepare(url, Path(temporary))
            plugin_id = spec['id']
            target = self.folder / plugin_id
            if plugin_id in records or target.exists() or target.is_symlink() or self.unit(plugin_id).exists():
                raise ValueError('Plugin id or service already exists')
            approved = commit(candidate)
            self.check(url, approved, plugin_id)
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
        """approve(changes) sees update_changes(); a rewritten history is refused before it."""
        identifier(plugin_id)
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            record = records[plugin_id]
            self.check(record['url'], plugin_id=plugin_id)
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
            self.check(record['url'], new_commit, plugin_id)
            try:
                git(candidate, 'merge-base', '--is-ancestor', record['commit'], new_commit)
            except subprocess.CalledProcessError:
                raise ValueError(tr('The history of {id} was rewritten: the approved commit {commit} is not part of the new one. '
                                    'Eitr does not update it automatically. If you still trust its author, remove the plugin and add it again.',
                                    id=plugin_id, commit=record['commit'][:12])) from None
            old_spec = manifest(target)
            if not approve(update_changes(candidate, target, record['commit'], new_commit, old_spec, spec)):
                return False
            replacement = self.folder / ('.' + plugin_id + '-new')
            backup = self.folder / ('.' + plugin_id + '-previous')
            if replacement.exists() or backup.exists():
                raise ValueError('An interrupted plugin update needs recovery')
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

    def installed(self):
        """Install > Plugins: every plugin, with its manifest author and whether it is blocked."""
        blocked = self.blocked()
        rows = []
        for plugin_id in self.records():
            spec = self.spec(plugin_id)
            rows.append(dict(id=plugin_id, name=printable(spec['name']) if spec else plugin_id,
                             author=short_author(spec) if spec else '?', blocked=blocked.get(plugin_id, ('',))[0]))
        return sorted(rows, key=lambda row: row['name'].casefold())

    def rows(self):
        blocked = self.enforce(blocking=False)
        rows = []
        for plugin_id, record in self.records().items():
            if plugin_id in blocked:
                continue
            root = self.folder / plugin_id
            try:
                if root.is_symlink() or commit(root) != record['commit']:
                    continue
                spec = manifest(root)
                for index, row in enumerate(spec['rows']):
                    rows.append(dict(id=plugin_id, index=index, title=row['title'], description=row['description'],
                                     author=short_author(spec), icon=row.get('icon', '󰏖')))
            except (OSError, ValueError, subprocess.SubprocessError):
                continue
        return sorted(rows, key=lambda row: row['title'].casefold())

    def launch(self, plugin_id, index):
        if os.geteuid() == 0:
            raise ValueError('Plugins are per-user; do not run as root')
        record = self.records()[identifier(plugin_id)]
        if self.refusal(record['url'], record['commit'], plugin_id):
            self.enforce()
            self.check(record['url'], record['commit'], plugin_id)
        root = self.folder / plugin_id
        if root.is_symlink() or commit(root) != record['commit']:
            raise ValueError('Plugin differs from its approved commit')
        spec = manifest(root)
        subprocess.Popen(command(root, spec['rows'][index]), cwd=root, start_new_session=True)
