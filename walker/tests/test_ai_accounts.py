"""Account isolation without starting sessions or opening a real browser."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

from home_isolation import setUpModule, tearDownModule
import eitr_ai_accounts as accounts
import eitr_assistants as assistants
import eitr_collaboration as collaboration

ROOT = Path(__file__).resolve().parents[2]


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.patcher = patch.object(Path, 'home', return_value=self.home)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def add_account(self, identifier='codex', label='Example'):
        with patch.object(assistants, 'executable', return_value=Path('/mock/bin/' + identifier)), \
                patch.object(subprocess, 'run', return_value=Mock(returncode=0)) as login:
            self.assertEqual(accounts.add(identifier, label), 0)
        account = accounts.rows(identifier)[1]['id']
        return account, login.call_args

    def test_add_login_private_permissions_and_switch(self):
        for identifier, (variable, _, login_arguments) in accounts.CONFIGURATION.items():
            if variable is None:
                continue
            account, call = self.add_account(identifier)
            folder = accounts.folder(identifier, account)
            self.assertEqual(folder.stat().st_mode & 0o777, 0o700)
            self.assertEqual(accounts.config('eitr/ai-accounts.json').stat().st_mode & 0o777, 0o600)
            self.assertEqual(call.args[0], ['/mock/bin/' + identifier, *login_arguments])
            self.assertEqual(call.kwargs['env'][variable], str(folder))
            self.assertTrue(call.kwargs['env']['BROWSER'].endswith('ai-private-browser.py'))
            self.assertTrue(accounts.rows(identifier)[0]['current'])
            accounts.switch(identifier, account)
            self.assertTrue(accounts.rows(identifier)[1]['current'])
            accounts.switch(identifier, 'default')
            self.assertNotIn(variable, accounts.environment(identifier, {}))

    def test_launch_and_headless_environment(self):
        account, _ = self.add_account()
        accounts.switch('codex', account)
        with patch.object(assistants, 'executable', return_value=Path('/mock/bin/codex')), \
                patch.object(assistants, 'assistant_access', return_value='full'), \
                patch.object(os, 'chdir'), \
                patch.object(os, 'execve') as execute:
            assistants.launch('codex', [], trusted=True)
        self.assertEqual(execute.call_args.args[2]['CODEX_HOME'], str(accounts.folder('codex', account)))
        self.assertIn('--dangerously-bypass-approvals-and-sandbox', execute.call_args.args[1])
        auth = accounts.folder('codex', account) / 'auth.json'
        auth.write_text(json.dumps({'tokens': {'access_token': 'fake'}}))
        with patch.object(collaboration, 'executable', return_value=Path('/mock/bin/codex')), \
                patch.object(collaboration.subprocess, 'Popen') as process, patch.dict(os.environ, {collaboration.DEPTH: ''}):
            process.return_value.communicate.return_value = (json.dumps({'type': 'item.completed', 'item': {'type': 'agent_message', 'text': 'Example answer'}}), '')
            process.return_value.returncode = 0
            collaboration.ask('codex', 'example', announce=False)
        self.assertEqual(process.call_args.kwargs['env']['CODEX_HOME'], str(auth.parent))

    def test_delete_falls_back_and_protects_default(self):
        account, _ = self.add_account()
        accounts.switch('codex', account)
        accounts.delete('codex', account)
        self.assertFalse(accounts.folder('codex', account).exists())
        self.assertTrue(accounts.rows('codex')[0]['current'])
        with self.assertRaises(ValueError):
            accounts.delete('codex', 'default')

    def test_cancelled_login_retains_account_without_switching(self):
        with patch.object(assistants, 'executable', return_value=Path('/mock/bin/codex')), \
                patch.object(subprocess, 'run', return_value=Mock(returncode=1)):
            self.assertEqual(accounts.add('codex', 'Example'), 1)
        self.assertEqual(len(accounts.rows('codex')), 2)
        self.assertTrue(accounts.rows('codex')[0]['current'])

    def test_cancelled_wizard_and_delete_change_nothing(self):
        account, _ = self.add_account()
        before = accounts.config('eitr/ai-accounts.json').read_bytes()
        with patch('eitr_wizard.collect', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                accounts.main(['add', 'codex'])
        with patch.object(accounts.sys.stdin, 'isatty', return_value=True), \
                patch('eitr_terminal.read_key', return_value='\x1b'), patch('builtins.print'):
            self.assertEqual(accounts.main(['delete', 'codex', account]), 1)
        self.assertEqual(accounts.config('eitr/ai-accounts.json').read_bytes(), before)
        self.assertTrue(accounts.folder('codex', account).exists())

    def test_unsupported_and_local(self):
        self.assertFalse(accounts.menu('agy')['supported'])
        self.assertEqual(len(accounts.menu('agy')['accounts']), 1)
        with self.assertRaises(ValueError):
            accounts.load('local')

    def test_gemini_parent_home_and_default_override(self):
        account, _ = self.add_account('gemini')
        accounts.switch('gemini', account)
        self.assertEqual(accounts.config_folder('gemini'), accounts.folder('gemini', account) / '.gemini')
        self.assertEqual(accounts.environment('codex', {'CODEX_HOME': '/existing'}), {'CODEX_HOME': '/existing'})

    def test_usage_hides_unreadable_accounts_and_preserves_isolation(self):
        account, _ = self.add_account()
        specification = importlib.util.spec_from_file_location('account_usage', ROOT / 'quickshell/desktop-bar/scripts/ai-usage.py')
        usage = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(usage)
        with patch.object(usage, 'cli_binary', side_effect=lambda identifier: '/mock/codex' if identifier == 'codex' else None), \
                patch.object(usage, 'codex_usage', side_effect=[{'windows': [{'used': 10}]}, RuntimeError('private-token')]) as reader:
            result = usage.collect()
        entries = result['providers'][0]['accounts']
        self.assertEqual([entry['label'] for entry in entries], ['Default'])
        self.assertEqual(entries[0]['windows'], [{'used': 10}])
        self.assertNotIn('private-token', json.dumps(result))
        self.assertEqual(reader.call_args_list[1].args[0]['CODEX_HOME'], str(accounts.folder('codex', account)))

    def test_menu_structure_and_delete_binding(self):
        for identifier in accounts.CONFIGURATION:
            name = 'ai-' + identifier + '-accounts'
            self.assertIn('Parent = "ai-' + identifier + '"', (ROOT / f'elephant/menus/{name}.lua').read_text())
            rows = json.loads((ROOT / f'elephant/menu-rows/ai-{identifier}.json').read_text())
            self.assertEqual(rows[0]['text'], 'Accounts')
            self.assertEqual(rows[0]['subtext'], '>')
            self.assertEqual((ROOT / f'walker/themes/current/item_menus-{name}.xml').read_bytes(),
                             (ROOT / 'walker/themes/current/item_menus-main.xml').read_bytes())
        self.assertIn('action = "ai_account_delete", label = "Delete", bind = "Delete"', (ROOT / 'walker/config.toml').read_text())
        source = (ROOT / 'elephant/ai-account-entries.lua').read_text()
        self.assertIn('account.id ~= "default"', source)
        self.assertIn('Separate accounts unavailable', source)

    def test_account_menu_lua_current_delete_and_unsupported(self):
        for supported in ('true', 'false'):
            harness = r'''jsonDecode = function()
                return {supported = SUPPORTED, accounts = {
                    {id = "default", label = "Default", current = true},
                    {id = "0123456789abcdef0123456789abcdef", label = "Personal", current = false}}}
            end
            io.popen = function() return {read = function() return "{}" end, close = function() end} end
            local entries = dofile("elephant/ai-account-entries.lua")("codex")()
            assert(entries[1].Text == "Default")
            assert(entries[1].State[1] == "current")
            assert(entries[1].Icon == "\239\128\140")
            assert(entries[1].Actions.ai_account_delete == nil)
            assert(entries[2].Actions.ai_account_delete:find(" delete ", 1, true))
            assert(entries[2].Actions.open:find(" switch ", 1, true))
            if SUPPORTED then
                assert(entries[3].Text == "Add Account…")
            else
                assert(entries[3].Text == "Separate accounts unavailable")
                assert(entries[3].Actions.open == nil)
            end
            '''.replace('SUPPORTED', supported)
            environment = dict(os.environ, EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'), EITR_CODE_ROOT=str(ROOT), LC_ALL='C.UTF-8')
            subprocess.run(['lua', '-e', harness], cwd=ROOT, env=environment, check=True, capture_output=True, text=True)

    def test_private_browser_flags_and_unknown_fallback(self):
        specification = importlib.util.spec_from_file_location('private_browser', ROOT / 'walker/scripts/actions/ai-private-browser.py')
        browser = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(browser)
        directory = self.home / '.local/share/applications'
        directory.mkdir(parents=True)
        for binary, flag in [('firefox', '--private-window'), ('chromium', '--incognito'), ('microsoft-edge', '--inprivate'), ('unknown', None)]:
            (directory / 'browser.desktop').write_text('[Desktop Entry]\nExec=' + binary + ' %U\n')
            with patch.object(browser.subprocess, 'run', return_value=Mock(stdout='browser.desktop\n')):
                command = browser.browser_command('https://example.invalid/login')
            self.assertEqual(command, [binary, flag, 'https://example.invalid/login'] if flag else ['xdg-open', 'https://example.invalid/login'])
        with patch.object(browser, 'browser_command', return_value=['xdg-open', 'https://example.invalid/login']), \
                patch.object(browser.subprocess, 'run', return_value=Mock(returncode=0)) as opener, \
                patch.dict(os.environ, {'BROWSER': '/helper'}):
            browser.open_private('https://example.invalid/login')
        self.assertNotIn('BROWSER', opener.call_args.kwargs['env'])
