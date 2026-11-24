"""The one-time starter theme ledger and its Store entry points, using no network."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import Mock, call, patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))
import eitr_starter_themes as starter
from eitr_paths import read_settings
from eitr_theme_packages import ThemeUnavailable


class StarterThemesTests(unittest.TestCase):
    def setUp(self):
        directory = self.enterContext(tempfile.TemporaryDirectory())
        self.path = Path(directory) / 'eitr/starter-themes.json'
        self.enterContext(patch.object(starter, 'progress_path', return_value=self.path))
        self.enterContext(patch.object(starter, 'code_root', return_value=ROOT))
        self.installed = self.enterContext(patch.object(starter, 'theme_paths', return_value={}))
        self.dispatch = self.enterContext(patch('eitr_store_backends.dispatch'))
        self.refresh = self.enterContext(patch('eitr_store_content.refresh_community_index'))
        self.rows = starter.load(ROOT / 'distro/starter-themes.json')

    def test_manifest(self):
        self.assertEqual(len(self.rows), 5)
        self.assertEqual([row['channel'] for row in self.rows].count('official'), 2)
        self.assertEqual([row['channel'] for row in self.rows].count('community'), 3)
        for invalid in ([], [self.rows[0]] * 2, [dict(self.rows[0], id='../bad')],
                        [dict(self.rows[0], kind='plugins')], [dict(self.rows[0], channel='git')]):
            with self.subTest(invalid=invalid):
                path = self.path.parent.parent / 'invalid.json'
                path.write_text(json.dumps(invalid))
                with self.assertRaises(ValueError):
                    starter.load(path)

    def test_old_installer_and_welcome_markers_do_not_enroll_upgrades(self):
        self.path.parent.mkdir()
        for name in ('installed-paths', 'welcome-pending'):
            (self.path.parent / name).touch()
        starter.enqueue()
        self.assertTrue(starter.finish())
        self.assertFalse(self.path.exists())
        self.dispatch.assert_not_called()
        self.refresh.assert_not_called()

    def test_fresh_account_runs_through_store_without_apply_and_never_runs_again(self):
        starter.enqueue()
        self.dispatch.assert_not_called()
        self.assertTrue(starter.finish())
        self.assertEqual(self.dispatch.call_args_list, [
            call('install', {'kind': row['kind'], 'channel': row['channel'], 'ids': [row['id']]})
            for row in self.rows
        ])
        self.refresh.assert_called_once_with()
        self.dispatch.reset_mock()
        # A removed theme is absent again, and a later login still leaves it alone.
        starter.enqueue()
        self.assertTrue(starter.finish())
        self.dispatch.assert_not_called()

    def test_resume_after_partial_run_and_skip_already_installed_and_missing(self):
        installed, retry, missing, *remaining = [row['id'] for row in self.rows]
        self.installed.return_value = {installed: Path('/example')}
        starter.enqueue()
        self.dispatch.side_effect = [subprocess.TimeoutExpired('git', 5), ThemeUnavailable(), None, None]
        self.assertFalse(starter.finish())
        self.assertEqual(read_settings(self.path)['outcomes'],
                         {installed: 'installed', missing: 'unavailable',
                          **dict.fromkeys(remaining, 'installed')})

        self.dispatch.reset_mock(side_effect=True)
        self.assertTrue(starter.finish())
        self.dispatch.assert_called_once_with('install', {'kind': 'themes', 'channel': 'official', 'ids': [retry]})

    def test_community_index_failure_leaves_community_pending(self):
        starter.enqueue()
        self.refresh.side_effect = OSError('offline')
        self.assertFalse(starter.finish())
        self.refresh.assert_called_once_with()
        self.assertEqual(read_settings(self.path)['outcomes'],
                         {row['id']: 'installed' for row in self.rows if row['channel'] == 'official'})


class StarterStoreRoutingTests(unittest.TestCase):
    def test_store_routes_each_channel_to_its_package_installer(self):
        from eitr_store_backends import dispatch, THEMES
        backend = Mock()
        with (patch('eitr_paths.code_root', return_value=ROOT),
              patch('eitr_store_backends._THEME_BACKEND', backend),
              patch('eitr_store_backends.community') as community):
            for row in starter.load(ROOT / 'distro/starter-themes.json'):
                args = dict(kind=row['kind'], channel=row['channel'], ids=[row['id']])
                dispatch('install', args)
                if row['channel'] == 'official':
                    backend.install.assert_called_with(THEMES, args['ids'])
                else:
                    community.assert_called_with('install', args)
            self.assertEqual(backend.install.call_count, 2)
            self.assertEqual(community.call_count, 3)
