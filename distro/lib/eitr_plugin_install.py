"""Plugin Git operations, approval transactions and persistent installation state."""
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

import eitr_policy
from eitr_i18n import mark, tr
from eitr_paths import config, data, state
from eitr_plugin_manifest import (
    identifier,
    manifest,
    object_keys,
    plugin_files,
    printable,
    qml_files,
    repository_plugins,
    string,
    unique_object,
)


COMMIT = re.compile(r'[0-9a-f]{40}(?:[0-9a-f]{24})?\Z')
# Shipped in the signed eitr-desktop package, beside lib/ (distro/ in a checkout).
BLOCKLIST = Path(__file__).resolve().parents[1] / 'plugin-blocklist.json'
REPORT_URL = 'https://github.com/eitr-org/eitr/issues/new?template=malicious-plugin.yml'


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


# Eitr's own plugin repository; trust follows its address, never a manifest's author field.
OFFICIAL_REPOSITORY = 'github.com/eitr-org/eitr-plugins'


def official(url):
    return normalized_url(url) == OFFICIAL_REPOSITORY


ALREADY_INSTALLED = mark('This plugin is already installed. Update or remove it from Control Center > Plugins.')
ALL_INSTALLED = mark('Every plugin in this repository is already installed. Update or remove them from Control Center > Plugins.')

def normalized_url(value):
    """One spelling per repository: host and path, without scheme, user, port, .git or case."""
    if '://' not in value and SSH_SHORT.fullmatch(value):
        host, path = value.split('@', 1)[1].split(':', 1)
    else:
        parsed = urlsplit(value)
        host, path = parsed.hostname or '', parsed.path
    path = path.strip('/').removesuffix('.git').rstrip('/')
    return (host + '/' + path).casefold()


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
    flags = [tr('QML runs inside the bar: {path}', path=printable(str(path.relative_to(root)))) for path in qml_files(root)]
    if 'service' in spec:
        flags.append(tr('Starts a background service at every login: {command}', command=service_text(spec)))
    flags.extend(tr('Binary file: {path}', path=printable(path)) for path in binary_files(root))
    flags.extend(live_flags(spec))
    return flags


def live_flags(spec, previous=None):
    flags = []
    if 'audio-spectrum' in spec.get('capabilities', []) and 'audio-spectrum' not in (previous or {}).get('capabilities', []):
        flags.append(tr('Reads the system audio spectrum (levels only, no audio is recorded or sent)'))
    for kind, entries in spec.get('ui', {}).items():
        for entry in entries:
            old = next((item for item in (previous or {}).get('ui', {}).get(kind, []) if item['id'] == entry['id']), {})
            for field in ('dataCommand', 'dataStream'):
                if field in entry and entry[field] != old.get(field):
                    flags.append(tr('Live data command added or changed: {kind} · {id} · {command}', kind=field, id=entry['id'], command=printable(' '.join([entry[field]['run'], *entry[field].get('arguments', [])]))))
    return flags


def update_changes(candidate, target, old, new, old_spec, spec):
    """What an update changes and the risks worth a second look, read from the Git history."""
    subjects = [printable(line) for line in git(candidate, 'log', '--format=%h %s', old + '..' + new).splitlines()]
    counts = {}
    for item in git(candidate, 'diff', '--numstat', '--relative', '-z', '--no-renames', '--no-ext-diff', '--no-textconv', old, new).split('\0'):
        if item:
            added, removed, path = item.split('\t', 2)
            counts[path] = (added, removed)
    raw = git(candidate, 'diff', '--raw', '--relative', '-z', '--no-renames', '--no-abbrev', old, new).split('\0')
    files = []
    for header, path in zip(raw[0::2], raw[1::2]):
        old_mode, new_mode, _, _, status = header.lstrip(':').split(' ')
        added, removed = counts.get(path, ('0', '0'))
        files.append(dict(path=printable(path), status=status, old_mode=old_mode, new_mode=new_mode,
                          added=added, removed=removed, binary=added == '-'))
    flags = live_flags(spec, old_spec)
    if old_spec.get('service') != spec.get('service'):
        if 'service' not in old_spec:
            flags.append(tr('Background service added: {command}', command=service_text(spec)))
        elif 'service' not in spec:
            flags.append(tr('Background service removed'))
        else:
            flags.append(tr('Background service changed: {command}', command=service_text(spec)))
    for event, hook in spec.get('hooks', {}).items():
        if old_spec.get('hooks', {}).get(event) != hook:
            flags.append(tr('Event hook added or changed: {event}', event=event))
    if any(change['path'] == 'eitr-plugin.json' for change in files):
        flags.append(tr('Manifest changed: {path}', path='eitr-plugin.json'))
    for change in files:
        if change['path'].casefold().endswith('.qml'):
            flags.append(tr('QML added, changed or removed: {path}', path=change['path']))
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




