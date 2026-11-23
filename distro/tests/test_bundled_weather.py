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
        self.assertEqual(set(self.manager.records()), {'weather', 'ai-usage', 'hardware'})
        self.manager.remove('ai-usage', lambda record: True)
        self.manager.remove('hardware', lambda record: True)
        self.assertEqual(next(entry for entry in self.manager.ui() if entry['kind'] == 'barItems')['slot'], 'clockEnd')
        self.assertIn({'plugin': 'weather', 'id': 'weather'}, self.manager.placements()['barItems'])
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
        self.assertEqual(len(self.manager.placements()['barItems']), 3)
        self.assertEqual(len(self.manager.ui()), 2)

    def test_override_survives_repeated_placement_and_package_migration(self):
        self.manager.ensure_bundled()
        for slot in ('start', 'clock', 'clockEnd', 'status'):
            self.manager.place('weather', 'weather', slot=slot)
            self.manager.place('weather', 'weather')
            self.manager.ensure_bundled()
            self.assertEqual(next(entry['slot'] for entry in self.manager.placements()['barItems'] if entry['plugin'] == 'weather'), slot)
        for slot in ('unknown', 1, [], {}):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                self.manager.place('weather', 'weather', slot=slot)

    def test_disabled_default_stays_disabled(self):
        self.manager.ensure_bundled()
        self.manager.remove('ai-usage', lambda record: True)
        self.manager.remove('hardware', lambda record: True)
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
            self.assertEqual([entry['id'] for entry in rows], ['weather', 'ai-usage', 'hardware'])
            self.assertTrue(rows[0]['previewUrl'].startswith('file:'))
            self.assertEqual(store.plugins('prepare', {'kind': 'plugins', 'id': 'weather'}), {'bundled': True})
            self.assertTrue(store.plugins('install', {'kind': 'plugins', 'ids': ['weather']})['result'])
            self.assertEqual(len(self.manager.ui()), 7)

    def test_ai_usage_upgrade_preserves_removed_weather_and_can_reinstall(self):
        import eitr_store_backends as store
        marker = Path(os.environ['XDG_STATE_HOME']) / 'eitr/bundled-plugins.json'
        marker.parent.mkdir(parents=True)
        marker.write_text('{"version": 1}')
        self.manager.ensure_bundled()
        self.assertEqual(set(self.manager.records()), {'ai-usage', 'hardware'})
        self.manager.remove('hardware', lambda record: True)
        self.assertEqual({(entry['kind'], entry['id']) for entry in self.manager.ui()},
                         {('barItems', 'usage'), ('panels', 'limits')})
        self.manager.set_enabled('ai-usage', False)
        self.manager.ensure_bundled()
        self.assertEqual(self.manager.ui(), [])
        with patch.object(store, '_PLUGIN_BACKEND', self.manager):
            store.plugins('remove', {'kind': 'plugins', 'id': 'ai-usage'})
            self.manager.ensure_bundled()
            self.assertEqual(self.manager.records(), {})
            self.assertEqual(store.plugins('prepare', {'kind': 'plugins', 'id': 'ai-usage'}), {'bundled': True})
            self.assertTrue(store.plugins('install', {'kind': 'plugins', 'ids': ['ai-usage']})['result'])
        self.assertEqual(self.manager.placements()['barItems'],
                         [{'plugin': 'ai-usage', 'id': 'usage'}, {'plugin': 'hardware', 'id': 'monitor'}])
        self.assertEqual(len(self.manager.ui()), 2)

    def test_hardware_upgrade_and_external_official_replacement(self):
        import eitr_store_backends as store
        marker = Path(os.environ['XDG_STATE_HOME']) / 'eitr/bundled-plugins.json'
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('{"version": 2}')

        # Simulate an existing desktop that had installed the external official hardware plugin
        # with placed widget copies and per-instance settings.
        commit = 'a' * 40
        url = 'https://github.com/eitr-org/eitr-plugins'
        snapshot = self.manager.snapshot(url, commit)
        snapshot.mkdir(parents=True, exist_ok=True)
        (snapshot / 'marker.txt').write_text('old external snapshot')
        self.manager.save({
            'hardware': {
                'id': 'hardware',
                'url': url,
                'path': 'plugins/hardware',
                'commit': commit,
                'installed': '2026-11-01T00:00:00Z',
            }
        })
        widget_copy = {
            'plugin': 'hardware',
            'id': 'hardware',
            'instance': '12345678',
            'monitor': 'DP-1',
            'x': 24,
            'y': 48,
            'width': 480,
            'height': 280,
            'aboveWindows': False,
        }
        placements_file = Path(os.environ['XDG_CONFIG_HOME']) / 'eitr/plugin-placements.json'
        placements_file.parent.mkdir(parents=True, exist_ok=True)
        placements_file.write_text(json.dumps({'version': 3, 'widgets': [widget_copy], 'barItems': []}))
        instance_file = Path(os.environ['XDG_DATA_HOME']) / 'eitr/plugin-data/hardware/hardware/12345678.json'
        instance_file.parent.mkdir(parents=True, exist_ok=True)
        instance_file.write_text('{"mode": "compact"}')

        self.manager.ensure_bundled()
        record = self.manager.records()['hardware']
        self.assertTrue(record.get('bundled'))
        self.assertFalse(snapshot.exists())
        self.assertEqual(self.manager.placements()['widgets'], [widget_copy])
        self.assertIn({'plugin': 'hardware', 'id': 'monitor'}, self.manager.placements()['barItems'])
        self.assertEqual(json.loads(instance_file.read_text()), {'mode': 'compact'})
        self.assertEqual({(entry['kind'], entry['id']) for entry in self.manager.ui()},
                         {('barItems', 'monitor'), ('panels', 'details'), ('widgets', 'hardware')})

        # Unplacing the bar item (Show on the bar = off) keeps the widget and plugin active.
        self.manager.place('hardware', 'monitor', remove=True)
        self.assertEqual(self.manager.placements()['barItems'], [])
        self.assertEqual(self.manager.placements()['widgets'], [widget_copy])

        # Removing bundled hardware later never reinstalls it automatically, and Store can reinstall offline.
        with patch.object(store, '_PLUGIN_BACKEND', self.manager):
            store.plugins('remove', {'kind': 'plugins', 'id': 'hardware'})
            self.manager.ensure_bundled()
            self.assertEqual(self.manager.records(), {})
            self.assertEqual(store.plugins('prepare', {'kind': 'plugins', 'id': 'hardware'}), {'bundled': True})
            self.assertTrue(store.plugins('install', {'kind': 'plugins', 'ids': ['hardware']})['result'])
        self.assertIn({'plugin': 'hardware', 'id': 'monitor'}, self.manager.placements()['barItems'])

    def install_forked_hardware(self, url, author):
        """A Hardware widget plugin installed from a repository other than eitr-org/eitr-plugins."""
        marker = Path(os.environ['XDG_STATE_HOME']) / 'eitr/bundled-plugins.json'
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text('{"version": 2}')
        commit = 'b' * 40
        folder = self.manager.snapshot(url, commit) / 'plugins/hardware'
        folder.mkdir(parents=True, exist_ok=True)
        # The downloadable Hardware plugin's own manifest (eitr-plugins before it was retired).
        (folder / 'eitr-plugin.json').write_text(json.dumps({
            'schemaVersion': 2, 'id': 'hardware', 'name': 'Hardware', 'author': author, 'version': '0.1.0',
            'description': 'Live CPU, GPU, RAM, storage and network usage on your desktop',
            'capabilities': ['hardware'], 'rows': [],
            'ui': {'widgets': [{'id': 'hardware', 'title': 'Hardware', 'qml': 'Hardware.qml', 'minWidth': 260,
                                'minHeight': 88, 'defaultWidth': 480, 'defaultHeight': 280, 'surface': 'panel'}]},
            'icon': 'icon.svg'}))
        (folder / 'Hardware.qml').write_text('import QtQuick\nItem {}\n')
        (folder / 'icon.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"/>')
        self.manager.save({'hardware': {'id': 'hardware', 'url': url, 'path': 'plugins/hardware', 'commit': commit,
                                        'installed': '2026-11-01T00:00:00Z'}})

    def test_eitr_hardware_from_a_fork_is_replaced(self):
        self.install_forked_hardware('git@github.com:someone/eitr-plugins-test.git', 'The Eitr project')
        self.manager.ensure_bundled()
        self.assertTrue(self.manager.records()['hardware'].get('bundled'))
        self.assertIn({'plugin': 'hardware', 'id': 'monitor'}, self.manager.placements()['barItems'])

    def test_another_authors_hardware_plugin_is_kept(self):
        self.install_forked_hardware('https://example.com/hardware.git', 'Someone else')
        self.manager.ensure_bundled()
        self.assertFalse(self.manager.records()['hardware'].get('bundled'))
        self.assertEqual(self.manager.records()['hardware']['url'], 'https://example.com/hardware.git')

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
        hw_migration = Path(__file__).resolve().parents[1] / 'migrations/20261123140000-bundled-hardware.py'
        with patch.object(eitr_plugins, 'Plugins', return_value=self.manager):
            runpy.run_path(str(migration))
            self.assertIn('weather', self.manager.records())
            self.assertIn('hardware', self.manager.records())
            self.manager.remove('weather', lambda record: True)
            self.manager.remove('hardware', lambda record: True)
            runpy.run_path(str(migration))
            runpy.run_path(str(hw_migration))
            self.assertEqual(set(self.manager.records()), {'ai-usage'})
