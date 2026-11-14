"""Bounded Store index and Git artwork reads; existing machine-local cache names remain stable."""
import json
from pathlib import Path
import re
import tempfile

THEMES = 'https://github.com/eitr-org/eitr-themes'

def community(name, args):
    from eitr_store_backends import plugin_backend, save_plugin_rows
    from eitr_paths import cache
    from eitr_community import validate_index, fetch
    from eitr_plugin_manifest import unique_object
    from eitr_theme_packages import Themes, SOURCE
    import urllib.request
    import urllib.error
    target = cache('eitr/community-index.json')
    if name == 'index':
        url = 'https://raw.githubusercontent.com/eitr-org/eitr-store/HEAD/index.json'
        try:
            response = urllib.request.urlopen(url, timeout=15)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            response = urllib.request.urlopen('https://raw.githubusercontent.com/eitr-org/eitr-community/HEAD/index.json', timeout=15)
        with response:
            payload = response.read(1024 * 1024 + 1)
        if len(payload) > 1024 * 1024:
            raise ValueError('Community index exceeds size limit')
        index = validate_index(json.loads(payload, object_pairs_hook=unique_object))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(index))
        if args['kind'] == 'plugins':
            from eitr_plugins import Plugins
            backend = plugin_backend()
            rows = []
            for row in index['plugins']:
                metadata = backend.catalog(row['repository'], revision=row['commit'], folder=row['folder'], plugin_id=row['id'])[0]
                rows.append(dict(metadata, **{key: value for key, value in row.items() if key != 'description'}, kind='official' if row.get('official') else 'community', channel='community'))
            save_plugin_rows(rows, 'community')
            return {'items': rows}
        return {'items': [dict(row, name=row['id'].replace('-', ' ').title(), kind='official' if row.get('official') else 'community', channel='community') for row in index.get(args['kind'], [])]}
    # Install exactly the reviewed metadata, not an upstream catalog or branch's index.
    index = validate_index(json.loads(target.read_text()))
    backend = Themes()
    rows = {row['id']: row for row in index['themes']}
    backend.folder.mkdir(parents=True, exist_ok=True)
    with backend.lock(), tempfile.TemporaryDirectory(prefix='.community-', dir=backend.folder) as directory:
        stage = Path(directory)
        destinations = []
        from eitr_paths import theme_paths, code_root, config
        for theme_id in args['ids']:
            if (theme_id in theme_paths() or theme_id not in rows
                    or any((parent / theme_id).exists() for parent in (backend.folder, code_root() / 'themes', config('themes')))):
                raise ValueError('Theme ID already exists or is absent from community index')
            destination = stage / theme_id
            destination.mkdir()
            package, spec, revision = fetch(rows[theme_id], 'themes', destination)
            from eitr_theme_packages import official as theme_official
            import importlib.util
            module_spec = importlib.util.spec_from_file_location('eitr_theme_files', code_root() / 'themes/theme_files.py')
            builder = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(builder)
            builder.write_theme_files(package, official=theme_official(rows[theme_id]['repository']), integrations_path=code_root() / 'themes/integrations.json')
            (package / SOURCE).write_text(json.dumps(dict(url=rows[theme_id]['repository'], commit=revision, folder=rows[theme_id]['folder'], official=theme_official(rows[theme_id]['repository']), community=True)) + '\n')
            destinations.append((theme_id, package))
        backend.folder.mkdir(parents=True, exist_ok=True)
        moved = []
        try:
            for theme_id, package in destinations:
                import shutil
                package.rename(backend.folder / theme_id)
                moved.append(backend.folder / theme_id)
        except BaseException:
            for path in moved:
                shutil.rmtree(path)
            raise
    return {'result': args['ids']}


def installed_badges(rows, kind):
    from eitr_paths import cache
    from eitr_plugin_install import normalized_url
    from eitr_community import validate_index
    try:
        index = validate_index(json.loads(cache('eitr/community-index.json').read_text()))
    except (OSError, ValueError):
        return rows
    for row in rows:
        source = row.get('source') or row
        url = source.get('url', '')
        candidate = next((candidate for candidate in index.get(kind, []) if
                          candidate['id'] == row['id'] and normalized_url(candidate['repository']) == normalized_url(url)
                          and candidate['folder'] == source.get('folder', source.get('path'))), None)
        if row['kind'] not in {'builtin', 'official', 'own'} and candidate is not None:
            row['kind'] = 'official' if candidate.get('official') else 'community'
    return rows