class PluginInstall:
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
            object_keys(record, ('url', 'id', 'commit', 'installed'), ('enabled', 'path'))
            if 'path' in record:
                relative = record['path']
                if not isinstance(relative, str) or not relative or PurePosixPath(relative).is_absolute() or '..' in PurePosixPath(relative).parts or '\\' in relative or str(PurePosixPath(relative)) != relative:
                    raise ValueError('Invalid plugin repository path')
            if type(record.get('enabled', True)) is not bool:
                raise ValueError('Invalid plugin enabled state')
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

    def snapshot(self, url, revision):
        source = hashlib.sha256(normalized_url(url).encode()).hexdigest()
        return self.folder / '.repositories' / source / revision

    def root(self, plugin_id):
        record = self.records().get(plugin_id, {})
        if record.get('path'):
            return self.snapshot(record['url'], record['commit']) / record['path']
        return self.folder / plugin_id

    def keep_snapshot(self, candidate, url, revision):
        target = self.snapshot(url, revision)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, target, symlinks=True)
        if target.is_symlink() or commit(target) != revision:
            raise ValueError('Repository snapshot differs from its approved commit')
        return target

    def clean_snapshots(self):
        retained = {self.snapshot(record['url'], record['commit']) for record in self.records().values() if record.get('path')}
        parent = self.folder / '.repositories'
        if parent.exists():
            for source in parent.iterdir():
                if source.is_symlink() or not source.is_dir():
                    raise ValueError('Invalid plugin repository storage')
                for snapshot in source.iterdir():
                    if snapshot not in retained:
                        if snapshot.is_symlink() or not snapshot.is_dir():
                            raise ValueError('Invalid plugin repository snapshot')
                        shutil.rmtree(snapshot)
                if not any(source.iterdir()):
                    source.rmdir()

    def refusal(self, url, commit=None, plugin_id=None, *, include_disabled=True):
        """('policy' or 'blocklist', reason) when this repository, commit or id may not be used."""
        if include_disabled and plugin_id and not self.records().get(plugin_id, {}).get('enabled', True):
            return 'disabled', 'Plugin disabled'
        reason = policy_reason(url)
        if reason:
            return 'policy', reason
        reason = blocked_reason(blocklist(), url, commit, plugin_id)
        return ('blocklist', reason) if reason else None

    def check(self, url, commit=None, plugin_id=None):
        refused = self.refusal(url, commit, plugin_id, include_disabled=False)
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
            return manifest(self.root(plugin_id))
        except (OSError, ValueError):
            return None

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
                if kind == 'disabled':
                    continue
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
        entries = repository_plugins(candidate)
        return candidate, entries if entries[0]["path"] else entries[0]["spec"]

    def add(self, url, consent, approve, pick=None):
        """consent(url) accepts the risk before anything is downloaded; approve() the exact commit."""
        repository_url(url, allow_file=self.allow_file)
        self.check(url)
        # A single-plugin repository installed earlier is recognised before anything is downloaded.
        if any(normalized_url(record['url']) == normalized_url(url) and not record.get('path')
               for record in self.records().values()):
            raise ValueError(tr(ALREADY_INSTALLED))
        if not consent(url):
            return False
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            candidate, spec = self.prepare(url, Path(temporary))
            if isinstance(spec, list):
                return self.add_indexed(candidate, spec, url, records, approve, pick)
            if spec.get('schemaVersion') == 2 and 'icon' not in spec:
                raise ValueError('Schema version 2 requires a plugin icon')
            plugin_id = spec['id']
            target = self.root(plugin_id)
            if plugin_id in records:
                raise ValueError(tr(ALREADY_INSTALLED))
            if target.exists() or target.is_symlink() or self.unit(plugin_id).exists():
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

    def add_indexed(self, candidate, entries, url, records, approve, pick):
        if pick is None:
            raise ValueError('Choose plugins from this repository before installing')
        entries = [{**entry, 'installed': entry['spec']['id'] in records} for entry in entries]
        if all(entry['installed'] for entry in entries):
            raise ValueError(tr(ALL_INSTALLED))
        choices = pick(entries)
        if not isinstance(choices, list) or any(not isinstance(choice, str) for choice in choices) or len(choices) != len(set(choices)):
            raise ValueError('Invalid plugin selection')
        available = {entry['spec']['id']: entry for entry in entries}
        if set(choices) - available.keys():
            raise ValueError('Unknown plugin selection')
        if any(available[choice]['installed'] for choice in choices):
            raise ValueError(tr(ALREADY_INSTALLED))
        revision = commit(candidate)
        installed = False
        try:
            for plugin_id in choices:
                entry = available[plugin_id]
                spec = entry['spec']
                if plugin_id in records or (self.folder / plugin_id).exists() or self.unit(plugin_id).exists():
                    raise ValueError('Plugin id or service already exists')
                if spec.get('schemaVersion') == 2 and 'icon' not in spec:
                    raise ValueError('Schema version 2 requires a plugin icon')
                self.check(url, revision, plugin_id)
                if not approve(candidate / entry['path'], spec, url):
                    continue
                snapshot = self.keep_snapshot(candidate, url, revision)
                root = snapshot / entry['path']
                if manifest(root) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                record = dict(url=url, id=plugin_id, commit=revision, path=entry['path'],
                              installed=datetime.datetime.now(datetime.timezone.utc).isoformat())
                try:
                    if 'service' in spec:
                        self.service(plugin_id, spec, root=root)
                    self.save({**records, plugin_id: record})
                except BaseException:
                    if self.unit(plugin_id).exists():
                        with contextlib.suppress(OSError, subprocess.SubprocessError):
                            self.service(plugin_id)
                    raise
                records[plugin_id] = record
                installed = True
        finally:
            self.clean_snapshots()
        return installed

    def update_indexed(self, plugin_id, record, records, approve):
        target = self.root(plugin_id)
        if target.is_symlink() or commit(target) != record['commit']:
            raise ValueError('Installed plugin differs from its approved commit')
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            candidate, entries = self.prepare(record['url'], Path(temporary))
            if not isinstance(entries, list):
                raise ValueError('Installed plugin is missing from the repository index')
            entry = next((entry for entry in entries if entry['spec']['id'] == plugin_id), None)
            if entry is None or entry['path'] != record['path']:
                raise ValueError('Installed plugin path cannot change during update')
            revision = commit(candidate)
            if revision == record['commit']:
                return False
            self.check(record['url'], revision, plugin_id)
            try:
                git(candidate, 'merge-base', '--is-ancestor', record['commit'], revision)
            except subprocess.CalledProcessError:
                raise ValueError('Plugin repository history was rewritten') from None
            if (git(candidate, 'rev-parse', record['commit'] + ':' + record['path'])
                    == git(candidate, 'rev-parse', revision + ':' + record['path'])):
                return False
            old_spec, spec = manifest(target), entry['spec']
            if spec.get('schemaVersion') == 2 and 'icon' not in spec:
                raise ValueError('Schema version 2 requires a plugin icon')
            changes = update_changes(candidate / entry['path'], target, record['commit'], revision, old_spec, spec)
            changes['official'] = official(record['url'])
            if not approve(changes):
                return False
            snapshot = self.keep_snapshot(candidate, record['url'], revision)
            root = snapshot / entry['path']
            try:
                if manifest(root) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in spec or 'service' in old_spec:
                    self.service(plugin_id, spec if record.get('enabled', True) else None, root=root)
                self.save({**records, plugin_id: {**record, 'commit': revision}})
            except BaseException:
                if 'service' in spec or 'service' in old_spec:
                    with contextlib.suppress(OSError, subprocess.SubprocessError):
                        self.service(plugin_id, old_spec if record.get('enabled', True) else None, root=target)
                raise
            finally:
                self.clean_snapshots()
            return True

    def update(self, plugin_id, approve):
        """approve(changes) sees update_changes(); a rewritten history is refused before it."""
        identifier(plugin_id)
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-plugin-') as temporary:
            records = self.records()
            record = records[plugin_id]
            self.check(record['url'], plugin_id=plugin_id)
            if record.get('path'):
                return self.update_indexed(plugin_id, record, records, approve)
            target = self.root(plugin_id)
            if target.is_symlink() or commit(target) != record['commit']:
                raise ValueError('Installed plugin differs from its approved commit')
            # Fetch into a disposable clone: hooks and unapproved worktree never run.
            candidate, spec = self.prepare(record['url'], Path(temporary))
            if isinstance(spec, list):
                raise ValueError('Single-plugin repository changed to an index; remove and add it again')
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
            if spec.get('schemaVersion') == 2 and 'icon' not in spec and (old_spec.get('schemaVersion', 1) != 2 or old_spec.get('icon')):
                raise ValueError('Schema version 2 requires a plugin icon')
            changes = update_changes(candidate, target, record['commit'], new_commit, old_spec, spec)
            changes['official'] = official(record['url'])
            if not approve(changes):
                return False
            replacement = self.folder / ('.' + plugin_id + '-new')
            backup = self.folder / ('.' + plugin_id + '-previous')
            if replacement.exists() or backup.exists():
                raise ValueError('An interrupted plugin update needs recovery')
            try:
                shutil.copytree(candidate, replacement, symlinks=True)
                if manifest(replacement) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in old_spec and self.unit(plugin_id).exists():
                    self.systemctl('stop', self.unit(plugin_id).name)
                target.rename(backup)
                replacement.rename(target)
                if 'service' in spec or 'service' in old_spec:
                    self.service(plugin_id, spec if record.get('enabled', True) else None)
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
                            self.service(plugin_id, old_spec if record.get('enabled', True) else None)
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
            target = self.root(plugin_id)
            if target.is_symlink():
                raise ValueError('Plugin folder must not be a symlink')
            if self.unit(plugin_id).exists():
                self.service(plugin_id)
            if target.exists() and not record.get('path'):
                shutil.rmtree(target)
            del records[plugin_id]
            self.save(records)
            self.clean_snapshots()
            return True

    def set_enabled(self, plugin_id, enabled):
        identifier(plugin_id)
        with self.lock():
            records = self.records()
            record = records[plugin_id]
            if enabled:
                self.check(record['url'], record['commit'], plugin_id)
                root = self.root(plugin_id)
                if root.is_symlink() or commit(root) != record['commit']:
                    raise ValueError('Plugin differs from its approved commit')
                spec = manifest(root)
                self.service(plugin_id, spec)
            elif self.unit(plugin_id).exists():
                self.service(plugin_id)
            records[plugin_id] = {**record, 'enabled': enabled}
            self.save(records)

    def check_updates(self):
        """Fetch metadata into installed repositories without checking out or running code."""
        counts = {}
        checked = {}
        with self.lock():
            for plugin_id, record in self.records().items():
                try:
                    root = self.root(plugin_id)
                    git(root, 'fetch', '--no-recurse-submodules', '--', record['url'],
                        'HEAD', allow_file=self.allow_file)
                    # A plugin from an indexed repository counts only commits that touch its own folder.
                    scope = ['--', ':(top)' + record['path']] if record.get('path') else []
                    count = int(git(root, 'rev-list', '--count', record['commit'] + '..FETCH_HEAD', *scope))
                    checked[plugin_id] = dict(commit=record['commit'], count=count)
                    counts[plugin_id] = count
                except (OSError, ValueError, subprocess.SubprocessError):
                    continue
            self.write(self.state.with_name('plugin-updates.json'), checked)
        return counts

    def update_counts(self):
        try:
            return json.loads(self.state.with_name('plugin-updates.json').read_text())
        except (OSError, ValueError):
            return {}

    def installed(self):
        """Plugins > Installed Plugins: every plugin, with its manifest author and whether it is blocked."""
        blocked = self.blocked()
        updates = self.update_counts()
        rows = []
        for plugin_id, record in self.records().items():
            spec = self.spec(plugin_id)
            checked = updates.get(plugin_id, {})
            count = checked.get('count', 0) if checked.get('commit') == record['commit'] else 0
            rows.append(dict(id=plugin_id, updateCount=count, official=official(record['url']),
                             name=printable(spec['name']) if spec else plugin_id,
                             author=printable(spec['author']) if spec else '?', blocked=blocked.get(plugin_id, ('',))[0],
                             repository=printable(record['url']), repositoryPath=record.get('path', ''),
                             enabled=record.get('enabled', True), version=spec['version'] if spec else '',
                             description=spec['description'] if spec else '',
                             visualsDisabled=bool(self.ui_state().get(plugin_id, {}).get('disabled')),
                             icon=(self.root(plugin_id) / spec['icon']).as_uri() if spec and spec.get('icon') else '',
                             preview=(self.root(plugin_id) / spec['preview']).as_uri() if spec and spec.get('preview') else ''))
        return sorted(rows, key=lambda row: row['name'].casefold())
