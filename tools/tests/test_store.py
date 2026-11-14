"""Store registry, dispatch, schema compatibility and wallpaper ownership regressions."""
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'walker/tests'))
from home_isolation import setUpModule, tearDownModule
from eitr_community import validate_index, entry
from eitr_store_kinds import load
from eitr_store_backends import dispatch, BACKENDS
from eitr_wallpaper_packages import Wallpapers, validate


class StoreTests(unittest.TestCase):
    def row(self):
        return dict(id='northern-art', repository='https://github.com/example/art', folder='wallpapers/northern-art',
                    maintainer='Example', license='MIT', description='Northern artwork')

    def test_registry_projection_and_dispatch(self):
        registry = load(ROOT / 'distro/store-kinds.json')
        self.assertEqual({row['id'] for row in registry}, {'themes', 'plugins', 'lockscreens', 'wallpapers'})
        self.assertEqual(subprocess.run([sys.executable, str(ROOT / 'tools/store-kinds.py'), '--check']).returncode, 0)
        for row in registry:
            for operation in ('installed', 'index', 'install', 'remove', 'update', 'apply', 'preview'):
                with self.subTest(kind=row['id'], operation=operation), patch.dict(BACKENDS, {row['backend']: lambda name, args: (name, args)}):
                    args = dict(kind=row['id'])
                    self.assertEqual(dispatch(operation, args), (operation, args))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'registry.json'
            for changes in ({'id': '../bad'}, {'sources': ['git']}, {'capabilities': {}}, {'backend': '__import__(bad)'}, {'filters': {}}, {'filters': [dict(id='adds', label='Adds', multiple='yes', options=[])]},
                            {'filters': [dict(id='adds', label='Adds', multiple=True, options=[dict(id='widget', label='Widget', path='../bad')])]}):
                path.write_text(json.dumps([dict(registry[0], **changes)]))
                with self.assertRaises(ValueError):
                    load(path)
            path.write_text(json.dumps([registry[0], registry[0]]))
            with self.assertRaises(ValueError):
                load(path)

    def test_both_index_versions_and_strict_official_flag(self):
        old = dict(schemaVersion=1, themes=[self.row()], plugins=[], removed=[])
        self.assertEqual(validate_index(old), old)
        current = dict(old, schemaVersion=2, wallpapers=[dict(self.row(), official=True)])
        self.assertEqual(validate_index(current), current)
        for flag in (1, 'true', None, []):
            with self.assertRaises(ValueError):
                entry(dict(self.row(), official=flag), 'wallpapers')
        for value in (dict(current, wallpapers=[self.row(), self.row()]), dict(old, wallpapers=[]),
                      dict(current, removed=[dict(kind='wallpapers', id='northern-art', reason='Removed')])):
            with self.assertRaises(ValueError):
                validate_index(value)
        with self.assertRaises(ValueError):
            entry(dict(self.row(), commit='HEAD'), 'plugins')

    def test_store_endpoint_fallback_and_schema_one_wallpapers(self):
        import urllib.error
        from eitr_store_content import community
        old = dict(schemaVersion=1, themes=[self.row()], plugins=[], removed=[])
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {'XDG_CACHE_HOME': directory}):
            response = io.BytesIO(json.dumps(old).encode())
            missing = urllib.error.HTTPError('new', 404, 'Not published', {}, None)
            with patch('urllib.request.urlopen', side_effect=[missing, response]) as request:
                result = community('index', {'kind': 'wallpapers'})
                self.assertEqual(result, {'items': []})
                self.assertIn('/eitr-store/', request.call_args_list[0].args[0])
                self.assertIn('/eitr-community/', request.call_args_list[1].args[0])
            current = dict(old, schemaVersion=2, wallpapers=[dict(self.row(), official=True)])
            with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(current).encode())):
                result = community('index', {'kind': 'wallpapers'})
                self.assertEqual(result['items'][0]['kind'], 'official')
                self.assertEqual(result['items'][0]['channel'], 'community')
            forbidden = urllib.error.HTTPError('new', 403, 'Forbidden', {}, None)
            with patch('urllib.request.urlopen', side_effect=forbidden) as request, self.assertRaises(urllib.error.HTTPError):
                community('index', {'kind': 'themes'})
            self.assertEqual(request.call_count, 1)

    def package(self, directory):
        from PIL import Image
        directory.mkdir(parents=True, exist_ok=True)
        Image.new('RGB', (96, 96), '#123456').save(directory / 'north.png')
        spec = dict(id='northern-art', name='Northern art', description='Two colours', images=['north.png'])
        (directory / 'eitr-wallpapers.json').write_text(json.dumps(spec))
        return spec

    def test_pack_validation_install_picker_apply_and_scoped_remove(self):
        from eitr_own_pictures import wallpapers
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, {
                'HOME': directory, 'XDG_DATA_HOME': directory + '/data', 'XDG_CACHE_HOME': directory + '/cache',
                'XDG_CONFIG_HOME': directory + '/config', 'XDG_STATE_HOME': directory + '/state'}):
            package = Path(directory) / 'package'
            spec = self.package(package)
            self.assertGreater(validate(package)[1], 0)
            backend = Wallpapers()
            backend.folder.mkdir(parents=True)
            unrelated = backend.folder / 'personal.png'
            unrelated.write_bytes((package / 'north.png').read_bytes())
            with patch('eitr_community.fetch', return_value=(package, spec, 'a' * 40)):
                backend.install([self.row()])
                with self.assertRaises(ValueError):
                    backend.install([self.row()])
            self.assertEqual(len(wallpapers()), 2)
            installed = backend.installed()
            self.assertTrue(any(row['id'] == 'northern-art' and row['removable'] for row in installed))
            with patch('subprocess.run') as command:
                backend.apply('northern-art')
                self.assertIn('store-northern-art-north.png', command.call_args.args[0][-1])
                # The worker answers on stdout; the apply script's output must not reach it.
                self.assertIs(command.call_args.kwargs['stdout'], subprocess.DEVNULL)
            with patch.object(backend, 'current_paths', return_value={str(backend.folder / 'store-northern-art-north.png')}), self.assertRaisesRegex(ValueError, 'another wallpaper'):
                backend.remove('northern-art')
            backend.remove('northern-art')
            self.assertTrue(unrelated.exists())
            self.assertEqual(wallpapers(), [unrelated])

    def test_pack_refuses_scripts_links_traversal_and_size(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            spec = self.package(root)
            script = root / 'run.sh'
            script.write_text('exit 99')
            with self.assertRaises(ValueError):
                validate(root)
            script.unlink()
            (root / 'north.png').rename(root / 'source.png')
            (root / 'north.png').symlink_to(root / 'source.png')
            with self.assertRaises(ValueError):
                validate(root)
            (root / 'north.png').unlink()
            (root / 'source.png').rename(root / 'north.png')
            with patch('eitr_wallpaper_packages.MAX_BYTES', 1), self.assertRaises(ValueError):
                validate(root)
            for images in (['../north.png'], ['north.png', 'north.png'], []):
                (root / 'eitr-wallpapers.json').write_text(json.dumps(dict(spec, images=images)))
                with self.assertRaises(ValueError):
                    validate(root)

    def test_standalone_repository_validator_uses_identical_rules(self):
        repository = ROOT.parent / 'eitr-store-repo'
        if not repository.exists():
            self.skipTest('Standalone Store repository is a separate release artifact')
        for path in (repository / 'vendor').glob('*.py'):
            self.assertEqual(path.read_bytes(), (ROOT / 'distro/lib' / path.name).read_bytes(), path.name)
        result = subprocess.run([sys.executable, str(repository / 'validate.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
