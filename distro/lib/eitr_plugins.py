"""Per-user, explicitly approved Git plugins. Plugin commands are always argv."""
import contextlib
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import signal
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

import eitr_policy
from eitr_i18n import tr
from eitr_paths import config, data, state

SLUG = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*\Z')
COMMIT = re.compile(r'[0-9a-f]{40}(?:[0-9a-f]{24})?\Z')
# Shipped in the signed eitr-desktop package, beside lib/ (distro/ in a checkout).
BLOCKLIST = Path(__file__).resolve().parents[1] / 'plugin-blocklist.json'
HOOK_EVENTS = ('theme-changed', 'wallpaper-changed', 'after-update', 'login')
HOOK_TIMEOUT = 30

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


def image_asset(root, relative, *, preview=False):
    """Validate local artwork before passing its URL to Qt's image loader."""
    path = PurePosixPath(string(relative))
    if path.is_absolute() or '..' in path.parts or not path.parts or path.parts[0] == '.git':
        raise ValueError('Plugin image must stay inside its folder')
    target = root / path
    if any(parent.is_symlink() for parent in [target, *target.parents] if parent.is_relative_to(root)):
        raise ValueError('Plugin images may not be symlinks')
    if not target.resolve(strict=True).is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError('Plugin image must be a file inside its folder')
    if target.stat().st_size > (2 * 1024 * 1024 if preview else 512 * 1024):
        raise ValueError('Plugin image exceeds its size limit')
    if target.suffix.lower() == '.svg' and not preview:
        raw = target.read_bytes()
        if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
            raise ValueError('Plugin SVG must not declare entities')
        try:
            svg = ET.fromstring(raw)
            view = [float(number) for number in svg.get('viewBox', '').replace(',', ' ').split()]
            width = float(svg.get('width', str(view[2] if len(view) == 4 else 0)).removesuffix('px'))
            height = float(svg.get('height', str(view[3] if len(view) == 4 else 0)).removesuffix('px'))
        except (ET.ParseError, ValueError) as error:
            raise ValueError('Invalid plugin SVG') from error
        if svg.tag != '{http://www.w3.org/2000/svg}svg' or not 0 < width == height <= 1024:
            raise ValueError('Plugin icon must be square')
        for element in svg.iter():
            if element.tag.rsplit('}', 1)[-1] in ('script', 'style', 'foreignObject', 'image', 'use'):
                raise ValueError('Plugin SVG must be self-contained shapes')
            if any('href' in key or key.lower().startswith('on') or 'url(' in content.lower() for key, content in element.attrib.items()):
                raise ValueError('Plugin SVG must not reference external content')
    else:
        from PIL import Image, UnidentifiedImageError
        try:
            with Image.open(target) as image:
                expected = ('PNG', 'JPEG') if preview else ('PNG',)
                if image.format not in expected or target.suffix.lower() not in (('.png', '.jpg', '.jpeg') if preview else ('.png',)):
                    raise ValueError('Invalid plugin image format')
                width, height = image.size
                valid = (0 < width <= 3840 and 0 < height <= 3840) if preview else (64 <= width == height <= 1024)
                if not valid:
                    raise ValueError('Invalid plugin image dimensions')
                image.verify()
        except (UnidentifiedImageError, Image.DecompressionBombError, SyntaxError) as error:
            raise ValueError('Invalid plugin image') from error
    return target


