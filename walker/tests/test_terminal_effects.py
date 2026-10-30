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


spec = importlib.util.spec_from_file_location('terminal_choice', ROOT / 'walker/scripts/actions/style/terminal.py')
terminal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(terminal)


class TerminalChoiceTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.preference = self.home / 'eitr/terminal.json'
        for override in (patch.object(terminal, 'PREFERENCE', self.preference),
                         patch.object(terminal, 'config', side_effect=lambda relative: self.home / relative),
                         patch.dict(os.environ, EITR_NO_SESSION='1')):
            override.start()
            self.addCleanup(override.stop)

    def test_fresh_default_and_missing_ghostty_fallback(self):
        self.assertEqual(terminal.selected(), 'kitty')
        self.assertFalse(self.preference.exists())
        self.preference.parent.mkdir()
        self.preference.write_text('{"version":1,"terminal":"ghostty","cursor_fire":true}')
        with patch.object(terminal.shutil, 'which', return_value=None):
            self.assertEqual(terminal.launch(['-e', 'tmux']), ['kitty', '-e', 'tmux'])
        self.assertEqual(json.loads(self.preference.read_text())['terminal'], 'ghostty')

    def test_missing_choice_opens_installer_without_saving(self):
        with patch.object(terminal.shutil, 'which', return_value=None), \
                patch.object(terminal.subprocess, 'Popen') as opened:
            terminal.choose('ghostty')
        self.assertFalse(self.preference.exists())
        arguments = opened.call_args.args[0]
        self.assertIn('eitr-software', arguments)
        self.assertIn('install', arguments)
        self.assertTrue(any('task-terminal.py' in argument for argument in arguments))

    def test_install_cancel_and_failure_keep_choice(self):
        with patch('eitr_terminal.read_key', return_value='\x1b'), \
                patch.object(terminal.subprocess, 'run') as run:
            terminal.install()
        run.assert_not_called()
        with patch('eitr_terminal.read_key', return_value='\r'), \
                patch.object(terminal.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'install')):
            with self.assertRaises(subprocess.CalledProcessError):
                terminal.install()
        self.assertFalse(self.preference.exists())

    def test_successful_install_selects_only_after_command_completes(self):
        with patch('eitr_terminal.read_key', return_value='\r'), \
                patch.object(terminal.shutil, 'which', return_value='/usr/bin/ghostty'), \
                patch.object(terminal.subprocess, 'run') as run:
            terminal.install()
        self.assertEqual(run.call_args.args[0][-3:], ['recipe', 'tools', 'ghostty'])
        self.assertEqual(json.loads(self.preference.read_text())['terminal'], 'ghostty')

    def test_choose_preserves_cursor_fire_and_unknown_fields(self):
        self.preference.parent.mkdir()
        self.preference.write_text('{"version":1,"cursor_fire":true,"future":42}')
        with patch.object(terminal.shutil, 'which', return_value='/usr/bin/ghostty'):
            terminal.choose('ghostty')
        self.assertEqual(json.loads(self.preference.read_text()),
                         {'version': 1, 'cursor_fire': True, 'future': 42, 'terminal': 'ghostty'})

    def test_theme_generation_and_personal_override(self):
        theme = self.home / 'theme/current'
        theme.mkdir(parents=True)
        (theme / 'colors.toml').write_text((ROOT / 'themes/eitr/colors.toml').read_text())
        self.preference.parent.mkdir()
        (self.preference.parent / 'font.json').write_text('{"version":1,"family":"Example Font"}')
        personal = self.home / 'ghostty/local.conf'
        personal.parent.mkdir()
        personal.write_text('font-size = 14\n')
        terminal.sync()
        text = (self.home / 'ghostty/eitr.conf').read_text()
        self.assertIn('font-family = Example Font', text)
        self.assertIn('background-opacity = 0.75', text)
        self.assertIn('command = /usr/bin/zsh', text)
        self.assertEqual(sum(line.startswith('palette = ') for line in text.splitlines()), 16)
        self.assertEqual(text.splitlines()[-1], 'config-file = ?local.conf')
        self.assertEqual(personal.read_text(), 'font-size = 14\n')
        from palette import load
        colors = load(theme)
        self.assertIn('background = ' + colors['background'], text)
        self.assertIn('cursor-color = ' + colors.get('cursor', colors['foreground']), text)
        (theme / 'colors.toml').write_text((ROOT / 'themes/daylight/colors.toml').read_text())
        terminal.sync()
        self.assertNotEqual((self.home / 'ghostty/eitr.conf').read_text(), text)

    def test_launch_preserves_argv_and_directory(self):
        with patch.object(terminal, 'selected', return_value='ghostty'), patch.object(terminal, 'sync'):
            arguments = terminal.launch(['--directory', '/tmp/two words', '-e', 'zsh', '-ic', 'printf "$HOME"'])
        self.assertEqual(arguments, ['ghostty', '--config-file=' + str(self.home / 'ghostty/eitr.conf'),
                                     '--working-directory=/tmp/two words', '-e', 'zsh', '-ic', 'printf "$HOME"'])

    def test_launcher_executes_choice_and_keeps_utility_on_kitty(self):
        for name in ('kitty', 'ghostty'):
            executable = self.home / name
            executable.write_text('#!/usr/bin/python3\nimport json,sys\nprint(json.dumps(sys.argv))\n')
            executable.chmod(0o755)
        self.preference.parent.mkdir()
        self.preference.write_text('{"version":1,"terminal":"ghostty"}')
        environment = dict(os.environ, XDG_CONFIG_HOME=str(self.home),
                           PATH=str(self.home) + ':/usr/bin', EITR_CODE_ROOT=str(ROOT))
        for launcher, arguments, expected in (
                ('app-launch', ['--terminal', '-e', 'tmux', 'two words'], 'ghostty'),
                ('menu-path/kitty', [], 'ghostty'),
                ('menu-path/kitty', ['--class', 'eitr-plugins', '-e', 'setup'], 'kitty')):
            result = subprocess.run([str(ROOT / 'walker/bin' / launcher), *arguments], env=environment,
                                    capture_output=True, text=True, check=True)
            command = json.loads(result.stdout)
            self.assertEqual(Path(command[0]).name, expected)
            if expected == 'kitty':
                self.assertIn('eitr-plugins', command)
                self.assertIn('background_opacity=1', command)

    def test_unsupported_schema_stays_read_only(self):
        self.preference.parent.mkdir()
        self.preference.write_text('{"version":2}')
        with self.assertRaises(ValueError):
            terminal.choose('kitty')
        self.assertEqual(self.preference.read_text(), '{"version":2}')


if __name__ == '__main__':
    unittest.main()
