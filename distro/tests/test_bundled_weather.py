"""Bundled defaults and placement overrides operate offline in isolated homes."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
from eitr_plugins import Plugins
from eitr_plugin_bundled import bundled_root


class BundledWeatherTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        home = Path(self.folder.name)
        self.environment = patch.dict(os.environ, {key: str(home / key) for key in
                                     ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME')})
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.manager = Plugins()
        self.addCleanup(patch.stopall)
        patch('eitr_plugin_install.os.geteuid', return_value=1000).start()
        patch('eitr_plugin_install.policy_reason', return_value=None).start()
        # Bundled operations must never fetch, launch services or install packages.
        patch('eitr_plugin_install.git', side_effect=AssertionError('Git used for bundled plugin')).start()
        patch.object(self.manager, 'systemctl', side_effect=AssertionError('Service operation')).start()

    def test_default_migrates_once_remove_and_reinstall(self):
        self.manager.ensure_bundled()
        self.assertEqual(set(self.manager.records()), {'weather'})
        self.assertEqual(next(entry for entry in self.manager.ui() if entry['kind'] == 'barItems')['slot'], 'clockEnd')
        self.assertEqual(self.manager.placements()['barItems'], [{'plugin': 'weather', 'id': 'weather'}])
        installed = self.manager.installed()[0]
        self.assertTrue(installed['official'])
        self.assertTrue(installed['builtin'])
        self.assertTrue(installed['removable'])
        self.assertTrue(self.manager.remove('weather', lambda record: True))
        self.assertTrue(bundled_root('weather').is_dir())
        self.manager.ensure_bundled()
        self.assertEqual(self.manager.records(), {})
        self.assertEqual(self.manager.ui(), [])
        self.assertEqual(self.manager.bundled_catalog()[0]['id'], 'weather')
        self.manager.install_bundled('weather')
        self.assertEqual(len(self.manager.placements()['barItems']), 1)
        self.assertEqual(len(self.manager.ui()), 2)

    def test_override_survives_repeated_placement_and_package_migration(self):
        self.manager.ensure_bundled()
        for slot in ('start', 'clock', 'clockEnd', 'status'):
            self.manager.place('weather', 'weather', slot=slot)
            self.manager.place('weather', 'weather')
            self.manager.ensure_bundled()
            self.assertEqual(self.manager.placements()['barItems'][0]['slot'], slot)
        for slot in ('unknown', 1, [], {}):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                self.manager.place('weather', 'weather', slot=slot)

    def test_disabled_default_stays_disabled(self):
        self.manager.ensure_bundled()
        self.manager.set_enabled('weather', False)
        self.manager.ensure_bundled()
        self.assertEqual(self.manager.ui(), [])
        self.manager.set_enabled('weather', True)
        self.assertEqual(len(self.manager.ui()), 2)
        self.assertEqual(self.manager.check_updates(), {})

    def test_legacy_placement_versions_and_slot_validation(self):
        self.manager.ensure_bundled()
        target = Path(os.environ['XDG_CONFIG_HOME']) / 'eitr/plugin-placements.json'
        for version in (1, 2, 3):
            target.write_text(json.dumps(dict(version=version, widgets=[], barItems=[dict(plugin='weather', id='weather')])))
            self.assertNotIn('slot', self.manager.placements()['barItems'][0])
        target.write_text(json.dumps(dict(version=3, widgets=[], barItems=[dict(plugin='weather', id='weather', slot='bad')])))
        with self.assertRaises(ValueError):
            self.manager.placements()

    def test_store_offline_discovery_and_reinstall(self):
        import eitr_store_backends as store
        self.manager.ensure_bundled()
        with patch.object(store, '_PLUGIN_BACKEND', self.manager):
            installed = store.plugins('installed', {'kind': 'plugins'})['items'][0]
            self.assertEqual(installed['kind'], 'builtin')
            store.plugins('remove', {'kind': 'plugins', 'id': 'weather'})
            with patch.object(self.manager, 'catalog', side_effect=OSError('offline')):
                rows = store.plugins('index', {'kind': 'plugins'})['items']
            self.assertEqual([entry['id'] for entry in rows], ['weather'])
            self.assertTrue(rows[0]['previewUrl'].startswith('file:'))
            self.assertEqual(store.plugins('prepare', {'kind': 'plugins', 'id': 'weather'}), {'bundled': True})
            self.assertTrue(store.plugins('install', {'kind': 'plugins', 'ids': ['weather']})['result'])
            self.assertEqual(len(self.manager.ui()), 2)

    def test_package_stage_contains_bundled_source_and_helpers(self):
        import importlib.util
        repository = Path(__file__).resolve().parents[2]
        module_spec = importlib.util.spec_from_file_location('layout', repository / 'distro/lib/layout.py')
        layout = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(layout)
        # Stage only this feature's files; the package uses the same mapping for the full tree.
        owner = layout.Layout(repository)
        files = ['distro/lib/eitr_plugin_bundled.py', 'distro/plugins/bundled/weather/eitr-plugin.json',
                 'distro/plugins/bundled/weather/Weather.qml', 'distro/plugins/bundled/weather/icon.svg']
        with tempfile.TemporaryDirectory() as directory, patch.object(owner, 'files', return_value=files):
            owner.stage(directory)
            self.assertTrue((Path(directory) / 'lib/eitr_plugin_bundled.py').is_file())
            self.assertTrue((Path(directory) / 'distro/plugins/bundled/weather/Weather.qml').is_file())

    def test_upgrade_migration_shares_the_one_time_default_marker(self):
        import runpy
        import eitr_plugins
        migration = Path(__file__).resolve().parents[1] / 'migrations/20261114120000-bundled-weather.py'
        with patch.object(eitr_plugins, 'Plugins', return_value=self.manager):
            runpy.run_path(str(migration))
            self.assertIn('weather', self.manager.records())
            self.manager.remove('weather', lambda record: True)
            runpy.run_path(str(migration))
            self.assertEqual(self.manager.records(), {})