def manifest(root):
    path = root / 'eitr-plugin.json'
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Invalid plugin manifest file')
    value = json.loads(path.read_text(), object_pairs_hook=unique_object)
    if not isinstance(value, dict):
        raise ValueError('Invalid plugin manifest fields')
    version = value.get('schemaVersion', 1)
    if type(version) is not int or version < 1:
        raise ValueError(tr('Invalid plugin schemaVersion; expected 1 or 2'))
    if version > 2:
        raise ValueError(tr('This plugin needs a newer Eitr'))
    object_keys(value, ('id', 'name', 'description', 'author', 'version', 'rows'), ('service', 'schemaVersion', 'hooks', 'icon', 'preview', 'homepage') + (('ui', 'capabilities') if version == 2 else ()))
    for field in ('icon', 'preview'):
        if field in value:
            image_asset(root, value[field], preview=field == 'preview')
    if 'homepage' in value:
        homepage_text = string(value['homepage'], 2048)
        homepage = urlsplit(homepage_text)
        homepage.port
        if any(character.isspace() for character in homepage_text) or '\\' in homepage_text:
            raise ValueError('Invalid plugin homepage')
        if homepage.scheme != 'https' or not homepage.hostname or homepage.username or homepage.password:
            raise ValueError('Plugin homepage must be an HTTPS URL without credentials')
    capabilities = value.get('capabilities', [])
    if not isinstance(capabilities, list) or any(not isinstance(capability, str) or capability != 'audio-spectrum' for capability in capabilities) or len(capabilities) != len(set(capabilities)):
        raise ValueError('Invalid plugin capabilities')
    identifier(value['id'])
    for field in ('name', 'author', 'version'):
        string(value[field])
    string(value['description'], 72)
    # A visual-only plugin (schema 2 with ui components) needs no Walker rows.
    visual = version == 2 and isinstance(value.get('ui'), dict) and any(value['ui'].values())
    if not isinstance(value['rows'], list) or not (0 if visual else 1) <= len(value['rows']) <= 20:
        raise ValueError('A plugin must declare 1..20 rows' if not visual else 'A plugin may declare at most 20 rows')
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
    hooks = value.get('hooks', {})
    if not isinstance(hooks, dict) or hooks.keys() - set(HOOK_EVENTS):
        raise ValueError(tr('Invalid plugin hooks; unknown event'))
    for hook in hooks.values():
        object_keys(hook, ('run',), ('arguments',))
        command(root, hook)
    if 'ui' in value:
        validate_ui(root, value['ui'])
    return value


def repository_plugins(root):
    """Validate the entire index before offering any entry for review."""
    index = root / 'eitr-plugins.json'
    if not index.exists() and not index.is_symlink():
        return [dict(path='', spec=manifest(root))]
    list(plugin_files(root))
    if index.is_symlink() or not index.is_file() or index.stat().st_size > 65536:
        raise ValueError('Invalid plugin index file')
    value = json.loads(index.read_text(), object_pairs_hook=unique_object)
    object_keys(value, ('schemaVersion', 'plugins'))
    if type(value['schemaVersion']) is not int or value['schemaVersion'] != 1:
        raise ValueError('Invalid plugin index schemaVersion')
    entries = value['plugins']
    if not isinstance(entries, list) or not 1 <= len(entries) <= 100:
        raise ValueError('A plugin index must declare 1..100 plugins')
    result, ids, paths = [], set(), set()
    for entry in entries:
        object_keys(entry, ('id', 'path'))
        plugin_id = identifier(entry['id'])
        relative = string(entry['path'], 512)
        parts = PurePosixPath(relative)
        if (parts.is_absolute() or '..' in parts.parts or '.' in relative.split('/')
                or '\\' in relative or str(parts) != relative or not parts.parts):
            raise ValueError('Plugin index paths must be normalized repository-relative folders')
        folder = root / relative
        if not folder.is_dir() or not folder.resolve().is_relative_to(root.resolve()):
            raise ValueError('Plugin index path escapes the repository or is missing')
        if plugin_id in ids or relative in paths:
            raise ValueError('Duplicate plugin index id or path')
        if any(folder.is_relative_to(root / previous) or (root / previous).is_relative_to(folder) for previous in paths):
            raise ValueError('Plugin index folders may not overlap')
        spec = manifest(folder)
        if spec['id'] != plugin_id:
            raise ValueError('Plugin index id does not match its manifest')
        if spec.get('schemaVersion') == 2 and 'icon' not in spec:
            raise ValueError('Schema version 2 requires a plugin icon')
        ids.add(plugin_id)
        paths.add(relative)
        result.append(dict(path=relative, spec=spec))
    return result


UI_FAILURE_LIMIT = 3


def qml_files(root):
    files = sorted(path for path in plugin_files(root) if path.suffix.casefold() == '.qml')
    if len(files) > 32:
        raise ValueError('A plugin may contain at most 32 QML files')
    for path in files:
        if path.stat().st_size > 65536:
            raise ValueError('Plugin QML files must be at most 64 KiB')
        source = path.read_text(encoding='utf-8')
        if '\0' in source:
            raise ValueError('Plugin QML must be UTF-8 text without NUL')
    return files


