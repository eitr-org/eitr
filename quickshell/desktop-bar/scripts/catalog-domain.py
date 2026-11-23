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
from eitr_store_previews import CATALOG_LIMIT, cached_discover

THEMES = 'https://github.com/eitr-org/eitr-themes'
PLUGINS = 'https://github.com/eitr-org/eitr-plugins'
MUTATIONS = {'prepare', 'confirm', 'discard', 'advice', 'install', 'update', 'remove', 'apply'}


def bundled_install(name, args):
    """A package-owned plugin (Weather, AI Usage) installs from the package with no review:
    the Store's prepare answers 'bundled' and then asks for this install."""
    from eitr_plugin_bundled import BUNDLED_DEFAULTS
    ids = args.get('ids')
    return name == 'install' and isinstance(ids, list) and len(ids) == 1 and ids[0] in BUNDLED_DEFAULTS


def validate(name, args):
    if name not in {'installed', 'index', 'cached-index', 'preview', 'artwork', 'detail', 'source', 'check', 'changes', *MUTATIONS} or not isinstance(args, dict):
        raise ValueError('invalid-request')
    from eitr_store_kinds import registry
    kinds = registry()
    if args.get('kind') not in kinds:
        raise ValueError('invalid-kind')
    if args.get('channel', 'official') not in {'official', 'community', 'installed', 'git'}:
        raise ValueError('invalid-channel')
    if name == 'cached-index' and (args['kind'] != 'themes' or args.get('channel') not in {'official', 'community'}):
        raise ValueError('invalid-cached-index')
    if args['kind'] == 'plugins' and name in {'install', 'update', 'apply'} and not bundled_install(name, args):
        raise ValueError('Use the plugin prepare/confirm review')
    if name == 'changes':
        from eitr_plugin_manifest import identifier
        if args.get('channel', 'official') == 'git':
            raise ValueError('invalid-channel')
        identifier(args.get('id'))
        return
    if args['kind'] == 'lockscreens':
        if name not in {'installed', 'index', 'install', 'remove', 'apply'} or args.get('channel', 'official') not in {'official', 'installed'}:
            raise ValueError('invalid-lockscreen-request')
        if name in {'install', 'remove'}:
            from eitr_lockscreen_packages import names
            names(args.get('ids', []) if name == 'install' else [args.get('id')])
        return
    if args['kind'] == 'wallpapers' and name not in {'installed', 'index', 'install', 'remove', 'apply', 'preview', 'artwork', 'detail'}:
        raise ValueError('invalid-wallpaper-request')
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

    def exchange(self, name, args, cancelled, deadline=None):
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
        if deadline is None:
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
                if len(payload) > CATALOG_LIMIT:
                    raise ValueError('Catalog response too large')
                if payload.endswith(b'\n'):
                    result = json.loads(payload)
                    if not isinstance(result, dict):
                        raise ValueError('Invalid catalog response')
                    return result
        raise TimeoutError()

    def request(self, name, args, cancelled):
        validate(name, args)
        if name == 'cached-index':
            return cached_discover(args['channel'])
        mutation = name in MUTATIONS
        deadline = time.monotonic() + (300 if mutation else 60)
        if mutation and not self.action_lock.acquire(blocking=False):
            return {'error': tr('Catalog action already running')}
        acquired = False
        try:
            while not cancelled.is_set() and time.monotonic() < deadline:
                if self.transport_lock.acquire(timeout=0.1):
                    acquired = True
                    break
            if cancelled.is_set():
                return {}
            if not acquired:
                return {'error': tr('Repository unavailable; retry')}
            return self.exchange(name, args, cancelled, deadline)
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


from eitr_store_content import community, community_detail, installed_badges, artwork_preview
from eitr_store_backends import plugin_backend, save_plugin_rows


def worker(name, args):
    from eitr_store_backends import dispatch
    validate(name, args)
    return cached_discover(args['channel']) if name == 'cached-index' else dispatch(name, args)


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
