import json
import contextlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch
import urllib.error
import urllib.request

from home_isolation import setUpModule, tearDownModule
import eitr_assistants as assistants
import eitr_local_assistant as local


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
            claude = Path(directory) / '.claude/settings.json'
            claude.parent.mkdir()
            claude.write_bytes(b'{ "theme" : "dark", "key":"secret", "model":"user-choice" }\r\n')
            gemini = Path(directory) / '.gemini/settings.json'
            gemini.parent.mkdir()
            gemini.write_text('{broken')
            assistants.sync_themes(True)
            self.assertEqual(claude.read_bytes(), b'{ "theme" : "light", "key":"secret", "model":"user-choice" }\r\n')
            self.assertEqual(gemini.read_text(), '{broken')
            with patch.object(assistants, 'executable', return_value=None):
                assistants.sync_themes(False)
            self.assertIn(b'"light"', claude.read_bytes())
            for kept in (b'{"theme": "auto"}', b'{"model": "mine"}'):
                claude.write_bytes(kept)
                assistants.sync_themes(False)
                self.assertEqual(claude.read_bytes(), kept, 'auto or no theme is the user\'s choice')

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


class AntigravityTests(unittest.TestCase):
    def test_installed_agy_preserves_arguments(self):
        with tempfile.TemporaryDirectory() as temporary:
            binary = Path(temporary) / 'agy'
            binary.write_text('#!/bin/sh\nexit 0\n')
            binary.chmod(0o755)
            with patch.object(Path, 'home', return_value=Path(temporary)), \
                    patch.dict(os.environ, PATH=temporary), \
                    patch.object(assistants.os, 'execve') as execute:
                self.assertEqual(assistants.launch('agy', ['--help']), 0)
                self.assertEqual(execute.call_args.args[1], [str(binary), '--help'])

    def test_install_uses_googles_official_installer(self):
        repository = Path(__file__).resolve().parents[2]
        installers = json.loads((repository / 'distro/installers.json').read_text())
        self.assertEqual(installers['agy'], 'https://antigravity.google/cli/install.sh')
        script = (repository / 'walker/scripts/actions/install/development.sh').read_text()
        self.assertIn('agy) download_run "$(installer_url agy)" ;;', script)
        self.assertIn("--proto '=https'", script)


