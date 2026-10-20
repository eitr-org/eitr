import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
import eitr_assistants as assistants


class AssistantTests(unittest.TestCase):
    def test_launchers_are_never_discovered_as_installed_tools(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)), \
                patch.dict(os.environ, PATH=str(assistants.code('walker/assistants'))):
            for identifier in assistants.assistants():
                self.assertIsNone(assistants.executable(identifier))

    def test_real_binary_wins_and_arguments_are_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / 'codex'
            binary.write_text('#!/bin/sh\nexit 0\n')
            binary.chmod(0o755)
            with patch.object(Path, 'home', return_value=Path(directory)), \
                    patch.dict(os.environ, PATH=str(binary.parent)), \
                    patch.object(assistants.os, 'execve') as execute:
                self.assertEqual(assistants.launch('codex', ['a b', '--help']), 0)
                self.assertEqual(execute.call_args.args[1], [str(binary), 'a b', '--help'])

    def test_noninteractive_never_installs(self):
        with patch.object(assistants, 'executable', return_value=None), \
                patch.object(assistants.sys.stdin, 'isatty', return_value=False), \
                patch.object(assistants.subprocess, 'run') as run, contextlib.redirect_stderr(io.StringIO()) as output:
            self.assertEqual(assistants.launch('copilot', []), 1)
            run.assert_not_called()
            self.assertIn('Install > AI CLIs', output.getvalue())

    def test_enter_cancels_and_yes_uses_shared_recipe(self):
        for answer in ('', 'yes'):
            with self.subTest(answer=answer), patch.object(assistants, 'executable', return_value=None), \
                    patch.object(assistants.sys.stdin, 'isatty', return_value=True), \
                    patch.object(assistants.sys.stdout, 'isatty', return_value=True), \
                    patch('builtins.input', return_value=answer), \
                    patch.object(assistants.subprocess, 'run') as run, contextlib.redirect_stderr(io.StringIO()):
                run.return_value.returncode = 7
                self.assertEqual(assistants.launch('copilot', []), 7 if answer else 1)
                if answer:
                    self.assertEqual(run.call_args.args[0][-3:], ['recipe', 'ai', 'copilot'])
                else:
                    run.assert_not_called()

    def test_default_is_local_and_only_installed_assistants_can_be_selected(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)), \
                patch.object(assistants, 'executable', return_value=Path('/usr/bin/codex')):
            self.assertEqual(assistants.default_assistant(), '')
            assistants.set_default('codex')
            self.assertEqual(assistants.default_assistant(), 'codex')
            with patch.object(assistants, 'executable', return_value=None):
                self.assertEqual(assistants.default_assistant(), '')
                with self.assertRaises(ValueError):
                    assistants.set_default('codex')

    def test_shortcut_chooses_or_opens_without_permission_bypass_flags(self):
        with patch.object(assistants, 'default_assistant', return_value=''), \
                patch.object(assistants.subprocess, 'run') as run:
            assistants.open_default()
            self.assertEqual(run.call_args.args[0][-1], 'menus:ai-default')
        with patch.object(assistants, 'default_assistant', return_value='codex'), \
                patch.object(assistants.subprocess, 'Popen') as launch:
            assistants.open_default(['Explain this crash'])
            self.assertEqual(launch.call_args.args[0][-3:], ['run', 'codex', 'Explain this crash'])

    def test_theme_changes_only_the_requested_value(self):
        original = '{\r\n "ui" : {"theme": "old", "value": 1e3}, "token":"\\u0061", "other":true\r\n}\r\n'
        updated = assistants.replace_json_setting(original, ['ui', 'theme'], 'Default Light')
        self.assertEqual(updated, original.replace('"old"', '"Default Light"'))
        self.assertEqual(assistants.replace_json_setting('{ "other": 1 }', ['ui', 'theme'], 'Default'),
                         '{ "other": 1 ,"ui":{"theme": "Default"}}')
        for broken in ('{', '[]', '{"ui": null}', '{"theme": 1, "theme": 2}'):
            with self.assertRaises((ValueError, IndexError)):
                assistants.replace_json_setting(broken, ['ui', 'theme'], 'Default')

    def test_theme_sync_skips_broken_missing_and_uninstalled_configs(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(Path, 'home', return_value=Path(directory)), \
                patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(Path(directory) / '.claude')}), \
                patch.object(assistants, 'executable', return_value=Path('/bin/tool')):
            claude = Path(directory) / '.claude.json'
            claude.write_bytes(b'{ "theme" : "dark", "key":"secret", "model":"user-choice" }\r\n')
            gemini = Path(directory) / '.gemini/settings.json'
            gemini.parent.mkdir()
            gemini.write_text('{broken')
            assistants.sync_themes(True)
            self.assertEqual(claude.read_bytes(), b'{ "theme" : "light", "key":"secret", "model":"user-choice" }\r\n')
            self.assertEqual(gemini.read_text(), '{broken')
            self.assertFalse((Path(directory) / '.claude').exists())
            with patch.object(assistants, 'executable', return_value=None):
                assistants.sync_themes(False)
            self.assertIn(b'"light"', claude.read_bytes())

    def test_grok_theme_preserves_every_other_byte(self):
        for original in ('[ui]\r\ntheme = "auto" # preference\r\ncompact_mode = true\r\n[models]\r\ndefault = "my-model"\r\n',
                         'ui = { theme = "auto", compact_mode = true }\n',
                         'ui.theme = "auto"\nother = "secret"\n'):
            changed = assistants.replace_toml_theme(original, 'light')
            self.assertEqual(changed, original.replace('"auto"', '"light"'))
        for without in ('[ui]\ncompact_mode = true\n', 'model = "mine"\n'):
            with self.assertRaises(ValueError, msg='a theme the user never set is not added'):
                assistants.replace_toml_theme(without, 'dark')
        with self.assertRaises(ValueError):
            assistants.replace_toml_theme('[ui\nbroken', 'light')


class PackagedLayoutTests(unittest.TestCase):
    def test_recipes_are_found_where_the_package_installs_them(self):
        repository = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'software.json').write_text((repository / 'distro/software.json').read_text())
            with patch.object(assistants, 'code', side_effect=lambda relative: root / relative):
                self.assertIn('copilot', assistants.assistants())
