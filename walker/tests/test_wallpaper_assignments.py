"""Scope resolution and isolated persistence, including temporary preview rollback."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from home_isolation import setUpModule, tearDownModule  # noqa: F401
import eitr_wallpapers as choices


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        environment = patch.dict(os.environ, {
            'XDG_CONFIG_HOME': str(self.root / 'config'), 'XDG_CACHE_HOME': str(self.root / 'cache'),
            'XDG_STATE_HOME': str(self.root / 'state'), 'XDG_RUNTIME_DIR': str(self.root / 'run')})
        environment.start()
        self.addCleanup(environment.stop)
        self.images = []
        for name in ('default', 'global', 'monitor', 'workspace', 'preview'):
            image = self.root / (name + '.png')
            image.touch()
            self.images.append(str(image))
        self.monitor = {'name': 'DP-1', 'activeWorkspace': {'id': 12}}
        self.global_key = 'global'
        self.monitor_key = choices.key('monitor', 'DP-1')
        self.workspace_key = choices.key('workspace', 'DP-1', 2)

    def test_precedence_and_missing_files(self):
        default, global_image, monitor_image, workspace, _ = self.images
        data = {'global': global_image, self.monitor_key: monitor_image, self.workspace_key: workspace}
        self.assertEqual(choices.resolve(self.monitor, default, data, {}), workspace)
        Path(workspace).unlink()
        self.assertEqual(choices.resolve(self.monitor, default, data, {}), monitor_image)
        del data[self.monitor_key]
        self.assertEqual(choices.resolve(self.monitor, default, data, {}), global_image)
        self.assertEqual(choices.resolve(self.monitor, default, {}, {}), default)

    def test_persistence_pruning_and_disconnected_monitors(self):
        choices.change('apply', self.monitor_key, self.images[2], 'owner')
        self.assertEqual(choices.prune(), {self.monitor_key: self.images[2]})
        self.assertEqual(choices.images({'for_monitor': lambda path, monitor: path}, self.images[0], []), {'*': self.images[0]})
        self.assertIn(self.monitor_key, choices.prune(), 'disconnect retains an available assignment')
        Path(self.images[2]).unlink()
        self.assertEqual(choices.prune(), {})
        self.assertEqual(json.loads(choices.settings().read_text())['assignments'], {})

    def test_preview_cancel_restores_without_persisting_palette_or_global(self):
        choices.change('apply', self.monitor_key, self.images[2], 'owner')
        saved = choices.settings().read_bytes()
        choices.change('preview', self.monitor_key, self.images[4], 'owner')
        self.assertEqual(choices.resolve(self.monitor, self.images[0]), self.images[4])
        choices.change('cancel', 'global', '', 'other-picker')
        self.assertEqual(choices.resolve(self.monitor, self.images[0]), self.images[4])
        choices.change('cancel', 'global', '', 'owner')
        self.assertEqual(choices.resolve(self.monitor, self.images[0]), self.images[2])
        self.assertEqual(choices.settings().read_bytes(), saved)
        self.assertFalse((self.root / 'config/eitr/appearance.json').exists())

    def test_workspace_modes_use_plan_then_visible_number(self):
        from eitr_paths import write_settings, state
        write_settings(state('eitr/workspaces.json'), {'rows': [{'id': 12, 'monitor': 'DP-1', 'number': 7}]})
        self.assertEqual(choices.workspace_number(self.monitor), 7)
        self.assertEqual(choices.workspace_number({'name': 'DP-2', 'activeWorkspace': {'id': -1}}), 0)
        with patch.object(choices, 'preferences', return_value={'workspaceMode': 'split'}):
            self.assertEqual(choices.workspace_number({'name': 'DP-2', 'activeWorkspace': {'id': 8}}), 8)

    def test_reconcile_changes_only_latest_output_and_restores_removed_workspace(self):
        choices.change('apply', self.workspace_key, self.images[3], 'owner')
        monitors = [self.monitor, {'name': 'DP-2', 'activeWorkspace': {'id': 1}}]
        adapter = {'for_monitor': lambda path, monitor: path,
                   'active_wallpapers': lambda: {'DP-1': self.images[0], 'DP-2': self.images[0]}}
        with patch.object(choices, 'query', return_value=monitors), patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0])
            self.assertEqual(command.call_count, 1)
            self.assertIn('DP-1,' + self.images[3], command.call_args.args[0])
        monitors[0] = {'name': 'DP-1', 'activeWorkspace': {'id': 11}}
        adapter['active_wallpapers'] = lambda: {'DP-1': self.images[3], 'DP-2': self.images[0]}
        with patch.object(choices, 'query', return_value=monitors), patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0])
            self.assertEqual(command.call_count, 1)
            self.assertIn('DP-1,' + self.images[0], command.call_args.args[0])

    def test_theme_replacement_keeps_source_identity_and_prunes_removed_art(self):
        from eitr_paths import cache, config
        current = config('theme/current/backgrounds')
        current.mkdir(parents=True)
        image = current / 'shared-name.png'
        image.touch()
        source = self.root / 'themes/old'
        (source / 'backgrounds').mkdir(parents=True)
        original = source / 'backgrounds/shared-name.png'
        original.touch()
        cache().mkdir(parents=True, exist_ok=True)
        (cache() / 'current-theme').write_text('old')
        with patch.object(choices, 'theme_paths', return_value={'old': source}):
            choices.change('apply', self.monitor_key, str(image), 'owner')
        image.write_bytes(b'new theme with same filename')
        self.assertEqual(choices.prune()[self.monitor_key], str(original))
        original.unlink()
        self.assertEqual(choices.prune(), {})

    def test_applying_preview_saves_and_clear_restores_global(self):
        choices.change('preview', self.monitor_key, self.images[4], 'owner')
        choices.change('apply', self.monitor_key, self.images[4], 'owner')
        self.assertFalse(choices.preview())
        self.assertEqual(choices.resolve(self.monitor, self.images[1]), self.images[4])
        choices.change('clear', self.monitor_key, '', 'owner')
        self.assertEqual(choices.resolve(self.monitor, self.images[1]), self.images[1])

    def test_failed_output_remains_eligible_for_fallback_and_reconnect_retries(self):
        import subprocess
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {}}
        with patch.object(choices, 'query', return_value=[self.monitor]), \
                patch.object(choices.subprocess, 'run', side_effect=subprocess.TimeoutExpired('hyprctl', 3)):
            images, active, failed = choices.reconcile(adapter, self.images[0])
        self.assertEqual(failed, ['DP-1'])
        self.assertEqual(images['DP-1'], self.images[0])
        self.assertEqual(active, {})
        with patch.object(choices, 'query', return_value=[self.monitor]), patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0])
            self.assertEqual(command.call_count, 1)

    def test_latest_workspace_is_read_after_lock_not_from_an_event_payload(self):
        choices.change('apply', self.workspace_key, self.images[3], 'owner')
        latest = {'name': 'DP-1', 'activeWorkspace': {'id': 13}}
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {'DP-1': self.images[0]}}
        with patch.object(choices, 'query', return_value=[latest]) as query, patch.object(choices.subprocess, 'run') as command:
            images, _, _ = choices.reconcile(adapter, self.images[0])
            query.assert_called_once_with('monitors')
            command.assert_not_called()
            self.assertEqual(images['DP-1'], self.images[0])

    def test_hyprpaper_error_reply_with_zero_exit_uses_fallback(self):
        import subprocess
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {'DP-1': self.images[0]}}
        choices.change('apply', self.monitor_key, self.images[2], 'owner')
        with patch.object(choices, 'query', return_value=[self.monitor]), \
                patch.object(choices.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'error: failed to load image')):
            _, _, failures = choices.reconcile(adapter, self.images[0])
        self.assertEqual(failures, ['DP-1'])
