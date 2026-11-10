"""Display resolution and isolated persistence, including temporary preview rollback."""
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
        for name in ('default', 'global', 'monitor', 'other', 'preview'):
            image = self.root / (name + '.png')
            image.touch()
            self.images.append(str(image))
        self.monitor = {'name': 'DP-1', 'focused': True}
        self.monitor_key = 'DP-1'
        choices.set_per_display(True)

    def test_toggle_ignores_but_retains_assignments(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        self.assertEqual(choices.resolve(self.monitor, self.images[0], temporary={}), self.images[2])
        choices.set_per_display(False)
        self.assertEqual(choices.resolve(self.monitor, self.images[0], temporary={}), self.images[0])
        self.assertEqual(choices.prune(), {'DP-1': self.images[2]})
        choices.set_per_display(True)
        self.assertEqual(choices.resolve(self.monitor, self.images[0], temporary={}), self.images[2])
        self.assertEqual(choices.resolve({'name': 'DP-2'}, self.images[0], temporary={}), self.images[0])

    def test_default_off_and_legacy_migration(self):
        from eitr_paths import write_settings
        choices.settings().unlink()
        write_settings(choices.settings(), {'assignments': {
            '["DP-1", 0]': self.images[2], '["DP-1", 2]': self.images[3], 'global': self.images[1]}})
        self.assertFalse(choices.per_display())
        self.assertEqual(choices.prune(), {'DP-1': self.images[2]})
        self.assertEqual(json.loads(choices.settings().read_text()),
                         {'perDisplay': False, 'assignments': {'DP-1': self.images[2]}, 'version': 1})

    def test_target_uses_focus_at_action_time_and_refuses_missing_focus(self):
        with patch.object(choices, 'query', return_value=[{'name': 'DP-2'}, self.monitor]):
            self.assertEqual(choices.target(), 'DP-1')
            self.assertEqual(choices.summary()['monitor'], 'DP-1')
        with patch.object(choices, 'query', return_value=[]):
            with self.assertRaises(ValueError):
                choices.target()
            choices.set_per_display(False)
            self.assertEqual(choices.target(), '')

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

    def test_reconcile_changes_only_assigned_output_and_toggle_restores_global(self):
        choices.change('apply', 'DP-1', self.images[3], 'owner')
        monitors = [self.monitor, {'name': 'DP-2'}]
        adapter = {'for_monitor': lambda path, monitor: path,
                   'active_wallpapers': lambda: {'DP-1': self.images[0], 'DP-2': self.images[0]}}
        with patch.object(choices, 'query', return_value=monitors), patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0])
            self.assertEqual(command.call_count, 1)
            self.assertIn('DP-1,' + self.images[3], command.call_args.args[0])
        choices.set_per_display(False)
        adapter['active_wallpapers'] = lambda: {'DP-1': self.images[3], 'DP-2': self.images[0]}
        with patch.object(choices, 'query', return_value=monitors), patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0])
            self.assertEqual(command.call_count, 1)
            self.assertIn('DP-1,' + self.images[0], command.call_args.args[0])

    def test_theme_switch_leaves_outputs_to_its_transition(self):
        from eitr_paths import config, write_settings
        # The theme swap removed the saved file: the bar only reports, it does not redraw.
        write_settings(config('eitr/appearance.json'), {'wallpaper': str(self.root / 'replaced.png')})
        self.assertFalse(choices.saved_global_available())
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {'DP-1': self.images[1]}}
        with patch.object(choices, 'query', return_value=[self.monitor]), patch.object(choices.subprocess, 'run') as command:
            selected, _, _ = choices.reconcile(adapter, self.images[0], write=choices.saved_global_available())
            command.assert_not_called()
        self.assertEqual(selected['DP-1'], self.images[0])
        write_settings(config('eitr/appearance.json'), {'wallpaper': self.images[1]})
        self.assertTrue(choices.saved_global_available())

    def test_global_preview_overrides_every_output_without_changing_assignments(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        choices.set_per_display(False)
        choices.change('preview', '', self.images[4], 'owner')
        for monitor in (self.monitor, {'name': 'DP-2'}):
            self.assertEqual(choices.resolve(monitor, self.images[0]), self.images[4])
        choices.change('cancel', '', '', 'owner')
        self.assertEqual(choices.prune(), {'DP-1': self.images[2]})
        self.assertEqual(choices.resolve(self.monitor, self.images[0]), self.images[0])

    def test_previewing_matches_only_the_owners_global_preview_of_that_picture(self):
        choices.set_per_display(False)
        choices.change('preview', '', self.images[4], 'owner')
        self.assertTrue(choices.previewing('owner', self.images[4]))
        self.assertFalse(choices.previewing('other-owner', self.images[4]))
        self.assertFalse(choices.previewing('owner', self.images[3]))
        choices.set_per_display(True)
        choices.change('preview', 'DP-1', self.images[4], 'owner')
        self.assertFalse(choices.previewing('owner', self.images[4]))

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

    def test_applying_preview_saves_and_theme_clear_keeps_preference(self):
        choices.change('preview', self.monitor_key, self.images[4], 'owner')
        choices.change('apply', self.monitor_key, self.images[4], 'owner')
        self.assertFalse(choices.preview())
        self.assertEqual(choices.resolve(self.monitor, self.images[1]), self.images[4])
        choices.clear_assignments()
        self.assertEqual(choices.resolve(self.monitor, self.images[1]), self.images[1])
        self.assertTrue(choices.per_display())

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

    def test_hyprpaper_error_reply_with_zero_exit_uses_fallback(self):
        import subprocess
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {'DP-1': self.images[0]}}
        choices.change('apply', self.monitor_key, self.images[2], 'owner')
        with patch.object(choices, 'query', return_value=[self.monitor]), \
                patch.object(choices.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'error: failed to load image')):
            _, _, failures = choices.reconcile(adapter, self.images[0])
        self.assertEqual(failures, ['DP-1'])

    def run_picker(self, *arguments, catalog=None):
        import contextlib
        import importlib.util
        import io
        import sys
        import types
        from unittest.mock import Mock
        transition = types.ModuleType('transition')
        transition.apply = Mock()
        transition.wallpapers = Mock(return_value=catalog or [])
        script = Path(__file__).resolve().parents[1] / 'scripts/actions/wallpaper/assignments.py'
        specification = importlib.util.spec_from_file_location('wallpaper_picker', script)
        picker = importlib.util.module_from_spec(specification)
        with patch.dict(sys.modules, {'transition': transition}):
            specification.loader.exec_module(picker)
        with patch.object(sys, 'argv', [str(script), *arguments]), \
                patch.object(choices, 'query', return_value=[self.monitor, {'name': 'DP-2'}]), \
                patch.object(choices, 'reconcile', return_value=({}, {}, [])) as reconcile, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            picker.main()
        return transition.apply, reconcile, output.getvalue()

    def test_picker_routes_global_apply_through_transition_and_keeps_picks(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        choices.set_per_display(False)
        apply, _, _ = self.run_picker('apply', '--path', self.images[1])
        apply.assert_called_once_with(self.images[1])
        self.assertEqual(choices.prune(), {'DP-1': self.images[2]})
        self.assertFalse(choices.per_display())

    def test_picker_apply_and_preview_use_focused_display_only(self):
        apply, reconcile, output = self.run_picker('apply', '--path', self.images[2])
        apply.assert_not_called()
        reconcile.assert_called_once()
        self.assertEqual(reconcile.call_args.kwargs, {'output': 'DP-1'})
        self.assertEqual(json.loads(output), {'monitor': 'DP-1', 'perDisplay': True,
                                             'assignments': [{'monitor': 'DP-1', 'path': self.images[2]}]})
        self.run_picker('preview', '--path', self.images[4], '--owner', 'picker')
        self.assertEqual(choices.resolve(self.monitor, self.images[0]), self.images[4])
        self.assertEqual(choices.resolve({'name': 'DP-2'}, self.images[0]), self.images[0])

    def test_picker_toggle_reconciles_and_theme_clear_keeps_switch(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        _, reconcile, _ = self.run_picker('per-display', 'off')
        reconcile.assert_called_once()
        self.assertFalse(choices.per_display())
        self.assertIn('DP-1', choices.prune())
        self.run_picker('per-display', 'on')
        self.run_picker('clear')
        self.assertEqual(choices.prune(), {})
        self.assertTrue(choices.per_display())

    def test_targeted_reconcile_leaves_other_outputs_untouched(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        choices.change('apply', 'DP-2', self.images[3], 'owner')
        adapter = {'for_monitor': lambda path, monitor: path, 'active_wallpapers': lambda: {}}
        with patch.object(choices.subprocess, 'run') as command:
            choices.reconcile(adapter, self.images[0], [self.monitor, {'name': 'DP-2'}], output='DP-1')
        self.assertEqual(command.call_count, 1)
        self.assertIn('DP-1,' + self.images[2], command.call_args.args[0])

    def test_motion_follows_display_resolution_and_preview_suppresses_only_its_target(self):
        import runpy
        rendering_path = Path(__file__).resolve().parents[2] / 'quickshell/desktop-bar/scripts/rendering.py'
        rendering = runpy.run_path(str(rendering_path))
        import eitr_paths
        adapter = {'wallpapers': lambda directory: [], 'for_monitor': lambda path, monitor: path,
                   'active_wallpapers': lambda: {'DP-1': self.images[2], 'DP-2': self.images[0]}}
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        from eitr_paths import write_settings, config
        write_settings(config('eitr/appearance.json'), {'wallpaper': self.images[0]})
        with patch.object(runpy, 'run_path', return_value=adapter), \
                patch.object(choices, 'query', return_value=[self.monitor, {'name': 'DP-2'}]), \
                patch.object(eitr_paths, 'code', return_value=Path('/unused')), \
                patch.dict(rendering['saved_wallpaper_status'].__globals__,
                           {'motion_folder': lambda path: 'motion:' + path}):
            result = rendering['saved_wallpaper_status']()
            self.assertEqual(result['motions'], {'DP-1': 'motion:' + self.images[2], 'DP-2': 'motion:' + self.images[0]})
            choices.change('preview', 'DP-1', self.images[4], 'owner')
            with patch.object(choices.subprocess, 'run'):
                result = rendering['saved_wallpaper_status']()
            self.assertEqual(result['motions'], {'DP-1': '', 'DP-2': 'motion:' + self.images[0]})
            choices.set_per_display(False)
            with patch.object(choices.subprocess, 'run'):
                result = rendering['saved_wallpaper_status']()
            self.assertEqual(result['motions'], {'DP-1': 'motion:' + self.images[0], 'DP-2': 'motion:' + self.images[0]})

    def test_next_and_menu_current_use_saved_display_pick_and_theme_alias(self):
        choices.change('apply', 'DP-1', self.images[2], 'owner')
        choices.change('preview', 'DP-1', self.images[4], 'owner')
        candidate = self.root / 'current/backgrounds/picture.png'
        with patch.object(choices, 'canonical', return_value=self.images[2]):
            _, _, output = self.run_picker('current', catalog=[candidate])
        self.assertEqual(output.strip(), str(candidate))
        self.assertEqual(choices.preview()['path'], self.images[4])