class LocalAssistantTests(unittest.TestCase):
    """The offline default assistant, with Ollama, systemctl and the network mocked."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        folders = {name: str(self.root / name.lower()) for name in
                   ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME')}
        for patcher in (patch.dict(os.environ, folders), patch.object(Path, 'home', return_value=self.root)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.binary = self.root / 'bin/ollama'

    def add_model(self, missing_blob=False):
        folder = local.models()
        digests = ['sha256:' + character * 64 for character in 'abc']
        manifest = folder / local.MANIFEST
        manifest.parent.mkdir(parents=True)
        manifest.write_text(json.dumps({'schemaVersion': 2, 'config': {'digest': digests[0]},
                                        'layers': [{'digest': digest} for digest in digests[1:]]}))
        (folder / 'blobs').mkdir()
        for digest in digests[:-1] if missing_blob else digests:
            (folder / 'blobs' / digest.replace(':', '-')).write_bytes(b'x')

    def add_unit(self):
        local.unit_path().parent.mkdir(parents=True, exist_ok=True)
        local.unit_path().write_text(local.unit_content(self.binary, local.models()))

    def test_installed_needs_binary_unit_and_complete_model(self):
        with patch.object(local, 'binary', return_value=self.binary):
            self.assertFalse(local.installed())
            self.assertFalse(local.present())
            self.add_model(missing_blob=True)
            self.add_unit()
            self.assertFalse(local.installed(), 'a partial download is not a model')
            self.assertTrue(local.present())
            shutil.rmtree(local.models())
            self.add_model()
            self.assertTrue(local.installed())
            (local.models() / local.MANIFEST).write_text('{broken')
            self.assertFalse(local.installed())
            shutil.rmtree(local.models())
            self.add_model()
            local.unit_path().unlink()
            self.assertFalse(local.installed())
            self.add_unit()
        with patch.object(local, 'binary', return_value=None):
            self.assertFalse(local.installed())

    def test_unit_is_per_user_bound_to_loopback_with_private_models(self):
        content = local.unit_content(self.binary, local.models())
        self.assertIn('ExecStart="' + str(self.binary) + '" serve', content)
        self.assertIn('Environment="OLLAMA_HOST=127.0.0.1:11434"', content)
        self.assertIn('Environment="OLLAMA_MODELS=' + str(self.root / 'xdg_data_home/eitr/ollama') + '"', content)
        self.assertEqual(local.unit_path(), self.root / 'xdg_config_home/systemd/user/eitr-ollama.service')
        self.assertNotIn('[Install]', content, 'started on demand, never at every login')

    def fake_server(self, answer=None, error=None):
        sent = []

        class Response(io.BytesIO):
            status = 200

        def open_request(request, timeout):
            sent.append((request, timeout))
            if error:
                raise error
            return Response(json.dumps(answer).encode())
        return Mock(open=open_request), sent

    def test_request_names_the_model_json_format_and_loopback_host(self):
        server, sent = self.fake_server({'response': '{"action": "list"}'})
        with patch.object(local, 'installed', return_value=True), \
                patch.object(local, 'ensure_running') as running, \
                patch.object(local, 'opener', return_value=server):
            self.assertEqual(local.ask('Remind me', response_format='json'), '{"action": "list"}')
            running.assert_called_once()
            request, timeout = sent[-1]
            self.assertEqual(request.full_url, 'http://127.0.0.1:11434/api/generate')
            self.assertEqual(request.get_method(), 'POST')
            body = json.loads(request.data)
            # Qwen3 would otherwise reason aloud before answering.
            self.assertIs(body['think'], False)
            self.assertEqual((body['model'], body['format'], body['stream'], body['prompt']),
                             ('qwen3:4b', 'json', False, 'Remind me'))
            self.assertEqual(timeout, local.TIMEOUT)
            local.ask('Hello')
            self.assertNotIn('format', json.loads(sent[-1][0].data))

    def test_proxies_from_the_environment_are_ignored(self):
        with patch.dict(os.environ, http_proxy='http://proxy.invalid:8080'):
            handlers = [handler for handler in local.opener().handlers
                        if isinstance(handler, urllib.request.ProxyHandler)]
        self.assertEqual(handlers, [], 'the default handler would read http_proxy')

    def test_timeouts_and_errors_are_readable(self):
        cases = [(TimeoutError('timed out'), 'timed out'),
                 (urllib.error.URLError(TimeoutError('timed out')), 'timed out'),
                 (urllib.error.URLError(ConnectionRefusedError()), 'unavailable'),
                 (urllib.error.HTTPError('http://127.0.0.1:11434/api/generate', 404, 'Not Found', {},
                                         io.BytesIO(b'{"error": "model not found"}')), 'model not found')]
        for error, expected in cases:
            server, _ = self.fake_server(error=error)
            with self.subTest(error=error), patch.object(local, 'installed', return_value=True), \
                    patch.object(local, 'ensure_running'), patch.object(local, 'opener', return_value=server):
                with self.assertRaisesRegex(ValueError, expected):
                    local.ask('Hello')
        for answer in ({'response': '  '}, ['not', 'an', 'object']):
            server, _ = self.fake_server(answer)
            with self.subTest(answer=answer), patch.object(local, 'installed', return_value=True), \
                    patch.object(local, 'ensure_running'), patch.object(local, 'opener', return_value=server):
                with self.assertRaisesRegex(ValueError, 'no answer'):
                    local.ask('Hello')
        with patch.object(local, 'installed', return_value=False), patch.object(local, 'opener') as opener:
            with self.assertRaisesRegex(ValueError, 'not set up'):
                local.ask('Hello')
            opener.assert_not_called()

    def test_service_starts_on_demand_and_a_foreign_server_is_refused(self):
        self.add_unit()
        calls = []

        def systemctl(*arguments):
            calls.append(arguments)
            return subprocess.CompletedProcess(arguments, 3 if arguments[0] == 'is-active' else 0)
        with patch.object(local, 'systemctl', side_effect=systemctl), \
                patch.object(local, 'responding', side_effect=[False, False, True]), \
                patch.object(local.time, 'sleep'):
            local.ensure_running()
        self.assertIn(('start', 'eitr-ollama.service'), calls)
        with patch.object(local, 'systemctl', side_effect=systemctl), \
                patch.object(local, 'responding', return_value=True):
            with self.assertRaisesRegex(ValueError, 'Another Ollama server'):
                local.ensure_running()
        with patch.object(local, 'systemctl', side_effect=systemctl), \
                patch.object(local, 'responding', return_value=False), \
                patch.object(local.time, 'monotonic', side_effect=[0, 0, 100]), \
                patch.object(local.time, 'sleep'):
            with self.assertRaisesRegex(ValueError, 'did not start'):
                local.ensure_running()

    def test_setup_refused_without_confirmation_changes_nothing(self):
        from eitr_forms import Terminal
        for answer in ('', 'n', 'no', 'later'):
            with self.subTest(answer=answer), patch('builtins.input', return_value=answer), \
                    patch.object(local.subprocess, 'run') as run, \
                    patch.object(local, 'binary', return_value=None), \
                    contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(local.setup(lambda question: Terminal().confirm(question, default=False)), 0)
                run.assert_not_called()
                for explained in ('about 15 MB', 'about 2.5 GB', 'only on this PC', 'less reliable', 'remove it later'):
                    self.assertIn(explained, output.getvalue())
                self.assertIn('Nothing changed.', output.getvalue())
        self.assertFalse(local.present())
        self.assertEqual(assistants.default_assistant(), '')

    def test_setup_installs_starts_pulls_and_sets_the_default(self):
        commands = []

        def run(command, **options):
            commands.append(command)
            if command[-3:] == ['recipe', 'tools', 'ollama']:
                self.binary.parent.mkdir(parents=True, exist_ok=True)
                self.binary.write_text('#!/bin/sh\n')
                self.binary.chmod(0o755)
            if command[1:] == ['pull', 'qwen3:4b']:
                self.assertEqual(options['env']['OLLAMA_HOST'], '127.0.0.1:11434')
                self.add_model()
            return subprocess.CompletedProcess(command, 0)
        with patch.dict(os.environ, PATH=str(self.binary.parent)), \
                patch.object(local.subprocess, 'run', side_effect=run), \
                patch.object(local, 'ensure_running'), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(local.setup(lambda question: True), 0)
            self.assertEqual(assistants.default_assistant(), 'local')
        self.assertEqual(commands[0][-3:], ['recipe', 'tools', 'ollama'])
        self.assertEqual(commands[1], ['systemctl', '--user', 'daemon-reload'])
        self.assertEqual(commands[2], [str(self.binary), 'pull', 'qwen3:4b'])
        self.assertTrue(local.unit_path().is_file())
        self.assertTrue(json.loads(local.record_path().read_text())['installed_package'])

    def test_failed_setup_keeps_the_previous_default(self):
        from eitr_paths import config, write_settings
        write_settings(config('eitr/ai.json'), {'assistant': 'codex'})
        for failing in ('recipe', 'pull'):
            def run(command, **options):
                return subprocess.CompletedProcess(command, 1 if failing in command else 0)
            with self.subTest(failing=failing), \
                    patch.object(local, 'binary', return_value=None if failing == 'recipe' else self.binary), \
                    patch.object(local.subprocess, 'run', side_effect=run), patch.object(local, 'ensure_running'), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as errors:
                self.assertNotEqual(local.setup(lambda question: True), 0)
                self.assertIn('unchanged', errors.getvalue())
            self.assertEqual(json.loads(config('eitr/ai.json').read_text())['assistant'], 'codex')

    def test_removal_asks_first_then_cleans_up_and_resets_a_local_default(self):
        from eitr_paths import config, write_settings
        self.add_unit()
        self.add_model()
        write_settings(config('eitr/ai.json'), {'assistant': 'local'})
        write_settings(local.record_path(), {'installed_package': True})
        with patch.object(local.subprocess, 'run') as run, patch.object(local, 'binary', return_value=self.binary), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(local.remove(lambda question: False), 0)
            run.assert_not_called()
        self.assertTrue(local.unit_path().exists() and local.models().exists())
        with patch.object(local.subprocess, 'run') as run, patch.object(local, 'binary', return_value=self.binary), \
                contextlib.redirect_stdout(io.StringIO()) as output:
            run.return_value = subprocess.CompletedProcess([], 0)
            self.assertEqual(local.remove(lambda question: True), 0)
        commands = [call.args[0] for call in run.call_args_list]
        self.assertEqual(commands[:2], [['systemctl', '--user', 'disable', '--now', 'eitr-ollama.service'],
                                        ['systemctl', '--user', 'daemon-reload']])
        self.assertEqual(commands[-1][-3:], ['recipe-remove', 'tools', 'ollama'])
        self.assertIn('removed', output.getvalue())
        self.assertFalse(local.present())
        self.assertEqual(json.loads(config('eitr/ai.json').read_text())['assistant'], '')

    def test_removal_keeps_a_package_setup_did_not_install_and_other_defaults(self):
        from eitr_paths import config, write_settings
        self.add_unit()
        write_settings(config('eitr/ai.json'), {'assistant': 'codex'})
        with patch.object(local.subprocess, 'run') as run, patch.object(local, 'binary', return_value=self.binary), \
                contextlib.redirect_stdout(io.StringIO()):
            run.return_value = subprocess.CompletedProcess([], 0)
            self.assertEqual(local.remove(lambda question: True), 0)
        self.assertFalse(any('recipe-remove' in call.args[0] for call in run.call_args_list))
        self.assertEqual(json.loads(config('eitr/ai.json').read_text())['assistant'], 'codex')

    def test_default_and_shortcut_run_the_model_against_the_user_service(self):
        with patch.object(local, 'installed', return_value=True):
            assistants.set_default('local')
            self.assertEqual(assistants.default_assistant(), 'local')
        with patch.object(local, 'installed', return_value=False):
            self.assertEqual(assistants.default_assistant(), '')
            with self.assertRaises(ValueError):
                assistants.set_default('local')
        with patch.object(local, 'installed', return_value=True), patch.object(local, 'binary', return_value=self.binary), \
                patch.object(local, 'ensure_running'), patch.object(local.subprocess, 'run') as run, \
                patch.object(local.os, 'execve') as execute, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(assistants.launch('local', ['Explain this crash']), 0)
        self.assertEqual(run.call_args.args[0], [str(self.binary), 'run', 'qwen3:4b', '--', 'Explain this crash'])
        self.assertEqual(execute.call_args.args[1], [str(self.binary), 'run', 'qwen3:4b'])
        self.assertEqual(execute.call_args.args[2]['OLLAMA_HOST'], '127.0.0.1:11434')
        self.assertNotIn('local', assistants.assistants(), 'never an AI CLI recipe')

    def test_recipe_installs_the_official_package(self):
        repository = Path(__file__).resolve().parents[2]
        catalog = json.loads((repository / 'distro/software.json').read_text())
        self.assertEqual(catalog['tools']['ollama'], {'label': 'Ollama', 'source': 'pacman', 'packages': ['ollama']})