def community_detail(item_id, backend):
    """Discover wallpaper names and sizes from trees without materializing images."""
    import hashlib
    from eitr_paths import cache
    from eitr_community import validate_index
    from eitr_plugin_install import git, normalized_url, repository_url
    from eitr_theme_packages import relative, MAX_FILES, MAX_BYTES
    index = validate_index(json.loads(cache('eitr/community-index.json').read_text()))
    row = next(row for row in index['themes'] if row['id'] == item_id)
    url = repository_url(row['repository'], allow_file=backend.allow_file)
    repository = backend.cache / hashlib.sha256(normalized_url(url).encode()).hexdigest()
    options = dict(allow_file=backend.allow_file)
    with backend.lock():
        if not repository.exists():
            git(None, 'clone', '--template=', '--filter=blob:none', '--sparse', '--no-checkout',
                '--no-recurse-submodules', '--', url, str(repository), **options)
        git(repository, 'fetch', '--filter=blob:none', '--no-recurse-submodules', '--', url, 'HEAD', **options)
        revision = git(repository, 'rev-parse', 'FETCH_HEAD', **options)
        tree = git(repository, 'ls-tree', '-rlz', revision + ':' + row['folder'], lazy_fetch=False, **options)
        records = [record.split('\t', 1) for record in tree.split('\0') if record]
        if len(records) > MAX_FILES:
            raise ValueError('Community package exceeds file limit')
        wallpapers, size, preview = [], 0, None
        size_known = True
        for header, filename in records:
            mode, object_kind, blob, length = header.split()
            relative(filename)
            if mode != '100644' or object_kind != 'blob':
                raise ValueError('Artwork must be a regular file')
            length = int(length) if length != 'BAD' else None
            size_known = size_known and length is not None
            size += length or 0
            if filename == 'preview.png':
                preview = row['folder'] + '/' + filename
            asset = Path(filename)
            if asset.parent.as_posix() == 'backgrounds' and asset.suffix.lower() in {'.jpg', '.png'}:
                wallpapers.append(dict(path=row['folder'] + '/' + filename, size=length))
        if size > MAX_BYTES:
            raise ValueError('Community package exceeds size limit')
        result = dict(row, commit=revision, wallpapers=wallpapers, size=size if size_known else None)
        # Read bounded data metadata for the overview; gallery discovery above
        # never requests a wallpaper or thumbnail blob.
        from eitr_theme_packages import manifest, palette, MANIFEST, PALETTE_KEYS
        entries = {filename: header.split() for header, filename in records}
        with tempfile.TemporaryDirectory(prefix='eitr-theme-detail-') as directory:
            metadata = Path(directory)
            for filename in (MANIFEST, 'colors.toml'):
                entry = entries.get(filename)
                if entry is None or int(git(repository, 'cat-file', '-s', entry[2], **options)) > 64 * 1024:
                    raise ValueError('Missing or oversized theme metadata')
                payload = git(repository, 'cat-file', 'blob', entry[2], binary=True, **options)
                if len(payload) > 64 * 1024:
                    raise ValueError('Theme metadata exceeds size limit')
                (metadata / filename).write_bytes(payload)
            spec = manifest(metadata)
            colors = palette(metadata)
            if spec['id'] != item_id or set(colors) != set(PALETTE_KEYS) or any(
                    not isinstance(color, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', color) for color in colors.values()):
                raise ValueError('Invalid theme overview metadata')
            result.update(name=spec['name'], light=spec['light'], palette=colors)
        if preview:
            result['preview'] = preview
        target = cache('eitr/catalog-previews/community-' + item_id + '.json')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result))
        return {'item': result}