def validate_ui(root, ui):
    object_keys(ui, (), ('tiles', 'panels', 'widgets', 'barItems'))
    if not isinstance(ui.get('panels', []), list):
        raise ValueError('Plugin panels must be a list')
    files = qml_files(root)
    ids = set()
    for kind in ('tiles', 'panels', 'widgets', 'barItems'):
        entries = ui.get(kind, [])
        if not isinstance(entries, list) or len(entries) > 8:
            raise ValueError('A plugin may declare at most 8 entries per visual kind')
        for entry in entries:
            optional = ('icon', 'refreshInterval', 'dataCommand', 'dataStream')
            if kind in ('tiles', 'barItems'):
                optional += ('panel',)
            if kind == 'tiles':
                optional += ('look',)
            elif kind == 'panels':
                optional += ('surface', 'header')
            elif kind == 'widgets':
                optional += ('minWidth', 'minHeight', 'defaultWidth', 'defaultHeight', 'surface')
            object_keys(entry, ('id', 'title', 'qml'), optional)
            if 'panel' in entry:
                panel_id = identifier(entry['panel'])
                if panel_id not in [panel.get('id') for panel in ui.get('panels', []) if isinstance(panel, dict)]:
                    raise ValueError('Visual panel must name a declared panel')
            if kind == 'tiles' and entry.get('look', 'eitr') not in ('eitr', 'custom'):
                raise ValueError('Invalid tile look')
            if kind == 'panels' and type(entry.get('header', True)) is not bool:
                raise ValueError('Panel header must be a boolean')
            if kind in ('widgets', 'panels') and entry.get('surface', 'none') not in ('panel', 'none'):
                raise ValueError('Invalid visual surface')
            if kind == 'widgets':
                for dimension in ('Width', 'Height'):
                    minimum = entry.get('min' + dimension, 96)
                    default = entry.get('default' + dimension, 192)
                    if type(minimum) is not int or type(default) is not int or not 24 <= minimum <= default <= 4096:
                        raise ValueError('Widget sizes must be integers: 24 <= min <= default <= 4096')
            key = identifier(entry['id'])
            if key in ids:
                raise ValueError('Duplicate plugin UI id')
            ids.add(key)
            string(entry['title'], 72)
            if 'icon' in entry:
                string(entry['icon'], 8)
            relative = PurePosixPath(string(entry['qml'], 256))
            if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0] == '.git':
                raise ValueError('Plugin QML must stay inside its folder')
            target = root / relative
            if target.is_symlink() or target.resolve() not in [path.resolve() for path in files]:
                raise ValueError('Plugin QML must name a QML file inside its folder')
            interval = entry.get('refreshInterval', 0)
            if type(interval) is not int or (interval != 0 and not 1000 <= interval <= 3600000):
                raise ValueError('Plugin refreshInterval must be 0 or 1000..3600000 milliseconds')
            if interval and 'dataCommand' not in entry:
                raise ValueError('Plugin refreshInterval needs a dataCommand')
            for field in ('dataCommand', 'dataStream'):
                if field in entry:
                    object_keys(entry[field], ('run',), ('arguments',))
                    command(root, entry[field])


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

    def add_indexed(self, candidate, entries, url, records, approve, pick):
        if pick is None:
            raise ValueError('Choose plugins from this repository before installing')
        choices = pick(entries)
        if not isinstance(choices, list) or any(not isinstance(choice, str) for choice in choices) or len(choices) != len(set(choices)):
            raise ValueError('Invalid plugin selection')
        available = {entry['spec']['id']: entry for entry in entries}
        if set(choices) - available.keys():
            raise ValueError('Unknown plugin selection')
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
        """Install > Plugins: every plugin, with its manifest author and whether it is blocked."""
        blocked = self.blocked()
        updates = self.update_counts()
        rows = []
        for plugin_id, record in self.records().items():
            spec = self.spec(plugin_id)
            checked = updates.get(plugin_id, {})
            count = checked.get('count', 0) if checked.get('commit') == record['commit'] else 0
            rows.append(dict(id=plugin_id, updateCount=count,
                             name=printable(spec['name']) if spec else plugin_id,
                             author=printable(spec['author']) if spec else '?', blocked=blocked.get(plugin_id, ('',))[0],
                             repository=printable(record['url']), repositoryPath=record.get('path', ''),
                             enabled=record.get('enabled', True), version=spec['version'] if spec else '',
                             description=spec['description'] if spec else '',
                             visualsDisabled=bool(self.ui_state().get(plugin_id, {}).get('disabled')),
                             icon=(self.root(plugin_id) / spec['icon']).as_uri() if spec and spec.get('icon') else '',
                             preview=(self.root(plugin_id) / spec['preview']).as_uri() if spec and spec.get('preview') else ''))
        return sorted(rows, key=lambda row: row['name'].casefold())

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
                                     author=short_author(spec), icon=row.get('icon', '󰏖')))
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


def dispatch_hooks(event, **context):
    """Fire and forget: triggering actions never wait for plugin code."""
    from eitr_paths import code
    try:
        subprocess.Popen(['python3', str(code('walker/scripts/actions/install/plugins.py')), 'hooks', event],
                         env=dict(os.environ, **context), start_new_session=True,
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
