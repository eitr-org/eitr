"""Data-only theme packages, sparse Git catalog and per-user transactions."""
import contextlib
import fcntl
from functools import partial
import hashlib
import json
import os
import re
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile
import secrets
import time
import tomllib

from eitr_paths import cache, code_root, config, data, theme_paths
from eitr_plugin_install import git, normalized_url, repository_url, COMMIT
from eitr_plugin_manifest import identifier, string, unique_object

MANIFEST = 'eitr-theme.json'
SOURCE = '.eitr-theme-source.json'
MAX_BYTES = 128 * 1024 * 1024
MAX_FILES = 1000
MAX_PREVIEW = 2 * 1024 * 1024
ROOT_FILES = {'colors.toml', 'display-name', 'light.mode', 'preview.png', 'artwork.md', 'rgb.color', MANIFEST}
ASSET_FOLDERS = {'backgrounds', 'backgrounds-ultrawide', 'motion'}
# Hyprland border values: rgb()/rgba() colors, optionally a gradient angle.
HYPRLAND_COLORS = r'(?:rgba\([0-9a-fA-F]{8}\)|rgb\([0-9a-fA-F]{6}\))(?: (?:rgba\([0-9a-fA-F]{8}\)|rgb\([0-9a-fA-F]{6}\)))*(?: [0-9]{1,3}deg)?'
ASSET_EXTENSIONS = {'.jpg', '.png', '.json'}
GENERATED = {'icons.theme', 'vscode.json', 'neovim.lua', 'btop.theme', 'dolphin.theme'}
PALETTE_KEYS = ('background', 'foreground', 'accent', *(f'color{number}' for number in range(16)))

def palette(root):
    colors = tomllib.loads((Path(root) / 'colors.toml').read_text())
    return {key: colors[key] for key in PALETTE_KEYS} if all(key in colors for key in PALETTE_KEYS) else {}

OFFICIAL = 'github.com/eitr-org/eitr-themes'


def official(url):
    return normalized_url(url) == OFFICIAL


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ValueError('Invalid theme fields')


def read_json(path, limit=1024 * 1024):
    if path.is_symlink() or path.stat().st_size > limit:
        raise ValueError('Invalid or oversized theme JSON')
    return json.loads(path.read_text(), object_pairs_hook=unique_object)


def relative(value):
    string(value, 256)
    path = PurePosixPath(value)
    if (path.is_absolute() or str(path) != value or any(part.startswith('.') for part in path.parts)
            or '\\' in value or not path.parts):
        raise ValueError('Unsafe catalog path')
    return value


def manifest(root):
    value = read_json(Path(root) / MANIFEST)
    keys(value, ('schemaVersion', 'id', 'name', 'description', 'version', 'light'))
    if type(value['schemaVersion']) is not int or value['schemaVersion'] != 1 or type(value['light']) is not bool:
        raise ValueError('Unsupported theme schema or light flag')
    identifier(value['id'])
    for field, limit in (('name', 64), ('description', 72), ('version', 64)):
        string(value[field], limit)
    return value


def package_path(filename, *, directory=False):
    path = PurePosixPath(filename)
    parts = path.parts
    if any(part in GENERATED for part in parts):
        raise ValueError('Generated application files are refused: ' + str(path))
    if len(parts) == 1:
        allowed = ASSET_FOLDERS if directory else ROOT_FILES
        if parts[0] not in allowed:
            raise ValueError('Unsupported theme package path: ' + str(path))
    elif parts[0] not in ASSET_FOLDERS or (not directory and path.suffix not in ASSET_EXTENSIONS):
        raise ValueError('Unsupported theme asset: ' + str(path))


