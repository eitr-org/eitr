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
import secrets
import time
from urllib.parse import urlsplit

import eitr_plugin_packages
import eitr_policy
from eitr_i18n import mark, tr
from eitr_paths import cache, config, data, state
from eitr_plugin_manifest import (
    identifier,
    index_entries,
    manifest,
    object_keys,
    plugin_files,
    printable,
    qml_files,
    repository_plugins,
    string,
    unique_object,
    media_entries,
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


def git(root, *arguments, allow_file=False, binary=False, lazy_fetch=True, timeout=120):
    environment = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    environment.update(GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
                       GIT_ALLOW_PROTOCOL='https:ssh:file' if allow_file else 'https:ssh',
                       # A passphrase prompt would break the install screen; keys come from the agent.
                       GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    if not lazy_fetch:
        environment['GIT_NO_LAZY_FETCH'] = '1'
    output = subprocess.check_output(['git', '--no-replace-objects', '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false',
                                    '-c', 'submodule.recurse=false', '-c', 'credential.helper=',
                                    *arguments], cwd=root, env=environment, text=not binary, stdin=subprocess.DEVNULL,
                                   stderr=subprocess.PIPE, timeout=timeout)
    return output if binary else output.strip()


def clone(url, destination, *, allow_file=False):
    repository_url(url, allow_file=allow_file)
    git(None, 'clone', '--template=', '--no-recurse-submodules', '--', url, str(destination), allow_file=allow_file)


def commit(root):
    from eitr_plugin_bundled import is_bundled, bundled_revision
    if is_bundled(root):
        return bundled_revision(root)
    return git(root, 'rev-parse', 'HEAD')


def verify_tree(root, revision):
    """Compare every worktree byte and executable bit with the reviewed Git tree."""
    if (root / '.git').is_symlink() or not (root / '.git').is_dir():
        raise ValueError('Plugin Git metadata must stay inside its stage')
    list(plugin_files(root))
    git(root, 'fsck', '--strict', '--full', '--no-reflogs')
    if commit(root) != revision:
        raise ValueError('Plugin differs from its reviewed commit')
    expected = {}
    for record in git(root, 'ls-tree', '-rz', revision).split('\0'):
        if not record:
            continue
        header, filename = record.split('\t', 1)
        mode, kind, object_id = header.split()
        if kind != 'blob' or mode not in ('100644', '100755'):
            raise ValueError('Plugins may not contain links or submodules')
        expected[filename] = (mode, object_id)
    actual = {str(path.relative_to(root)): path for path in plugin_files(root)}
    if actual.keys() != expected.keys():
        raise ValueError('Plugin files differ from the reviewed commit')
    for filename, path in actual.items():
        mode, object_id = expected[filename]
        if (bool(path.stat().st_mode & 0o111) != (mode == '100755') or
                git(root, 'hash-object', '--no-filters', '--', str(path)) != object_id):
            raise ValueError('Plugin files differ from the reviewed commit')


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
    added_packages = set(spec.get('packages', [])) - set((previous or {}).get('packages', []))
    if added_packages:
        flags.append(tr('System packages added: {packages}', packages=', '.join(sorted(added_packages))))
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
        self._reviews = {}
        self._review_revision = None

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
            object_keys(record, ('url', 'id', 'commit', 'installed'), ('enabled', 'path', 'packages', 'bundled'))
            if 'bundled' in record and (record['bundled'] is not True or plugin_id != 'weather' or record['url'] != 'https://github.com/eitr-org/eitr' or 'path' in record):
                raise ValueError('Invalid bundled plugin state')
            eitr_plugin_packages.names(record.get('packages', []), limit=4096)
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
        if record.get('bundled'):
            from eitr_plugin_bundled import bundled_root
            return bundled_root(plugin_id)
        if record.get('path'):
            return self.snapshot(record['url'], record['commit']) / record['path']
        return self.folder / plugin_id

    def keep_snapshot(self, candidate, url, revision):
        target = self.snapshot(url, revision)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate, target, symlinks=True)
        if target.is_symlink():
            raise ValueError('Repository snapshot differs from its approved commit')
        verify_tree(target, revision)
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

    def catalog(self, url, *, revision=None, folder=None, plugin_id=None):
        """Read index/card metadata only; installation still validates all files."""
        repository_url(url, allow_file=self.allow_file)
        pinned = revision
        with self.lock():
            candidate = cache('eitr/plugin-repositories') / hashlib.sha256(normalized_url(url).encode()).hexdigest()
            candidate.parent.mkdir(parents=True, exist_ok=True)
            if not candidate.exists():
                with tempfile.TemporaryDirectory(dir=candidate.parent) as temporary:
                    staging = Path(temporary) / 'repository'
                    git(None, 'clone', '--template=', '--filter=blob:none', '--sparse', '--no-checkout',
                        '--no-recurse-submodules', '--', url, str(staging), allow_file=self.allow_file)
                    staging.rename(candidate)
                revision = pinned or commit(candidate)
            elif pinned is None:
                git(candidate, 'fetch', '--filter=blob:none', '--no-recurse-submodules', '--', url, 'HEAD', allow_file=self.allow_file)
                revision = git(candidate, 'rev-parse', 'FETCH_HEAD', allow_file=self.allow_file)

            if pinned is not None:
                revision = pinned
                if not COMMIT.fullmatch(revision):
                    raise ValueError('Invalid pinned commit')
                git(candidate, 'fetch', '--no-recurse-submodules', '--', url, revision, allow_file=self.allow_file)
            else:
                revision = commit(candidate) if not revision else revision

            def blob(path):
                entry = git(candidate, 'ls-tree', revision, '--', path, allow_file=self.allow_file)
                if not entry.startswith('100644 blob '):
                    raise ValueError('Catalog metadata must be a regular file')
                object_id = git(candidate, 'rev-parse', revision + ':' + path, allow_file=self.allow_file)
                if int(git(candidate, 'cat-file', '-s', object_id, allow_file=self.allow_file)) > 65536:
                    raise ValueError('Catalog metadata exceeds size limit')
                return json.loads(git(candidate, 'cat-file', 'blob', object_id, allow_file=self.allow_file), object_pairs_hook=unique_object)

            entries = [dict(id=plugin_id, path=folder)] if folder is not None else index_entries(blob('eitr-plugins.json'))
            rows = []
            for entry in entries:
                spec = blob((entry['path'] + '/' if entry['path'] else '') + 'eitr-plugin.json')
                if not isinstance(spec, dict) or spec.get('id') != entry['id']:
                    raise ValueError('Plugin index id does not match its manifest')
                name = string(spec.get('name'))
                description = string(spec.get('description'), 72)
                artwork = {}
                for field in ('icon', 'preview'):
                    if field in spec:
                        relative = PurePosixPath(string(spec[field]))
                        if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] == '.git' or '\\' in spec[field]:
                            raise ValueError('Plugin image must stay inside its folder')
                        artwork[field] = str(PurePosixPath(entry['path']) / relative)
                media = [dict(asset, path=str(PurePosixPath(entry['path']) / asset['path']))
                         for asset in media_entries(spec.get('media', []))]
                rows.append(dict(id=entry['id'], name=name, description=description, size=0,
                                 author=string(spec.get('author')), version=string(spec.get('version')),
                                 components={key: spec[key] for key in ('rows', 'ui', 'hooks', 'service', 'capabilities') if key in spec},
                                 repository=url, folder=entry['path'], media=media, commit=revision, **artwork))
            return rows

    def prepare(self, url, temporary):
        candidate = temporary / 'candidate'
        if self._review_revision:
            git(None, 'init', '--template=', str(candidate), allow_file=self.allow_file)
            git(candidate, 'remote', 'add', 'origin', url, allow_file=self.allow_file)
            git(candidate, 'fetch', '--no-recurse-submodules', '--', url, self._review_revision, allow_file=self.allow_file)
            git(candidate, 'checkout', '--detach', self._review_revision, allow_file=self.allow_file)
        else:
            clone(url, candidate, allow_file=self.allow_file)
        verify_tree(candidate, commit(candidate))
        entries = repository_plugins(candidate)
        return candidate, entries if entries[0]["path"] else entries[0]["spec"]

    def _add(self, url, consent, approve, pick=None):
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
            caused = eitr_plugin_packages.install(spec)
            verify_tree(candidate, approved)
            self.folder.mkdir(parents=True, exist_ok=True)
            try:
                shutil.copytree(candidate, target, symlinks=True)
                verify_tree(target, approved)
                if manifest(target) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in spec:
                    self.service(plugin_id, spec)
                records[plugin_id] = dict(url=url, id=plugin_id, commit=approved,
                                         installed=datetime.datetime.now(datetime.timezone.utc).isoformat(), packages=caused)
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
                caused = eitr_plugin_packages.install(spec)
                verify_tree(candidate, revision)
                snapshot = self.keep_snapshot(candidate, url, revision)
                root = snapshot / entry['path']
                if manifest(root) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                record = dict(url=url, id=plugin_id, commit=revision, path=entry['path'],
                              installed=datetime.datetime.now(datetime.timezone.utc).isoformat(), packages=caused)
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
            caused = eitr_plugin_packages.install(spec, record.get('packages', []))
            verify_tree(candidate, changes['new'])
            snapshot = self.keep_snapshot(candidate, record['url'], revision)
            root = snapshot / entry['path']
            try:
                if manifest(root) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in spec or 'service' in old_spec:
                    self.service(plugin_id, spec if record.get('enabled', True) else None, root=root)
                self.save({**records, plugin_id: {**record, 'commit': revision, 'packages': caused}})
            except BaseException:
                if 'service' in spec or 'service' in old_spec:
                    with contextlib.suppress(OSError, subprocess.SubprocessError):
                        self.service(plugin_id, old_spec if record.get('enabled', True) else None, root=target)
                raise
            finally:
                self.clean_snapshots()
            return True

    def _update(self, plugin_id, approve):
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
            caused = eitr_plugin_packages.install(spec, record.get('packages', []))
            verify_tree(candidate, changes['new'])
            replacement = self.folder / ('.' + plugin_id + '-new')
            backup = self.folder / ('.' + plugin_id + '-previous')
            if replacement.exists() or backup.exists():
                raise ValueError('An interrupted plugin update needs recovery')
            try:
                shutil.copytree(candidate, replacement, symlinks=True)
                verify_tree(replacement, new_commit)
                if manifest(replacement) != spec:
                    raise ValueError('Plugin manifest changed after approval')
                if 'service' in old_spec and self.unit(plugin_id).exists():
                    self.systemctl('stop', self.unit(plugin_id).name)
                target.rename(backup)
                replacement.rename(target)
                if 'service' in spec or 'service' in old_spec:
                    self.service(plugin_id, spec if record.get('enabled', True) else None)
                self.save({**records, plugin_id: {**record, 'commit': new_commit, 'packages': caused}})
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

    def discard_reviews(self):
        for review in self._reviews.values():
            review['stage'].cleanup()
        self._reviews.clear()

    def _capture_review(self, root, spec, url, *, updating=False, changes=None, folder=None):
        repository = Path(git(root, 'rev-parse', '--show-toplevel'))
        selected = root.relative_to(repository).as_posix()
        selected = '' if selected == '.' else selected
        if folder is not None and selected != folder:
            raise ValueError('Plugin folder differs from catalog')
        approved = commit(repository)
        verify_tree(repository, approved)
        parent = (Path(os.environ['EITR_CATALOG_REVIEW_CACHE']) / 'plugins'
                  if os.environ.get('EITR_CATALOG_REVIEW_CACHE') else cache('eitr/plugin-reviews'))
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        stage = tempfile.TemporaryDirectory(prefix='review-', dir=parent)
        try:
            shutil.copytree(repository, Path(stage.name) / 'candidate')
            import eitr_plugin_review
            facts = dict(packages=eitr_plugin_packages.review(spec), spec=spec, url=url, folder=selected, commit=approved,
                         official=official(url), author=git(root, 'show', '-s', '--format=%an <%ae> · %aI', approved),
                         files=sorted(str(path.relative_to(root)) for path in plugin_files(root)),
                         flags=add_flags(root, spec), assistant=eitr_plugin_review.available(),
                         qml=[dict(path=str(path.relative_to(root)), size=path.stat().st_size) for path in qml_files(root)],
                         changes={key: value for key, value in (changes or {}).items() if key != 'root'})
            token = secrets.token_urlsafe(32)
            self._reviews[token] = dict(facts=facts, spec=spec, url=url, folder=selected, commit=approved,
                                       id=spec['id'], updating=updating, old=self.records().get(spec['id']),
                                       stage=stage, expires=time.monotonic() + 900)
            return dict(facts, token=token)
        except BaseException:
            stage.cleanup()
            raise

    def prepare_review(self, url=None, *, plugin_id=None, folder=None, revision=None, updating=False):
        """Run the normal validation transaction, stopping at its approval boundary."""
        if updating and self.records().get(plugin_id, {}).get("bundled"):
            raise ValueError("No plugin changes to review")
        self.expire_reviews()
        if revision is not None and not COMMIT.fullmatch(revision):
            raise ValueError('Invalid pinned commit')
        captured = []
        offered = []

        def capture(root, spec, source, changes=None):
            captured.append(self._capture_review(root, spec, source, updating=updating, changes=changes, folder=folder))
            return False

        def pick(entries):
            choices = [entry for entry in entries if not entry['installed'] and
                       (plugin_id is None or entry['spec']['id'] == plugin_id) and
                       (folder is None or entry['path'] == folder)]
            if len(choices) > 1 and plugin_id is None:
                offered.extend(dict(id=entry['spec']['id'], name=entry['spec']['name'], description=entry['spec']['description']) for entry in choices)
                return []
            if len(choices) != 1:
                raise ValueError('Choose one plugin from this repository')
            return [choices[0]['spec']['id']]

        try:
            self._review_revision = revision
            if updating:
                self._update(plugin_id, lambda changes: capture(changes['root'], changes['spec'], self.records()[plugin_id]['url'], changes))
            else:
                self._add(url, lambda source: True, capture, pick)
            if offered:
                return dict(choices=offered, url=url, official=official(url))
            if not captured:
                raise ValueError('No plugin changes to review')
            return captured[0]
        finally:
            self._review_revision = None

    def add(self, url, consent, approve, pick=None):
        """Terminal adapter: preserve consent/selection and use the native tokens."""
        tokens = []

        def capture(root, spec, source):
            facts = self._capture_review(root, spec, source)
            tokens.append(facts['token'])
            return False

        try:
            self._add(url, consent, capture, pick)
            installed = False
            for token in tokens:
                review = self._reviews[token]
                root = Path(review['stage'].name) / 'candidate' / review['folder']
                if approve(root, review['spec'], review['url']):
                    installed = self.confirm_review(token) or installed
            return installed
        finally:
            for token in tokens:
                review = self._reviews.pop(token, None)
                if review:
                    review['stage'].cleanup()

    def update(self, plugin_id, approve):
        try:
            facts = self.prepare_review(plugin_id=plugin_id, updating=True)
        except ValueError as error:
            if str(error) == 'No plugin changes to review':
                return False
            raise
        token = facts['token']
        review = self._reviews[token]
        root = Path(review['stage'].name) / 'candidate' / review['folder']
        try:
            if not approve(dict(facts['changes'], root=root)):
                return False
            return self.confirm_review(token)
        finally:
            review = self._reviews.pop(token, None)
            if review:
                review['stage'].cleanup()

    def expire_reviews(self):
        for token, review in list(self._reviews.items()):
            if review['expires'] <= time.monotonic():
                self._reviews.pop(token)['stage'].cleanup()

    def review_advice(self, token):
        self.expire_reviews()
        review = self._reviews.get(token)
        if review is None:
            raise ValueError('Review expired; prepare it again')
        candidate = Path(review['stage'].name) / 'candidate'
        verify_tree(candidate, review['commit'])
        import eitr_plugin_review
        return eitr_plugin_review.check(candidate, review['folder'] or '.')

    def review_source(self, token, path, offset=0):
        self.expire_reviews()
        review = self._reviews.get(token)
        if review is None:
            raise ValueError('Review expired; prepare it again')
        if type(offset) is not int or offset < 0:
            raise ValueError('Invalid review offset')
        candidate = Path(review['stage'].name) / 'candidate'
        verify_tree(candidate, review['commit'])
        root = candidate / review['folder']
        files = {str(source.relative_to(root)): source for source in qml_files(root)}
        if path not in files:
            raise ValueError('Source is not listed by this review')
        text = files[path].read_text()
        return dict(text=text[offset:offset + 16384], offset=offset, total=len(text))

    def confirm_review(self, token):
        self.expire_reviews()
        review = self._reviews.pop(token, None)
        if review is None:
            raise ValueError('Review expired; prepare it again')
        candidate = Path(review['stage'].name) / 'candidate'
        original_prepare = self.prepare

        def prepared(url, temporary):
            if self.records().get(review['id']) != review['old']:
                raise ValueError('Installed plugin changed; prepare it again')
            if url != review['url']:
                raise ValueError('Review source changed')
            verify_tree(candidate, review['commit'])
            entries = repository_plugins(candidate)
            return candidate, entries if entries[0]['path'] else entries[0]['spec']

        def approve(root, spec, url):
            if (spec != review['spec'] or spec['id'] != review['id'] or
                    root != candidate / review['folder'] or url != review['url']):
                raise ValueError('Review candidate changed')
            verify_tree(candidate, review['commit'])
            return True

        try:
            if self.records().get(review['id']) != review['old']:
                raise ValueError('Installed plugin changed; prepare it again')
            self.prepare = prepared
            if review['updating']:
                return self._update(review['id'], lambda changes: approve(changes['root'], changes['spec'], review['url']))
            installed = self._add(review['url'], lambda source: True, approve, lambda entries: [review['id']])
        finally:
            self.prepare = original_prepare
            review['stage'].cleanup()
        if installed:
            self.show_bar_items(review['id'], review['spec'])
        return installed

    def show_bar_items(self, plugin_id, spec):
        """A new plugin's bar items start on the bar; hiding one is kept across updates."""
        for item in spec.get('ui', {}).get('barItems', []):
            try:
                self.place(plugin_id, item['id'])
            except (OSError, ValueError):
                continue

    def remove(self, plugin_id, approve, remove_packages=None):
        identifier(plugin_id)
        with self.lock():
            records = self.records()
            record = dict(records[plugin_id])
            record['packages'] = eitr_plugin_packages.owned(plugin_id, record.get('packages', []))
            retained = {name for other_id in records if other_id != plugin_id
                        for name in (self.spec(other_id) or {}).get('packages', [])}
            candidates = eitr_plugin_packages.removable(record.get('packages', []), retained)
            if not approve(record):
                return False
            if candidates and remove_packages:
                selected = remove_packages(candidates)
                selected = candidates if selected is True else selected if isinstance(selected, list) else []
                if set(selected) - set(candidates):
                    raise ValueError('Invalid package cleanup selection')
                if selected:
                    eitr_plugin_packages.root('remove', selected)
            target = self.root(plugin_id)
            if target.is_symlink():
                raise ValueError('Plugin folder must not be a symlink')
            if self.unit(plugin_id).exists():
                self.service(plugin_id)
            if target.exists() and not record.get('path') and not record.get('bundled'):
                shutil.rmtree(target)
            for other_id, other in records.items():
                if other_id != plugin_id:
                    shared = set(record.get('packages', [])) & set((self.spec(other_id) or {}).get('packages', []))
                    if shared:
                        other['packages'] = list(dict.fromkeys([*other.get('packages', []), *sorted(shared)]))
            del records[plugin_id]
            self.save(records)
            self.clean_snapshots()
            eitr_plugin_packages.forget(plugin_id)
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
                if 'service' in spec or self.unit(plugin_id).exists():
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
                    if record.get('bundled'):
                        continue
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
            rows.append(dict(id=plugin_id, updateCount=count, official=bool(record.get('bundled')) or official(record['url']), builtin=bool(record.get('bundled')), removable=True,
                             removablePackages=eitr_plugin_packages.removable(eitr_plugin_packages.owned(plugin_id, record.get('packages', [])),
                                 {name for other_id in self.records() if other_id != plugin_id
                                  for name in (self.spec(other_id) or {}).get('packages', [])}),
                             name=printable(spec['name']) if spec else plugin_id,
                             author=printable(spec['author']) if spec else '?', blocked=blocked.get(plugin_id, ('',))[0],
                             repository=printable(record['url']), repositoryPath=record.get('path', ''),
                             enabled=record.get('enabled', True), version=spec['version'] if spec else '',
                             description=spec['description'] if spec else '', commit=record['commit'],
                             components={key: spec[key] for key in ('rows', 'ui', 'hooks', 'service', 'capabilities') if spec and key in spec},
                             media=[dict(asset, imageUrl=(self.root(plugin_id) / asset['path']).as_uri()) for asset in spec.get('media', [])] if spec else [],
                             visualsDisabled=bool(self.ui_state().get(plugin_id, {}).get('disabled')),
                             icon=(self.root(plugin_id) / spec['icon']).as_uri() if spec and spec.get('icon') else '',
                             preview=(self.root(plugin_id) / spec['preview']).as_uri() if spec and spec.get('preview') else ''))
        return sorted(rows, key=lambda row: row['name'].casefold())