def artwork_preview(kind, item_id, backend, requested=None, channel="official", git_url=None):
    """Materialize one regular Git blob, validate it, then publish atomically."""
    import hashlib
    import io
    from pathlib import PurePosixPath
    from eitr_paths import cache
    from eitr_plugin_install import git, normalized_url, COMMIT
    from eitr_plugin_manifest import image_asset, media_asset
    from PIL import Image
    plugin = kind == 'plugins'
    with backend.lock():
        if plugin and channel == 'git':
            from eitr_plugin_install import repository_url
            url = repository_url(git_url, allow_file=backend.allow_file)
            listing = json.loads((cache('eitr/catalog-previews') / ('plugins-git-' + hashlib.sha256(normalized_url(url).encode()).hexdigest() + '.json')).read_text())
            if normalized_url(listing['url']) != normalized_url(url):
                raise ValueError('Repository listing changed; add the address again')
            row = next(row for row in listing['plugins'] if row['id'] == item_id)
            revision = row['commit']
            repository = cache('eitr/plugin-repositories') / hashlib.sha256(normalized_url(row['repository']).encode()).hexdigest()
        elif plugin:
            rows = json.loads(cache('eitr/catalog-previews/plugins' + ('-community' if channel == 'community' else '') + '.json').read_text())
            row = next(row for row in rows if row['id'] == item_id)
            revision = row['commit']
            repository = cache('eitr/plugin-repositories') / hashlib.sha256(normalized_url(row['repository']).encode()).hexdigest()
        elif channel == 'git':
            # Rows a Git address listed for selection, cached by prepare_review.
            from eitr_theme_packages import validate_index
            from eitr_plugin_install import repository_url
            url = repository_url(git_url, allow_file=backend.allow_file)
            listing = json.loads((cache('eitr/catalog-previews') / ('git-' + hashlib.sha256(normalized_url(url).encode()).hexdigest() + '.json')).read_text())
            if normalized_url(listing['url']) != normalized_url(url):
                raise ValueError('Repository listing changed; add the address again')
            revision = listing['commit']
            row = next(row for row in validate_index(listing['themes']) if row['id'] == item_id)
            repository = backend.cache / hashlib.sha256(normalized_url(url).encode()).hexdigest()
        elif channel == 'community':
            from eitr_community import validate_index
            index = validate_index(json.loads(cache('eitr/community-index.json').read_text()))
            source = next(row for row in index['themes'] if row['id'] == item_id)
            row = json.loads(cache('eitr/catalog-previews/community-' + item_id + '.json').read_text())
            if any(source[field] != row[field] for field in source):
                raise ValueError('Community metadata changed; reopen details')
            revision = row['commit']
            repository = backend.cache / hashlib.sha256(normalized_url(source['repository']).encode()).hexdigest()
        else:
            from eitr_theme_packages import validate_index
            index = json.loads(cache('eitr/catalog-previews/index.json').read_text())
            revision = index['commit']
            row = next(row for row in validate_index(index['themes']) if row['id'] == item_id)
            repository = backend.cache / hashlib.sha256(normalized_url(THEMES).encode()).hexdigest()
        if not isinstance(revision, str) or not COMMIT.fullmatch(revision):
            raise ValueError('Invalid catalog revision')
        screenshot = bool(row.get('preview'))
        default = row.get('preview') or (row.get('icon') if plugin else '')
        allowed = {default: 512 * 1024 if plugin and not screenshot else 2 * 1024 * 1024} if default else {}
        for media in row.get('media', []):
            allowed[media['path']] = 24 * 1024 * 1024 if media['type'] == 'video' else 2 * 1024 * 1024
        for wallpaper in row.get('wallpapers', []):
            allowed[wallpaper['path']] = 16 * 1024 * 1024
            if wallpaper.get('thumbnail'):
                allowed[wallpaper['thumbnail']] = 128 * 1024
        relative = default if requested is None else requested
        if requested is not None and requested not in allowed:
            raise ValueError('Artwork path is not listed by this catalog entry')
        if not relative:
            return {'image': ''}
        path = PurePosixPath(relative)
        if path.is_absolute() or '..' in path.parts or not path.parts or '\\' in relative:
            raise ValueError('Invalid artwork path')
        target = cache('eitr/catalog-previews') / (hashlib.sha256((revision + relative).encode()).hexdigest() + path.suffix.lower())
        if not target.exists():
            options = dict(allow_file=backend.allow_file)
            entry = git(repository, 'ls-tree', revision, '--', relative, **options)
            if not entry.startswith('100644 blob '):
                raise ValueError('Artwork must be a regular file')
            blob = git(repository, 'rev-parse', revision + ':' + relative, **options)
            limit = allowed[relative]
            if int(git(repository, 'cat-file', '-s', blob, **options)) > limit:
                raise ValueError('Artwork exceeds size limit')
            payload = git(repository, 'cat-file', 'blob', blob, binary=True, **options)
            if len(payload) > limit:
                raise ValueError('Artwork exceeds size limit')
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=target.parent) as directory:
                temporary = Path(directory) / ('image' + path.suffix.lower())
                temporary.write_bytes(payload)
                if plugin:
                    media = next((asset for asset in row.get('media', []) if asset['path'] == relative), None)
                    if media:
                        media_asset(Path(directory), dict(media, path=temporary.name))
                    else:
                        image_asset(Path(directory), temporary.name, preview=screenshot)
                else:
                    with Image.open(io.BytesIO(payload)) as image:
                        maximum = 2048 if relative == default else 16384
                        if (image.format not in {'PNG', 'JPEG'} or max(image.size) > maximum
                                or image.width * image.height > 64 * 1024 * 1024
                                or relative == default and image.format != 'PNG'):
                            raise ValueError('Invalid artwork')
                        image.verify()
                temporary.replace(target)
        return {'image': target.as_uri(), 'size': target.stat().st_size}


