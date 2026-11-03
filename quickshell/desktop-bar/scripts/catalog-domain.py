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
MUTATIONS = {'install', 'update', 'remove', 'apply', 'unhide'}


def validate(name, args):
    if name not in {'installed', 'index', 'preview', 'check', *MUTATIONS} or not isinstance(args, dict):
        raise ValueError('invalid-request')
    if args.get('kind') not in {'themes', 'plugins'}:
        raise ValueError('invalid-kind')
    if args.get('channel', 'official') not in {'official', 'community', 'installed'}:
        raise ValueError('invalid-channel')
    if args['kind'] == 'plugins' and name in {'install', 'update', 'apply', 'unhide'}:
        raise ValueError(tr('Plugin installation and update review are not available yet'))
    ids = args.get('ids', []) if name == 'install' else [args.get('id')] if name in {'update', 'remove', 'apply', 'unhide', 'preview'} else []
    if not isinstance(ids, list) or (name == 'install' and not ids) or len(ids) > 1000 or any(
            not isinstance(theme_id, str) or not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', theme_id) or len(theme_id) > 64 for theme_id in ids):
        raise ValueError('invalid-id')


class CatalogDomain:
    def __init__(self, command=None):
        self.action_lock = threading.Lock()
        self.transport_lock = threading.Lock()
        self.process = None
        self.command = command or [sys.executable, str(Path(__file__).resolve()), '--worker', str(os.getpid())]

    def close(self):
        process, self.process = self.process, None
        if process is not None:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()

    def exchange(self, name, args, cancelled):
        # One persistent backend worker for the domain, not a Python process per
        # read. A cancelled operation destroys it; the next explicit request may
        # start a fresh worker, but the interrupted request is never resent.
        if self.process is None:
            self.process = subprocess.Popen(self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, start_new_session=True, bufsize=0)
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
            if (theme_id in theme_paths(include_hidden=True) or theme_id not in rows
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


def artwork_preview(kind, item_id, backend):
    """Materialize one regular Git blob, validate it, then publish atomically."""
    import hashlib
    import io
    from pathlib import PurePosixPath
    from eitr_paths import cache
    from eitr_plugin_install import git, normalized_url, COMMIT
    from eitr_plugin_manifest import image_asset
    from PIL import Image
    plugin = kind == 'plugins'
    with backend.lock():
        if plugin:
            rows = json.loads(cache('eitr/catalog-previews/plugins.json').read_text())
            row = next(row for row in rows if row['id'] == item_id)
            revision = row['commit']
            repository = cache('eitr/plugin-repositories') / hashlib.sha256(normalized_url(PLUGINS).encode()).hexdigest()
        else:
            from eitr_theme_packages import validate_index
            index = json.loads(cache('eitr/catalog-previews/index.json').read_text())
            revision = index['commit']
            row = next(row for row in validate_index(index['themes']) if row['id'] == item_id)
            repository = backend.cache / hashlib.sha256(normalized_url(THEMES).encode()).hexdigest()
        if not isinstance(revision, str) or not COMMIT.fullmatch(revision):
            raise ValueError('Invalid catalog revision')
        screenshot = bool(row.get('preview'))
        relative = row.get('preview') or (row.get('icon') if plugin else '')
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
            limit = 512 * 1024 if plugin and not screenshot else 2 * 1024 * 1024
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
                    image_asset(Path(directory), temporary.name, preview=screenshot)
                else:
                    with Image.open(io.BytesIO(payload)) as image:
                        if image.format != 'PNG' or max(image.size) > 2048:
                            raise ValueError('Invalid preview')
                        image.verify()
                temporary.replace(target)
        return {'image': target.as_uri()}


def worker(name, args):
    from eitr_paths import code_root, cache
    from eitr_theme_packages import Themes
    from eitr_plugins import Plugins
    validate(name, args)
    kind = args['kind']
    if args.get('channel') == 'community' and name in {'index', 'install'}:
        return community(name, args)
    if kind == 'themes':
        backend = Themes()
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
        if name == 'preview':
            return artwork_preview(kind, args['id'], backend)
        if name == 'install':
            return {'result': backend.install(THEMES, args['ids'])}
        if name == 'check':
            return {'updates': backend.check()}
        if name == 'apply':
            subprocess.run(['bash', str(code_root() / 'walker/scripts/actions/style/apply.sh'), args['id']], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=90)
            return {}
        return {'result': getattr(backend, name)(args['id'])}
    backend = Plugins()
    if name == 'installed':
        return {'items': installed_badges([dict(row, kind='official' if row['official'] else 'third-party') for row in backend.installed()], kind)}
    if name == 'check':
        return {'updates': backend.check_updates()}
    if name == 'remove':
        return {'result': backend.remove(args['id'], lambda record: True)}
    if name == 'preview':
        return artwork_preview(kind, args['id'], backend)
    rows = backend.catalog(PLUGINS)
    target = cache('eitr/catalog-previews/plugins.json')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(rows, handle)
    temporary.replace(target)
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
