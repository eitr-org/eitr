"""On-demand catalog adapter. Workers isolate backend commands behind one deadline."""
import json
import os
from pathlib import Path
import re
import signal
import selectors
import subprocess
import sys
import tempfile
import threading
import time

for parent in Path(__file__).resolve().parents:
    library = parent / 'lib'
    if not (library / 'eitr_paths.py').exists():
        library = parent / 'distro/lib'
    if (library / 'eitr_paths.py').exists():
        sys.path.insert(0, str(library))
        break
from eitr_i18n import tr

THEMES = 'https://github.com/eitr-org/eitr-themes'
PLUGINS = 'https://github.com/eitr-org/eitr-plugins'
MUTATIONS = {'prepare', 'confirm', 'discard', 'advice', 'install', 'update', 'remove', 'apply'}


def validate(name, args):
    if name not in {'installed', 'index', 'preview', 'artwork', 'detail', 'source', 'check', *MUTATIONS} or not isinstance(args, dict):
        raise ValueError('invalid-request')
    if args.get('kind') not in {'themes', 'plugins'}:
        raise ValueError('invalid-kind')
    if args.get('channel', 'official') not in {'official', 'community', 'installed', 'git'}:
        raise ValueError('invalid-channel')
    if args['kind'] == 'plugins' and name in {'install', 'update', 'apply'}:
        raise ValueError('Use the plugin prepare/confirm review')
    ids = args.get('ids', []) if name == 'install' or name == 'prepare' and 'ids' in args else [args.get('id')] if name in {'update', 'remove', 'apply', 'preview', 'artwork', 'detail'} else []
    if not isinstance(ids, list) or (name == 'install' and not ids) or len(ids) > 1000 or any(
            not isinstance(theme_id, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', theme_id) or len(theme_id) > 64 for theme_id in ids):
        raise ValueError('invalid-id')

    if 'removePackages' in args:
        from eitr_plugin_packages import names
        names(args['removePackages'], limit=4096)
    if name == 'detail' and args['kind'] == 'themes' and args.get('channel') != 'community':
        raise ValueError('invalid-detail-request')
    if name in {'confirm', 'advice', 'source'} and (not isinstance(args.get('token'), str) or len(args['token']) > 128):
        raise ValueError('invalid-review-token')
    if name == 'artwork':
        from eitr_theme_packages import relative
        relative(args.get('path'))
    if args.get('channel') == 'git' and (name != 'artwork' or not isinstance(args.get('url'), str)):
        raise ValueError('invalid-git-request')


class CatalogDomain:
    def __init__(self, command=None):
        self.action_lock = threading.Lock()
        self.transport_lock = threading.Lock()
        self.process = None
        self.review_stage = None
        self.command = command or [sys.executable, str(Path(__file__).resolve()), '--worker', str(os.getpid())]

    def close(self):
        process, self.process = self.process, None
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
        if self.review_stage is not None:
            self.review_stage.cleanup()
            self.review_stage = None

    def exchange(self, name, args, cancelled):
        # One persistent backend worker for the domain, not a Python process per
        # read. A cancelled operation destroys it; the next explicit request may
        # start a fresh worker, but the interrupted request is never resent.
        if self.process is None:
            from eitr_paths import cache
            parent = cache('eitr/catalog-reviews')
            parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            self.review_stage = tempfile.TemporaryDirectory(prefix='session-', dir=parent)
            environment = dict(os.environ, EITR_CATALOG_REVIEW_CACHE=self.review_stage.name)
            self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, start_new_session=True, bufsize=0, env=environment)
        process = self.process
        deadline = time.monotonic() + (300 if name in MUTATIONS else 60)
        frame = memoryview((json.dumps(dict(name=name, args=args)) + '\n').encode())
        payload = bytearray()
        with selectors.DefaultSelector() as selector:
            os.set_blocking(process.stdin.fileno(), False)
            selector.register(process.stdin, selectors.EVENT_WRITE)
            while frame:
                if cancelled.is_set() or time.monotonic() >= deadline:
                    raise TimeoutError()
                if selector.select(0.1):
                    frame = frame[os.write(process.stdin.fileno(), frame):]
            selector.unregister(process.stdin)
            selector.register(process.stdout, selectors.EVENT_READ)
            while not cancelled.is_set() and time.monotonic() < deadline:
                if not selector.select(0.1):
                    continue
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    raise OSError('Catalog worker stopped')
                payload.extend(chunk)
                if len(payload) > 240000:
                    raise ValueError('Catalog response too large')
                if payload.endswith(b'\n'):
                    result = json.loads(payload)
                    if not isinstance(result, dict):
                        raise ValueError('Invalid catalog response')
                    return result
        raise TimeoutError()

    def request(self, name, args, cancelled):
        validate(name, args)
        mutation = name in MUTATIONS
        if mutation and not self.action_lock.acquire(blocking=False):
            return {'error': tr('Catalog action already running')}
        acquired = False
        try:
            while not cancelled.is_set():
                if self.transport_lock.acquire(timeout=0.1):
                    acquired = True
                    break
            if cancelled.is_set():
                return {}
            return self.exchange(name, args, cancelled)
        except TimeoutError:
            self.close()
            return {'error': tr('Outcome unknown; refresh Installed before trying again') if mutation else tr('Repository unavailable; retry')}
        except (OSError, ValueError):
            self.close()
            return {'error': tr('Outcome unknown; refresh Installed before trying again') if mutation else tr('Catalog backend unavailable')}
        finally:
            if acquired:
                self.transport_lock.release()
            if mutation:
                self.action_lock.release()


def community(name, args):
    from eitr_paths import cache
    from eitr_community import validate_index, fetch
    from eitr_plugin_manifest import unique_object
    from eitr_theme_packages import Themes, SOURCE
    import urllib.request
    target = cache('eitr/community-index.json')
    if name == 'index':
        with urllib.request.urlopen('https://raw.githubusercontent.com/eitr-org/eitr-community/HEAD/index.json', timeout=15) as response:
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
                rows.append(dict(metadata, **{key: value for key, value in row.items() if key != 'description'}, kind='community'))
            save_plugin_rows(rows, 'community')
            return {'items': rows}
        return {'items': [dict(row, name=row['id'].replace('-', ' ').title(), kind='community') for row in index[args['kind']]]}
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
        if row['kind'] not in {'builtin', 'official', 'own'} and any(
                candidate['id'] == row['id'] and normalized_url(candidate['repository']) == normalized_url(url)
                and candidate['folder'] == source.get('folder', source.get('path')) for candidate in index[kind]):
            row['kind'] = 'community'
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


_PLUGIN_BACKEND = None
_THEME_BACKEND = None


def plugin_backend():
    global _PLUGIN_BACKEND
    if _PLUGIN_BACKEND is None:
        from eitr_plugins import Plugins
        _PLUGIN_BACKEND = Plugins()
    return _PLUGIN_BACKEND


def save_plugin_rows(rows, channel='official'):
    from eitr_paths import cache
    target = cache('eitr/catalog-previews/plugins' + ('-community' if channel == 'community' else '') + '.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(rows, handle)
    temporary.replace(target)


def worker(name, args):
    from eitr_paths import code_root, cache
    from eitr_theme_packages import Themes
    from eitr_plugins import Plugins
    validate(name, args)
    kind = args['kind']
    if args.get('channel') == 'community' and name in {'index', 'install'}:
        return community(name, args)
    if kind == 'themes':
        global _THEME_BACKEND
        if _THEME_BACKEND is None:
            _THEME_BACKEND = Themes()
        backend = _THEME_BACKEND
        if name == 'discard':
            backend.discard_reviews()
            return {}
        if name == 'prepare':
            return {'review': backend.prepare_review(args['url'], theme_id=args.get('id'), theme_ids=args.get('ids'))}
        if name == 'confirm':
            return {'result': backend.confirm_review(args['token'])}
        if name == 'installed':
            return {'items': installed_badges(backend.installed(), kind)}
        if name == 'index':
            result = backend.index(THEMES)
            target = cache('eitr/catalog-previews/index.json')
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(result, handle)
            temporary.replace(target)
            return {'items': result['themes']}
        if name == 'detail' and args.get('channel') == 'community':
            return community_detail(args['id'], backend)
        if name in {'preview', 'artwork'}:
            return artwork_preview(kind, args['id'], backend, args.get('path'), args.get('channel', 'official'), args.get('url'))
        if name == 'install':
            return {'result': backend.install(THEMES, args['ids'])}
        if name == 'check':
            return {'updates': backend.check()}
        if name == 'apply':
            subprocess.run(['bash', str(code_root() / 'walker/scripts/actions/style/apply.sh'), args['id']], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            return {}
        return {'result': getattr(backend, name)(args['id'])}
    backend = plugin_backend()
    if name == 'installed':
        return {'items': installed_badges([dict(row, kind='official' if row['official'] else 'third-party') for row in backend.installed()], kind)}
    if name == 'check':
        return {'updates': backend.check_updates()}
    if name == 'remove':
        return {'result': backend.remove(args['id'], lambda record: True,
                                           lambda packages: [name for name in packages if name in args.get('removePackages', [])])}
    if name == 'discard':
        backend.discard_reviews()
        return {}
    if name == 'confirm':
        return {'result': backend.confirm_review(args['token'])}
    if name == 'advice':
        return {'answer': backend.review_advice(args['token'])}
    if name == 'source':
        return backend.review_source(args['token'], args.get('path'), args.get('offset', 0))
    if name == 'prepare':
        if args.get('url'):
            review = backend.prepare_review(args['url'], plugin_id=args.get('id'))
            if 'choices' in review:
                import hashlib
                from eitr_plugin_install import normalized_url
                # Cards need artwork paths: list the repository's plugins without
                # fetching code or media, and keep the rows for artwork requests.
                offered = {choice['id'] for choice in review['choices']}
                rows = [row for row in backend.catalog(review['url']) if row['id'] in offered]
                listing = cache('eitr/catalog-previews') / ('plugins-git-' + hashlib.sha256(normalized_url(review['url']).encode()).hexdigest() + '.json')
                listing.parent.mkdir(parents=True, exist_ok=True)
                listing.write_text(json.dumps(dict(url=review['url'], plugins=rows)))
                review['choices'] = rows
            return {'review': review}
        item_id = args['id']
        if args.get('updating'):
            from eitr_community import validate_index
            from eitr_plugin_install import normalized_url
            record = backend.records()[item_id]
            try:
                index = validate_index(json.loads(cache('eitr/community-index.json').read_text()))
            except (OSError, ValueError):
                index = {'plugins': []}
            row = next((row for row in index['plugins'] if row['id'] == item_id and
                        normalized_url(record['url']) == normalized_url(row['repository']) and
                        record.get('path', '') == row['folder']), None)
            try:
                if row is not None:
                    review = backend.prepare_review(plugin_id=item_id, folder=row['folder'], revision=row['commit'], updating=True)
                    return {'review': dict(review, license=row['license'], maintainer=row['maintainer'])}
                if args.get('channel') == 'community':
                    raise ValueError('Community source differs from installed plugin')
                return {'review': backend.prepare_review(plugin_id=item_id, updating=True)}
            except ValueError as error:
                # Nothing newer than the installed commit: not an error, just up to date.
                if str(error) == 'No plugin changes to review':
                    return {'upToDate': True}
                raise
        channel = args.get('channel', 'official')
        rows = json.loads(cache('eitr/catalog-previews/plugins' + ('-community' if channel == 'community' else '') + '.json').read_text())
        row = next(row for row in rows if row['id'] == item_id)
        review = backend.prepare_review(row['repository'], plugin_id=item_id, folder=row['folder'],
                                        revision=row['commit'] if channel == 'community' else None)
        return {'review': dict(review, license=row.get('license', ''), maintainer=row.get('maintainer', ''))}
    if name in {'preview', 'artwork'}:
        return artwork_preview(kind, args['id'], backend, args.get('path'), args.get('channel', 'official'), args.get('url'))
    if name == 'detail':
        rows = json.loads(cache('eitr/catalog-previews/plugins' + ('-community' if args.get('channel') == 'community' else '') + '.json').read_text())
        return {'item': next(row for row in rows if row['id'] == args['id'])}
    rows = backend.catalog(PLUGINS)
    save_plugin_rows(rows)
    return {'items': rows}


def response(name, args):
    try:
        return worker(name, args)
    except Exception as error:
        return {'error': str(error) if isinstance(error, (ValueError, OSError)) else tr('Catalog operation failed')}


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        # The worker and its current command must not outlive a crashed broker.
        import ctypes
        def stop_worker(signal_number, stack_frame):
            os.killpg(os.getpgrp(), signal.SIGKILL)
        signal.signal(signal.SIGTERM, stop_worker)
        if ctypes.CDLL(None).prctl(1, signal.SIGTERM, 0, 0, 0) != 0 or os.getppid() != int(sys.argv[2]):
            stop_worker(None, None)
        for line in sys.stdin:
            try:
                frame = json.loads(line)
                result = response(frame['name'], frame['args'])
            except (KeyError, ValueError):
                result = {'error': tr('Catalog operation failed')}
            print(json.dumps(result), flush=True)
    else:
        print(json.dumps(response(sys.argv[1], json.loads(sys.argv[2]))))
