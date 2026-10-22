"""Organization profile format, validation and review; validation never writes."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from urllib.parse import urlsplit

from eitr_i18n import tr

PACKAGE = re.compile(r'[a-zA-Z0-9][a-zA-Z0-9@._+-]*\Z')
APP_ID = re.compile(r'[A-Za-z][A-Za-z0-9_-]*(?:\.[A-Za-z0-9_-]+){2,}\Z')
SHA256 = re.compile(r'[a-f0-9]{64}\Z')


class ProfileError(ValueError):
    pass


def data_root():
    source = Path(__file__).resolve().parents[1]
    return source if (source / 'removable-apps.json').is_file() else Path('/usr/share/eitr')


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProfileError(tr('Duplicate JSON key: {key}', key=key))
        result[key] = value
    return result


def read_json(path):
    try:
        return json.loads(Path(path).read_text(), object_pairs_hook=pairs_unique,
                          parse_constant=lambda value: fail(tr('Invalid JSON constant: {value}', value=value)))
    except (OSError, ValueError) as error:
        raise ProfileError(f'{path}: {error}') from None


def fail(message):
    raise ProfileError(message)


def object_keys(value, allowed, location):
    if not isinstance(value, dict):
        fail(tr('{location}: expected an object', location=location))
    unknown = value.keys() - set(allowed)
    if unknown:
        fail(tr('{location}: unknown keys: {packages}', location=location, packages=', '.join(sorted(unknown))))


def strings(value, pattern, location):
    if not isinstance(value, list) or any(not isinstance(item, str) or not pattern.fullmatch(item) for item in value):
        fail(tr('{location}: invalid list', location=location))
    if len(set(value)) != len(value):
        fail(tr('{location}: duplicate entry', location=location))
    return value


def stick_file(drive, name):
    if not isinstance(name, str) or not name or any(ord(character) < 32 for character in name):
        fail(tr('Invalid stick file path'))
    relative = PurePosixPath(name)
    if relative.is_absolute() or '..' in relative.parts or '\\' in name or relative.as_posix() != name:
        fail(tr('Unsafe stick path: {name}', name=name))
    current = Path(drive)
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            fail(tr('Stick symlinks are refused: {name}', name=name))
    if not current.is_file():
        fail(tr('Missing stick file: {name}', name=name))
    if not current.resolve().is_relative_to(Path(drive).resolve()):
        fail(tr('Unsafe stick path: {name}', name=name))
    return current


def checked_file(drive, value, location):
    object_keys(value, ('file', 'sha256'), location)
    digest = value.get('sha256')
    if not isinstance(digest, str) or not SHA256.fullmatch(digest):
        fail(tr('{location}: expected a lowercase SHA-256', location=location))
    path = stick_file(drive, value.get('file'))
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != digest:
        fail(tr('{location}: SHA-256 mismatch for {filename}', location=location, filename=path.name))
    return path


def removable():
    return read_json(data_root() / 'removable-apps.json')


def recipes():
    return {f'{group}/{name}': item for group, items in read_json(data_root() / 'software.json').items()
            for name, item in items.items()}


def removals(profile):
    excluded = set(profile.get('remove', []))
    policies = profile.get('policies', {})
    excluded.update(package for package, review in removable().items() if policies.get(review['group']) is False)
    return excluded


def validate(drive):
    drive = Path(drive).resolve()
    profile = read_json(stick_file(drive, 'eitr-profile.json'))
    object_keys(profile, ('version', 'name', 'remove', 'add', 'defaults', 'setup', 'policies'), 'profile')
    if type(profile.get('version')) is not int or profile['version'] != 1:
        fail(tr('Profile version must be 1'))
    name = profile.get('name')
    if not isinstance(name, str) or not 1 <= len(name) <= 100 or any(ord(character) < 32 for character in name):
        fail(tr('Profile name must be 1–100 printable characters'))
    reviewed = removable()
    for package in strings(profile.get('remove', []), PACKAGE, 'remove'):
        if package not in reviewed:
            fail(tr('Protected or unknown package cannot be removed: {package}', package=package))
    policies = profile.get('policies', {})
    object_keys(policies, {'remote_access', 'assistants_together', 'update_channel',
                           *(review['group'] for review in reviewed.values())}, 'policies')
    for key, value in policies.items():
        if key == 'update_channel':
            if value != 'stable':
                fail(tr('policies.update_channel may only pin stable'))
        elif type(value) is not bool:
            fail(tr('policies.{key}: expected true or false', key=key))
    additions = profile.get('add', {})
    object_keys(additions, ('recipes', 'packages', 'flathub', 'files'), 'add')
    selected = additions.get('recipes', [])
    strings(selected, re.compile(r'[a-z0-9-]+/[a-z0-9-]+\Z'), 'add.recipes')
    catalog = recipes()
    for name in selected:
        if name not in catalog:
            fail(tr('Unknown recipe: {name}', name=name))
        if catalog[name]['source'] not in ('pacman', 'flatpak'):
            fail(tr('Recipe {name} requires an AUR build or an interactive per-user installer; use a stick package instead', name=name))
    packages = strings(additions.get('packages', []), PACKAGE, 'add.packages')
    strings(additions.get('flathub', []), APP_ID, 'add.flathub')
    files = additions.get('files', [])
    if not isinstance(files, list):
        fail(tr('add.files must be a list'))
    for entry in files:
        path = checked_file(drive, entry, 'add.files')
        if not re.search(r'\.pkg\.tar(?:\.(zst|xz|gz))?$', path.name):
            fail(tr('Not an Arch package file: {filename}', filename=path.name))
    blocked = removals(profile)
    added_packages = set(packages)
    for name in selected:
        added_packages.update(catalog[name]['packages'])
        if policies.get(name.split('/')[0].replace('-', '_')) is False:
            fail(tr('Recipe disabled by policy: {name}', name=name))
    if blocked & added_packages:
        fail(tr('Added packages are also removed: {packages}', packages=', '.join(sorted(blocked & added_packages))))
    defaults = profile.get('defaults', {})
    object_keys(defaults, ('theme', 'wallpaper', 'browser', 'update_channel', 'repository'), 'defaults')
    if 'theme' in defaults:
        theme = defaults['theme']
        code = data_root().parent if data_root().name == 'distro' else data_root()
        if not isinstance(theme, str) or not PACKAGE.fullmatch(theme) or not (code / 'themes' / theme / 'colors.toml').is_file():
            fail(tr('Unknown theme: {theme}', theme=theme))
    if 'browser' in defaults and defaults['browser'] not in ('firefox', 'chromium'):
        fail(tr('Browser must be firefox or chromium (install it with add.packages)'))
    if defaults.get('browser') == 'chromium' and 'chromium' not in added_packages:
        fail(tr('Chromium default requires add.packages chromium or its recipe'))
    if defaults.get('browser') in blocked:
        fail(tr('Default browser is removed'))
    if 'update_channel' in defaults and defaults['update_channel'] not in ('stable', 'testing'):
        fail(tr('Update channel must be stable or testing'))
    if policies.get('update_channel') == 'stable' and defaults.get('update_channel', 'stable') != 'stable':
        fail(tr('Update channel conflicts with stable policy'))
    if 'wallpaper' in defaults:
        path = checked_file(drive, defaults['wallpaper'], 'defaults.wallpaper')
        from PIL import Image
        try:
            with Image.open(path) as image:
                if image.format not in ('PNG', 'JPEG', 'WEBP'):
                    fail(tr('Wallpaper must be PNG, JPEG or WebP'))
                image.verify()
        except (OSError, ValueError) as error:
            fail(tr('Invalid wallpaper: {error}', error=error))
    if 'repository' in defaults:
        repository = defaults['repository']
        object_keys(repository, ('name', 'server', 'key'), 'defaults.repository')
        name, server = repository.get('name'), repository.get('server')
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9-]*', name) or name in ('options', 'core', 'extra', 'multilib', 'eitr', 'eitr-testing'):
            fail(tr('Invalid or reserved repository name'))
        if not isinstance(server, str) or any(character.isspace() for character in server) or any(character in server for character in '\\[]#'):
            fail(tr('Invalid repository server URL'))
        url = urlsplit(server)
        if url.scheme != 'https' or not url.hostname or url.username or url.password or url.fragment or url.query:
            fail(tr('Repository server must use HTTPS without credentials, query or fragment'))
        key = checked_file(drive, repository.get('key'), 'repository.key')
        with tempfile.TemporaryDirectory(prefix='eitr-profile-gpg-') as temporary:
            result = subprocess.run(['gpg', '--homedir', temporary, '--batch', '--with-colons', '--show-keys', str(key)],
                                    capture_output=True, text=True)
        if result.returncode or sum(line.startswith('pub:') for line in result.stdout.splitlines()) != 1 or 'sec:' in result.stdout:
            fail(tr('Repository key must contain exactly one OpenPGP public key'))
    if 'setup' in profile:
        checked_file(drive, profile['setup'], 'setup')
    return profile


def summary(profile):
    lines = [tr('Organization profile: {name}', name=profile['name'])]
    for package in sorted(removals(profile)):
        lines.append(tr('Remove: {value}', value=package))
    for kind, values in profile.get('add', {}).items():
        for value in values:
            lines.append(tr('Add: {kind}: {value} ({connection})', kind=kind,
                            value=json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else value,
                            connection=tr('offline stick file') if kind == 'files' else tr('internet required')))
    for key, value in profile.get('defaults', {}).items():
        lines.append(tr('Default: {key}: {value}', key=key, value=json.dumps(value, ensure_ascii=False)))
    for key, value in profile.get('policies', {}).items():
        lines.append(tr('Policy: {key}: {value}', key=key, value=str(value)))
    if 'setup' in profile:
        lines.append(tr('Run once as root: {value}', value=json.dumps(profile['setup'])))
    lines.append(tr('Policies restrict Eitr tools. A user with root can override them.'))
    return '\n'.join(lines)


def file_entries(profile):
    entries = list(profile.get('add', {}).get('files', []))
    defaults = profile.get('defaults', {})
    entries += [defaults[key] for key in ('wallpaper',) if key in defaults]
    if 'repository' in defaults:
        entries.append(defaults['repository']['key'])
    if 'setup' in profile:
        entries.append(profile['setup'])
    return entries


def snapshot(drive, destination):
    """Copy only reviewed files into private staging, then revalidate that copy."""
    import shutil
    profile = validate(drive)
    destination = Path(destination)
    for entry in file_entries(profile):
        source = stick_file(drive, entry['file'])
        target = destination / entry['file']
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (destination / 'eitr-profile.json').write_text(json.dumps(profile) + '\n')
    return validate(destination)


def preflight_packages(profile, drive, run=subprocess.run, databases=None):
    """Read package metadata before any installation target is touched."""
    excluded = removals(profile)
    if excluded:
        databases = list(Path('/var/lib/pacman/sync').glob('*.db')) if databases is None else databases
        protected = protected_packages(dependency_graph(databases))
        conflict = protected & excluded
        if conflict:
            fail(tr('Protected dependency cannot be removed: {packages}', packages=', '.join(sorted(conflict))))
    catalog = recipes()
    packages = list(profile.get('add', {}).get('packages', []))
    for name in profile.get('add', {}).get('recipes', []):
        if catalog[name]['source'] == 'pacman':
            packages += catalog[name]['packages']
    if packages:
        result = run(['pacman', '-Si', '--', *packages], capture_output=True, text=True)
        if result.returncode:
            fail(tr('Unknown or unavailable repository package: {reason}', reason=result.stderr.strip()))
    for entry in profile.get('add', {}).get('files', []):
        result = run(['pacman', '-Qp', '--print-format', '%n', '--', str(stick_file(drive, entry['file']))],
                     capture_output=True, text=True)
        if result.returncode or not PACKAGE.fullmatch(result.stdout.strip()):
            fail(tr('Invalid package archive: {value}', value=entry['file']))
        if result.stdout.strip() in removals(profile):
            fail(tr('Stick package is also removed: {package}', package=result.stdout.strip()))


def preflight_flatpaks(profile, run=subprocess.run):
    """Query remote metadata in a disposable user installation, never the real home."""
    import os
    requests = []
    if profile.get('add', {}).get('flathub'):
        requests.append(('flathub', 'https://dl.flathub.org/repo/flathub.flatpakrepo',
                         profile['add']['flathub']))
    catalog = recipes()
    for name in profile.get('add', {}).get('recipes', []):
        item = catalog[name]
        if item['source'] == 'flatpak':
            requests.append((item['remote'], item['url'], item['packages']))
    if not requests:
        return
    with tempfile.TemporaryDirectory(prefix='eitr-profile-flatpak-') as temporary:
        (Path(temporary) / 'runtime').mkdir(mode=0o700)
        environment = dict(os.environ, HOME=temporary, XDG_CONFIG_HOME=temporary + '/config',
                           XDG_DATA_HOME=temporary + '/data', XDG_CACHE_HOME=temporary + '/cache',
                           XDG_STATE_HOME=temporary + '/state', XDG_RUNTIME_DIR=temporary + '/runtime',
                           FLATPAK_USER_DIR=temporary + '/flatpak', GNUPGHOME=temporary + '/gnupg',
                           DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', DBUS_SYSTEM_BUS_ADDRESS='unix:path=/nonexistent')
        for remote, url, apps in requests:
            try:
                result = run(['flatpak', 'remote-add', '--user', '--if-not-exists', remote, url],
                             env=environment, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
                if result.returncode:
                    fail(tr('Cannot validate Flatpak remote {remote}: {reason}', remote=remote, reason=result.stderr.strip()))
                for app in apps:
                    result = run(['flatpak', 'remote-info', '--user', remote, app], env=environment,
                                 stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
                    if result.returncode:
                        fail(tr('Unknown or unavailable Flatpak app {app}: {reason}', app=app, reason=result.stderr.strip()))
            except (OSError, subprocess.TimeoutExpired) as error:
                fail(tr('Cannot validate Flatpak additions (internet and flatpak required): {error}', error=error))


def check(drive):
    profile = validate(drive)
    preflight_packages(profile, drive)
    preflight_flatpaks(profile)
    return profile


def protected_packages(graph=None):
    """Protected roots and their transitive runtime dependencies, including providers."""
    root = data_root()
    protected = {'eitr-desktop', 'eitr-artwork'}
    for manifest in ('packages.txt', 'aur-packages.txt', 'local-packages.txt'):
        path = root / manifest
        if path.is_file():
            protected.update(line.split('#')[0].strip() for line in path.read_text().splitlines())
    protected.discard('')
    protected.discard('eitr-sunshine')
    pending = list(protected)
    graph = graph or {}
    while pending:
        package = pending.pop()
        for dependency in graph.get(package, ()):
            dependency = re.split(r'[<>=]', dependency, maxsplit=1)[0]
            if dependency and dependency not in protected:
                protected.add(dependency)
                pending.append(dependency)
    return protected


def dependency_graph(databases):
    import tarfile
    graph, providers = {}, {}
    for database in databases:
        try:
            with tarfile.open(database) as archive:
                for member in archive:
                    if not member.isfile() or not member.name.endswith('/desc'):
                        continue
                    fields = {}
                    key = None
                    with archive.extractfile(member) as stream:
                        for line in stream.read().decode().splitlines():
                            if line.startswith('%') and line.endswith('%'):
                                key = line.strip('%')
                                fields[key] = []
                            elif line and key:
                                fields[key].append(line)
                    name = fields.get('NAME', [''])[0]
                    graph[name] = fields.get('DEPENDS', [])
                    for provided in fields.get('PROVIDES', []):
                        providers.setdefault(re.split(r'[<>=]', provided)[0], []).append(name)
        except (OSError, ValueError, tarfile.TarError) as error:
            fail(tr('Cannot inspect package dependency database {database}: {error}', database=database, error=error))
    for provided, names in providers.items():
        graph.setdefault(provided, []).extend(names)
    return graph