def validate(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Theme must be a real directory')
    total = count = 0
    for directory, directories, filenames in os.walk(root, followlinks=False):
        for name in directories + filenames:
            path = Path(directory) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
                raise ValueError('Themes cannot contain links or special files')
            if name.startswith('.') or name == 'own-theme.json':
                raise ValueError('Reserved theme filename')
            package_path(path.relative_to(root), directory=stat.S_ISDIR(mode))
            count += 1
            if count > MAX_FILES:
                raise ValueError('Theme exceeds file-count limit')
            if stat.S_ISREG(mode):
                if mode & 0o111:
                    raise ValueError('Theme contains executable or unsupported file: ' + name)
                total += path.stat().st_size
                if total > MAX_BYTES:
                    raise ValueError('Theme exceeds size limit')
    spec = manifest(root)
    palette = tomllib.loads((root / 'colors.toml').read_text())
    required = {'background', 'foreground', 'accent', *('color' + str(index) for index in range(16))}
    if not required <= palette.keys():
        raise ValueError('Theme palette is incomplete')
    for key, value in palette.items():
        if key == 'mode':
            if value != ('light' if spec['light'] else 'dark'):
                raise ValueError('Palette mode must match light flag')
        elif not isinstance(value, str) or not re.fullmatch(
                HYPRLAND_COLORS if key.startswith('hyprland_') else r'#[0-9a-fA-F]{6}', value):
            raise ValueError('Palette values must be hex colors')
    if (root / 'display-name').read_text().strip() != spec['name']:
        raise ValueError('display-name must match manifest name')
    if (root / 'light.mode').exists() != spec['light']:
        raise ValueError('light.mode must match manifest light flag')
    preview = root / 'preview.png'
    if not preview.is_file() or preview.stat().st_size > MAX_PREVIEW:
        raise ValueError('A small preview.png is required')
    from PIL import Image
    with Image.open(preview) as image:
        if image.format != 'PNG' or max(image.size) > 2048:
            raise ValueError('Preview must be a PNG at most 2048 pixels across')
        image.verify()
    if not (root / 'backgrounds').is_dir() or not any((root / 'backgrounds').iterdir()):
        raise ValueError('Theme needs backgrounds')
    return spec, total


def catalog(root):
    """Generate the canonical index, discovering manifest roots without following links."""
    root = Path(root)
    rows = []
    for directory, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(name for name in directories if not name.startswith('.'))
        if MANIFEST in filenames:
            folder = Path(directory)
            spec, size = validate(folder)
            rows.append({field: spec[field] for field in ('id', 'name', 'description', 'light')} | dict(
                folder=relative(folder.relative_to(root).as_posix()), size=size,
                preview=(folder.relative_to(root) / 'preview.png').as_posix(), palette=palette(folder)))
            directories[:] = []
    return validate_index(rows)


def validate_index(rows):
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError('Catalog must be a bounded list')
    ids, folders = set(), []
    for row in rows:
        keys(row, ('id', 'name', 'description', 'light', 'folder', 'size', 'preview', *(field for field in ('palette', 'wallpapers') if field in row)))
        if 'palette' in row:
            if not isinstance(row['palette'], dict) or set(row['palette']) not in (set(PALETTE_KEYS), {'background', 'foreground', 'accent', *(f'color{number}' for number in range(1, 7))}):
                raise ValueError('Invalid catalog palette')
            if any(not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in row['palette'].values()):
                raise ValueError('Invalid catalog palette')
        identifier(row['id'])
        string(row['name'], 64)
        string(row['description'], 72)
        folder = relative(row['folder'])
        preview = relative(row['preview'])
        if (row['id'] in ids or any(folder == previous or folder.startswith(previous + '/') or previous.startswith(folder + '/') for previous in folders)
                or preview != folder + '/preview.png' or type(row['light']) is not bool
                or type(row['size']) is not int or not 0 < row['size'] <= MAX_BYTES):
            raise ValueError('Invalid or duplicate catalog entry')
        if 'wallpapers' in row:
            if not isinstance(row['wallpapers'], list) or len(row['wallpapers']) > MAX_FILES:
                raise ValueError('Invalid catalog wallpapers')
            seen = set()
            for wallpaper in row['wallpapers']:
                keys(wallpaper, ('path', 'thumbnail', 'size'))
                asset = PurePosixPath(relative(wallpaper['path']))
                thumbnail = relative(wallpaper['thumbnail'])
                if (asset.parent.as_posix() != folder + '/backgrounds' or asset.suffix.lower() not in {'.png', '.jpg'}
                        or thumbnail != f"thumbnails/{row['id']}/{asset.stem}.jpg" or thumbnail in seen
                        or type(wallpaper['size']) is not int or not 0 < wallpaper['size'] <= MAX_BYTES):
                    raise ValueError('Invalid catalog wallpaper')
                seen.add(thumbnail)
        ids.add(row['id'])
        folders.append(folder)
    return sorted(rows, key=lambda row: row['id'])


class Themes:
    def __init__(self, *, allow_file=False, git_timeout=120):
        self.allow_file = allow_file
        self.git = partial(git, timeout=git_timeout)
        self.folder = data('eitr/themes')
        self.cache = cache('eitr/theme-repositories')
        self._reviews = {}

    @contextlib.contextmanager
    def lock(self):
        self.cache.mkdir(parents=True, exist_ok=True)
        with (self.cache / '.lock').open('w') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def repository(self, url):
        repository_url(url, allow_file=self.allow_file)
        target = self.cache / hashlib.sha256(normalized_url(url).encode()).hexdigest()
        if not target.exists():
            temporary = Path(tempfile.mkdtemp(dir=self.cache))
            try:
                self.git(None, 'clone', '--template=', '--filter=blob:none', '--sparse', '--no-checkout',
                    '--no-recurse-submodules', '--', url, str(temporary / 'repo'), allow_file=self.allow_file)
                (temporary / 'repo').rename(target)
            finally:
                shutil.rmtree(temporary)
        self.git(target, 'fetch', '--filter=blob:none', '--no-recurse-submodules', '--', url, 'HEAD', allow_file=self.allow_file)
        revision = self.git(target, 'rev-parse', 'FETCH_HEAD')
        # Reading one blob avoids sparse-checkout's implicit root-file downloads.
        entry = self.git(target, 'ls-tree', revision, '--', 'eitr-catalog.json', allow_file=self.allow_file)
        if not entry.startswith('100644 blob '):
            raise ValueError('Catalog must be a regular non-executable file')
        blob = self.git(target, 'rev-parse', revision + ':eitr-catalog.json', allow_file=self.allow_file)
        if int(self.git(target, 'cat-file', '-s', blob, allow_file=self.allow_file)) > 1024 * 1024:
            raise ValueError('Catalog exceeds size limit')
        raw = self.git(target, 'cat-file', 'blob', blob, allow_file=self.allow_file)
        rows = validate_index(json.loads(raw, object_pairs_hook=unique_object))
        return target, revision, rows

    def index(self, url):
        with self.lock():
            _, revision, rows = self.repository(url)
            return dict(commit=revision, themes=rows, official=official(url))

    def source(self, theme_id):
        identifier(theme_id)
        root = self.folder / theme_id
        if root.is_symlink():
            raise ValueError('Installed theme must not be a symlink')
        if (root / 'own-theme.json').exists() or not (root / SOURCE).is_file():
            raise ValueError('Theme is not an installed catalog package: ' + theme_id)
        record = read_json(root / SOURCE)
        keys(record, ('url', 'commit', 'folder', 'official', *(['community'] if 'community' in record else [])))
        if 'community' in record and record['community'] is not True:
            raise ValueError('Invalid community provenance')
        repository_url(record['url'], allow_file=self.allow_file)
        relative(record['folder'])
        if not isinstance(record['commit'], str) or not COMMIT.fullmatch(record['commit']):
            raise ValueError('Invalid installed commit')
        return record

    def install(self, url, ids, *, updating=False, review=None):
        if not ids or len(set(ids)) != len(ids):
            raise ValueError('Choose distinct theme IDs')
        with self.lock():
            for theme_id in ids:
                identifier(theme_id)
                target = self.folder / theme_id
                if (code_root() / 'themes' / theme_id).exists() or (config('themes') / theme_id).exists():
                    raise ValueError('Theme ID clashes with built-in or override: ' + theme_id)
                if target.exists():
                    if not updating or (target / 'own-theme.json').exists() or normalized_url(self.source(theme_id)['url']) != normalized_url(url):
                        raise ValueError('Theme ID already exists: ' + theme_id)
                elif updating:
                    raise ValueError('Theme is not installed')
            repository, revision, rows = self.repository(url)
            selected = {row['id']: row for row in rows if row['id'] in ids}
            if set(selected) != set(ids):
                raise ValueError('Theme is absent from catalog')
            self.git(repository, 'update-ref', 'refs/eitr/pins/' + revision, revision, allow_file=self.allow_file)
            self.folder.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix='.install-', dir=self.folder) as staging:
                stage = Path(staging)
                for theme_id in ids:
                    row = selected[theme_id]
                    destination = stage / theme_id
                    destination.mkdir()
                    # Enumerate only the chosen tree. Read each regular blob directly;
                    # no checkout filters, attributes, hooks or repository code can run.
                    tree = self.git(repository, 'ls-tree', '-rz', revision + ':' + row['folder'], allow_file=self.allow_file)
                    entries = [entry for entry in tree.split('\0') if entry]
                    if len(entries) > MAX_FILES:
                        raise ValueError('Theme exceeds file-count limit')
                    total = 0
                    for entry in entries:
                        header, filename = entry.split('\t', 1)
                        mode, kind, blob = header.split()
                        relative(filename)
                        package_path(filename)
                        if mode != '100644' or kind != 'blob':
                            raise ValueError('Theme contains executable, link or submodule')
                        size = int(self.git(repository, 'cat-file', '-s', blob, allow_file=self.allow_file))
                        total += size
                        if total > MAX_BYTES:
                            raise ValueError('Theme exceeds size limit')
                        payload = self.git(repository, 'cat-file', 'blob', blob, allow_file=self.allow_file, binary=True)
                        output = destination / filename
                        output.parent.mkdir(parents=True, exist_ok=True)
                        output.write_bytes(payload)
                    spec, size = validate(destination)
                    if (any(spec[field] != row[field] for field in ('id', 'name', 'description', 'light')) or size != row['size']
                            or 'palette' in row and row['palette'] != palette(destination)):
                        raise ValueError('Theme differs from catalog')
                    import importlib.util
                    builder_path = code_root() / 'themes/theme_files.py'
                    builder_spec = importlib.util.spec_from_file_location('eitr_theme_files', builder_path)
                    builder = importlib.util.module_from_spec(builder_spec)
                    builder_spec.loader.exec_module(builder)
                    builder.write_theme_files(destination, official=official(url),
                                              integrations_path=code_root() / 'themes/integrations.json')
                    (destination / SOURCE).write_text(json.dumps(dict(url=url, commit=revision, folder=row['folder'], official=official(url))) + '\n')
                if review is not None:
                    return review(stage, revision, selected)
                moved, backups = [], []
                try:
                    for theme_id in ids:
                        target = self.folder / theme_id
                        if target.exists():
                            backup = stage / (theme_id + '.old')
                            target.rename(backup)
                            backups.append((backup, target))
                        (stage / theme_id).rename(target)
                        moved.append(target)
                except BaseException:
                    for target in moved:
                        shutil.rmtree(target)
                    for backup, target in reversed(backups):
                        backup.rename(target)
                    raise
            return ids

    def discard_reviews(self):
        for review in self._reviews.values():
            review['stage'].cleanup()
        self._reviews.clear()

    def prepare_review(self, url, theme_id=None, theme_ids=None):
        repository_url(url, allow_file=self.allow_file)
        with self.lock():
            _, revision, rows = self.repository(url)
        ids = list(theme_ids) if theme_ids else [theme_id] if theme_id else None
        if ids is None and len(rows) != 1:
            # The window shows these rows as cards; artwork requests read them back
            # from this cache, so only paths this index lists can be fetched.
            listing = cache('eitr/catalog-previews') / ('git-' + hashlib.sha256(normalized_url(url).encode()).hexdigest() + '.json')
            listing.parent.mkdir(parents=True, exist_ok=True)
            listing.write_text(json.dumps(dict(url=url, commit=revision, themes=rows)))
            return dict(choices=rows, url=url, commit=revision, official=official(url), dataOnly=True)
        ids = ids or [rows[0]['id']]
        parent = (Path(os.environ['EITR_CATALOG_REVIEW_CACHE']) / 'themes' if os.environ.get('EITR_CATALOG_REVIEW_CACHE') else cache('eitr/theme-reviews'))
        parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        stage = tempfile.TemporaryDirectory(prefix='review-', dir=parent)

        def capture(package, revision, selected):
            for selected_id in ids:
                shutil.copytree(package / selected_id, Path(stage.name) / selected_id)
            files = {str(path.relative_to(Path(stage.name))): (hashlib.sha256(path.read_bytes()).hexdigest(), bool(path.stat().st_mode & 0o111))
                     for path in Path(stage.name).rglob('*') if path.is_file()}
            token = secrets.token_urlsafe(32)
            specs = [manifest(package / selected_id) for selected_id in ids]
            facts = dict(token=token, url=url, official=official(url), commit=revision,
                         spec=specs[0], specs=specs, themes=[selected[selected_id] for selected_id in ids],
                         files=list(files), dataOnly=True)
            self._reviews[token] = dict(stage=stage, expires=time.monotonic() + 900, files=files, ids=ids)
            return facts
        try:
            return self.install(url, ids, review=capture)
        except BaseException:
            stage.cleanup()
            raise

    def confirm_review(self, token):
        review = self._reviews.pop(token, None)
        if review is None:
            raise ValueError('Review expired; prepare it again')
        try:
            if review['expires'] <= time.monotonic():
                raise ValueError('Review expired; prepare it again')
            root = Path(review['stage'].name)
            files = {}
            for path in root.rglob('*'):
                if path.is_symlink():
                    raise ValueError('Theme review changed')
                if path.is_file():
                    files[str(path.relative_to(root))] = (hashlib.sha256(path.read_bytes()).hexdigest(), bool(path.stat().st_mode & 0o111))
            if files != review['files']:
                raise ValueError('Theme review changed')
            ids = review['ids']
            with self.lock():
                if any((parent / theme_id).exists() for theme_id in ids for parent in (self.folder, code_root() / 'themes', config('themes'))):
                    raise ValueError('Theme ID already exists')
                self.folder.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(prefix='.review-', dir=self.folder) as directory:
                    for theme_id in ids:
                        shutil.copytree(root / theme_id, Path(directory) / theme_id)
                    copied = {str(path.relative_to(Path(directory))): (hashlib.sha256(path.read_bytes()).hexdigest(), bool(path.stat().st_mode & 0o111))
                              for path in Path(directory).rglob('*') if path.is_file() and not path.is_symlink()}
                    if copied != review['files']:
                        raise ValueError('Theme review changed')
                    for theme_id in ids:
                        (Path(directory) / theme_id).rename(self.folder / theme_id)
            return ids
        finally:
            review['stage'].cleanup()

    def installed(self):
        rows = []
        active = config('theme/current')
        active_id = manifest(active)['id'] if (active / MANIFEST).is_file() else None
        for current in (Path.home() / '.cache/current-theme', cache('current-theme')):
            if current.is_file():
                active_id = current.read_text().strip()
        for theme_id, root in theme_paths().items():
            source = None
            if (root / 'own-theme.json').exists():
                kind = 'own'
            elif root.parent == self.folder and (root / SOURCE).exists():
                source = self.source(theme_id)
                kind = 'official' if official(source['url']) else 'community' if source.get('community') else 'third-party'
            else:
                kind = 'builtin' if root.parent == code_root() / 'themes' else 'own'
            rows.append(dict(id=theme_id, name=(root / 'display-name').read_text().strip(),
                             light=(root / 'light.mode').exists(), kind=kind, source=source,
                             description=manifest(root)['description'] if (root / MANIFEST).is_file() else '',
                             palette=palette(root),
                             wallpapers=[dict(path=asset.name, imageUrl=asset.as_uri(), size=asset.stat().st_size)
                                         for asset in sorted((root / 'backgrounds').glob('*'))
                                         if asset.is_file() and not asset.is_symlink() and asset.suffix.lower() in {'.png', '.jpg'}],
                             size=sum(asset.stat().st_size for asset in root.rglob('*') if asset.is_file() and not asset.is_symlink()),
                             previewUrl=(root / 'preview.png').as_uri(), current=theme_id == active_id or root.resolve() == active.resolve()))
        return rows

    def check(self):
        counts = {}
        repositories = {}
        with self.lock():
            for row in self.installed():
                if row['source']:
                    source = row['source']
                    address = normalized_url(source['url'])
                    if address not in repositories:
                        repositories[address] = self.repository(source['url'])
                    repository, revision, _ = repositories[address]
                    counts[row['id']] = int(self.git(repository, 'rev-list', '--count', source['commit'] + '..' + revision,
                                                '--', ':(top,literal)' + source['folder']))
        return counts

    def update(self, theme_id):
        source = self.source(theme_id)
        return self.install(source['url'], [theme_id], updating=True)

    def remove(self, theme_id):
        if any(row['id'] == theme_id and row['kind'] == 'builtin' for row in self.installed()):
            raise ValueError('Built-in themes cannot be removed')
        with self.lock():
            self.source(theme_id)
            # apply.sh and existing pickers use this legacy cache location.
            currents = (Path.home() / '.cache/current-theme', cache('current-theme'))
            active = config('theme/current')
            active_id = manifest(active)['id'] if (active / MANIFEST).is_file() else None
            if active_id == theme_id or any(current.exists() and current.read_text().strip() == theme_id for current in currents):
                raise ValueError('Cannot remove the current theme; apply eitr first')
            target = self.folder / theme_id
            if (target / 'own-theme.json').exists():
                raise ValueError('Cannot remove a user-created theme')
            shutil.rmtree(target)
        return theme_id
