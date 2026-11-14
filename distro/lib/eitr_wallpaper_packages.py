"""Data-only wallpaper packs. Flat owned files join the existing picture picker."""
from contextlib import contextmanager
import fcntl
import hashlib
import json
from pathlib import Path
import tempfile

from eitr_paths import own, data, config, read_settings, theme_paths, code_root
from eitr_plugin_manifest import identifier, string, unique_object
from eitr_theme_packages import MAX_BYTES, MAX_FILES
from eitr_own_pictures import SUFFIXES, picture_format, wallpapers

MANIFEST = 'eitr-wallpapers.json'


def validate(root):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Wallpaper pack must be a real directory')
    manifest = root / MANIFEST
    if manifest.is_symlink() or manifest.stat().st_size > 65536:
        raise ValueError('Invalid wallpaper manifest')
    spec = json.loads(manifest.read_text(), object_pairs_hook=unique_object)
    if set(spec) != {'id', 'name', 'description', 'images'}:
        raise ValueError('Invalid wallpaper manifest fields')
    identifier(spec['id'])
    string(spec['name'], 80)
    string(spec['description'], 256)
    images = spec['images']
    if not isinstance(images, list) or not images or len(images) > MAX_FILES - 1:
        raise ValueError('Invalid wallpaper count')
    if any(not isinstance(name, str) or Path(name).name != name or name.startswith('.') or '\\' in name or Path(name).suffix.lower() not in SUFFIXES for name in images):
        raise ValueError('Invalid wallpaper filename')
    if len(set(images)) != len(images):
        raise ValueError('Duplicate wallpaper')
    expected = {MANIFEST, *images}
    files = list(root.iterdir())
    if {path.name for path in files} != expected or any(path.is_symlink() or not path.is_file() or path.stat().st_mode & 0o111 for path in files):
        raise ValueError('Wallpaper packs may contain only the manifest and listed images')
    size = sum(path.stat().st_size for path in files)
    if size > MAX_BYTES:
        raise ValueError('Wallpaper pack exceeds size limit')
    for name in images:
        suffix = picture_format((root / name).read_bytes())
        if suffix != Path(name).suffix.lower() and not (suffix == '.jpg' and Path(name).suffix.lower() == '.jpeg'):
            raise ValueError('Wallpaper format differs from its extension')
    return spec, size


class Wallpapers:
    def __init__(self):
        self.folder = own('wallpapers')
        self.records = data('eitr/wallpaper-packs')

    @contextmanager
    def lock(self):
        self.records.mkdir(parents=True, exist_ok=True)
        with (self.records / '.lock').open('w') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def current_paths(self):
        from eitr_wallpapers import saved_global
        assignments = read_settings(config('eitr/wallpapers.json')).get('assignments', {})
        values = list(assignments.values()) if isinstance(assignments, dict) else []
        return {str(Path(path).resolve()) for path in [saved_global(), *values] if isinstance(path, str) and path}

    def installed(self):
        rows, owned = [], set()
        current = self.current_paths()
        for record in sorted(self.records.glob('*.json')):
            spec = json.loads(record.read_text())
            paths = [self.folder / name for name in spec['files']]
            owned.update(paths)
            rows.append(dict(id=spec['id'], name=spec['name'], description=spec['description'], kind='official' if spec['source'].get('official') else 'community',
                             previewUrl=paths[0].as_uri() if paths and paths[0].is_file() else '',
                             source=spec['source'], removable=True, current=any(str(path.resolve()) in current for path in paths), wallpapers=[dict(path=path.name, imageUrl=path.as_uri(), size=path.stat().st_size) for path in paths if path.is_file()]))
        paths = [(path, 'own') for path in wallpapers()]
        for theme in theme_paths().values():
            from eitr_own_pictures import pictures_in
            paths += [(path, 'builtin' if path.is_relative_to(code_root()) else 'own') for path in pictures_in(theme / 'backgrounds')]
        for path, origin in paths:
            rows.append(dict(id='image-' + hashlib.sha256(str(path).encode()).hexdigest()[:24], name=path.stem,
                             kind=origin, previewUrl=path.as_uri(), path=str(path), removable=False, current=str(path.resolve()) in current))
        return rows

    def install(self, rows):
        from eitr_community import fetch
        with self.lock(), tempfile.TemporaryDirectory(prefix='eitr-wallpapers-') as directory:
            staged = []
            for row in rows:
                identifier(row['id'])
                record = self.records / (row['id'] + '.json')
                if record.exists():
                    raise ValueError('Wallpaper pack already installed')
                destination = Path(directory) / row['id']
                destination.mkdir()
                package, spec, revision = fetch(row, 'wallpapers', destination)
                files = {name: 'store-' + spec['id'] + '-' + name for name in spec['images']}
                if any((self.folder / name).exists() for name in files.values()):
                    raise ValueError('Wallpaper file already exists')
                staged.append((record, package, spec, files, dict(url=row['repository'], folder=row['folder'], commit=revision, official=row.get('official', False))))
            self.folder.mkdir(parents=True, exist_ok=True)
            written = []
            try:
                for record, package, spec, files, source in staged:
                    for original, name in files.items():
                        target = self.folder / name
                        with target.open('xb') as output:
                            written.append(target)
                            output.write((package / original).read_bytes())
                    record.write_text(json.dumps(dict(id=spec['id'], name=spec['name'], description=spec['description'],
                                                     files=list(files.values()), source=source)))
                    written.append(record)
            except BaseException:
                for path in reversed(written):
                    path.unlink(missing_ok=True)
                raise
        return [row['id'] for row in rows]

    def remove(self, item_id):
        identifier(item_id)
        with self.lock():
            record = self.records / (item_id + '.json')
            spec = json.loads(record.read_text())
            for name in spec['files']:
                if Path(name).name != name or not name.startswith('store-' + item_id + '-'):
                    raise ValueError('Invalid wallpaper ownership record')
            if any(str((self.folder / name).resolve()) in self.current_paths() for name in spec['files']):
                raise ValueError('Choose another wallpaper before removing this pack')
            for name in spec['files']:
                (self.folder / name).unlink(missing_ok=True)
            record.unlink()
        return item_id

    def apply(self, item_id):
        import subprocess
        row = next(row for row in self.installed() if row['id'] == item_id)
        path = row.get('path') or self.folder / json.loads((self.records / (item_id + '.json')).read_text())['files'][0]
        subprocess.run(['bash', str(code_root() / 'walker/scripts/actions/wallpaper/apply.sh'), str(path)], check=True, timeout=90)
        return item_id
