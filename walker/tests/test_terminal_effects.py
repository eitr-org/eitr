import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('terminal_effects', ROOT / 'walker/scripts/actions/style/terminal-effects.py')
effects = importlib.util.module_from_spec(spec)
spec.loader.exec_module(effects)


class TerminalEffectsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.preference = self.root / 'eitr/terminal.json'
        self.output = self.root / 'kitty/cursor-fire.conf'
        self.loader = self.root / 'kitty/kitty.conf'
        self.loader.parent.mkdir(parents=True)
        self.original = 'include /usr/share/eitr/kitty/kitty.conf\nglobinclude local.conf\n'
        self.loader.write_text(self.original)
        for name, value in [('PREFERENCE', self.preference), ('OUTPUT', self.output), ('LOADER', self.loader)]:
            override = patch.object(effects, name, value)
            override.start()
            self.addCleanup(override.stop)
        environment = patch.dict(os.environ, {'EITR_NO_SESSION': '1'})
        environment.start()
        self.addCleanup(environment.stop)

    def test_default_is_off_without_creating_preferences(self):
        self.assertFalse(effects.read()['cursor_fire'])
        self.assertFalse(self.preference.exists())

    def test_enable_disable_preserves_personal_options_and_unknown_settings(self):
        self.preference.parent.mkdir()
        self.preference.write_text('{"version":1,"future_option":"kept"}')
        personal = self.loader.parent / 'local.conf'
        personal.write_text('font_size 14\ncustom_shaders my-shader\n')
        pipeline = 'cursor-trail-blaze'
        with patch.object(effects, 'check_support', return_value=pipeline):
            effects.set_enabled(True)
            effects.set_enabled(True)
        self.assertIn('custom_shaders "cursor-trail-blaze"', self.output.read_text())
        self.assertIn('cursor_trail_start_threshold 1', self.output.read_text())
        self.assertEqual(self.loader.read_text().count(effects.INCLUDE), 1)
        self.assertTrue(self.loader.read_text().startswith(self.original))
        self.assertEqual(personal.read_text(), 'font_size 14\ncustom_shaders my-shader\n')
        effects.set_enabled(False)
        self.assertNotIn('custom_shaders', self.output.read_text())
        saved = json.loads(self.preference.read_text())
        self.assertEqual(saved, {'version': 1, 'cursor_fire': False, 'future_option': 'kept'})

    def test_unsupported_settings_fail_read_only(self):
        self.preference.parent.mkdir()
        for content in ['{"version":2,"cursor_fire":true}', '{"cursor_fire":"on"}']:
            self.preference.write_text(content)
            with self.assertRaises(ValueError):
                effects.set_enabled(False)
            self.assertEqual(self.preference.read_text(), content)
            self.assertEqual(self.loader.read_text(), self.original)
            self.assertFalse(self.output.exists())

    def test_missing_compiler_fails_before_writing_or_reloading(self):
        with patch.object(effects.shutil, 'which', return_value=None), patch.object(effects.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'shader-slang'):
                effects.set_enabled(True)
            run.assert_not_called()
        self.assertFalse(self.preference.exists())
        self.assertFalse(self.output.exists())
        self.assertEqual(self.loader.read_text(), self.original)

    def test_failed_shader_compile_keeps_existing_configuration(self):
        result = subprocess.CompletedProcess([], 0, 'kitty 0.49.2')
        with patch.object(effects.shutil, 'which', return_value='/usr/bin/slangc'), \
                patch.object(effects.subprocess, 'run', side_effect=[result, subprocess.CalledProcessError(1, 'kitty')]):
            with self.assertRaises(subprocess.CalledProcessError):
                effects.set_enabled(True)
        self.assertFalse(self.preference.exists())
        self.assertFalse(self.output.exists())

    def test_only_documented_config_reload_is_sent(self):
        with patch.dict(os.environ, {'EITR_NO_SESSION': '0'}), patch.object(effects.subprocess, 'run') as run:
            effects.set_enabled(False)
        self.assertEqual(run.call_args.args[0], ['pkill', '-USR1', '-u', str(os.getuid()), '-x', 'kitty'])

    def test_live_sync_uses_saved_preference(self):
        effects.set_enabled(False)
        self.assertFalse(effects.read()['cursor_fire'])
        self.assertIn('disabled', self.output.read_text())


if __name__ == '__main__':
    unittest.main()
