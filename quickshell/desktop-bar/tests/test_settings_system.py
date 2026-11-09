"""Settings projections use canonical data and never execute menu actions on reads."""
import re
import importlib.util
from pathlib import Path
import sys
import os
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('settings_system', SCRIPTS / 'settings-system.py')
settings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(settings)


class SettingsSystemTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        environment = patch.dict(os.environ, EITR_CODE_ROOT=str(SCRIPTS.parents[2]),
                                 XDG_CONFIG_HOME=temporary.name, XDG_STATE_HOME=temporary.name,
                                 XDG_DATA_HOME=temporary.name, LC_ALL='C.UTF-8')
        environment.start()
        self.addCleanup(environment.stop)

    def test_security_controls_expand_without_self_navigation(self):
        controls = settings.static_controls('security')
        titles = [entry['title'] for entry in controls]
        for title in ('Enable Fingerprint Authentication', 'Enroll Security Key', 'Enroll TPM Unlock', 'Remove TPM Unlock', 'Firewall', 'Create User…'):
            self.assertIn(title, titles)
        self.assertEqual(next(entry for entry in controls if entry['title'] == 'Profile Picture')['page'], 'user')
        self.assertTrue(all('menu' not in entry for entry in controls))

    def test_git_controls_use_inline_confirmation_and_selection(self):
        git = settings.module('settings_git_inline_test', 'walker/scripts/actions/development/git-accounts.py')
        model = {'accounts': {'fixture': {'label': 'Example'}}, 'default': None,
                 'folders': [{'account': 'fixture', 'path': '/projects/example'}]}
        with patch.object(git, 'load', return_value=model), patch.object(git, 'save') as save, patch.object(git, 'walker', side_effect=AssertionError('Walker opened')):
            git.perform('fixture', 'Remove Folder', confirmation=lambda question: False, picker=lambda options, prompt: options[0])
            save.assert_not_called()
            git.perform('fixture', 'Remove Folder', confirmation=lambda question: True, picker=lambda options, prompt: options[0])
            self.assertEqual(save.call_args.args[0]['folders'], [])
            git.perform('fixture', 'Make Default', confirmation=lambda question: True)
            self.assertEqual(save.call_args.args[0]['default'], 'fixture')

    def test_security_leaf_actions_and_assistant_dropdown_survive_projection(self):
        items = [{'title': 'Firewall', 'menu': '', 'actionMenu': 'security'},
                 {'title': 'Fingerprint', 'menu': 'fingerprint'},
                 {'title': 'Assistant Access', 'menu': 'assistant-access'}]
        with patch.object(settings, 'summary', return_value={'items': items}), patch('eitr_assistants.assistant_access', return_value='ask'):
            result = settings.controls_summary('security')
        self.assertNotIn('controls', result['items'][0])
        self.assertEqual(result['items'][0]['actionMenu'], 'security')
        self.assertTrue(result['items'][1]['controls'])
        self.assertEqual(result['access'], 'ask')

    def test_assistant_account_actions_are_direct_and_forms_use_task_terminals(self):
        accounts = {'supported': True, 'accounts': [{'id': 'default', 'label': 'Default', 'current': True}, {'id': 'fixture', 'label': 'Example'}]}
        with patch('eitr_assistants.assistants', return_value={'codex': {'label': 'Example assistant'}}), patch('eitr_assistants.available', return_value=True), patch('eitr_ai_accounts.menu', return_value=accounts):
            result = settings.assistants()['items']
        commands = [entry['command'] for item in result for entry in item['controls']]
        self.assertTrue(any('switch' in command and 'fixture' in command for command in commands))
        self.assertTrue(any('delete' in command and any('task-terminal.py' in argument for argument in command) for command in commands))
        self.assertFalse(any(any('walker/bin/walker' in argument for argument in command) for command in commands))
        with patch('eitr_assistants.assistants', return_value={'codex': {'label': 'Example assistant'}}), patch('eitr_assistants.available', return_value=False):
            missing = settings.assistants()['items'][0]
        self.assertIn('recipe', missing['controls'][0]['command'])

    def test_assistant_page_offers_installed_defaults_and_the_offline_assistant(self):
        import eitr_local_assistant
        definitions = {'codex': {'label': 'Example assistant'}, 'claude': {'label': 'Missing assistant'}}
        with patch('eitr_assistants.assistants', return_value=definitions), \
                patch('eitr_assistants.available', side_effect=lambda identifier: identifier == 'codex'), \
                patch('eitr_assistants.default_assistant', return_value='codex'), \
                patch('eitr_assistants.assistant_access', return_value='ask'), \
                patch('eitr_ai_accounts.menu', return_value={'supported': False, 'accounts': []}), \
                patch('eitr_collaboration.enabled', return_value=True), \
                patch.object(eitr_local_assistant, 'installed', return_value=False), \
                patch.object(eitr_local_assistant, 'present', return_value=False):
            result = settings.assistants()
        self.assertEqual(result['choices'], [{'value': 'codex', 'label': 'Example assistant'}])
        self.assertEqual((result['current'], result['access'], result['collaboration']), ('codex', 'ask', True))
        self.assertEqual([item['title'] for item in result['items']], ['Example assistant', 'Missing assistant', 'Ratatoskr (local, experimental)'])
        local = result['items'][-1]['controls']
        self.assertEqual([control['title'] for control in local], ['Set Up'])
        self.assertIn('setup-local', local[0]['command'])
        self.assertTrue(any('task-terminal.py' in argument for argument in local[0]['command']))

    def test_shortcuts_resolve_every_canonical_reference(self):
        reference = settings.shortcut_reference()
        result = settings.shortcuts()['items']
        self.assertEqual(len(result), sum('heading' not in entry for entry in reference))
        self.assertTrue(all(entry['group'] and entry['title'] and entry['detail'] for entry in result))
        terminal = next(entry for entry in result if entry['title'] == 'Open terminal')
        self.assertEqual(terminal['detail'], next(entry['key'] for entry in reference if entry.get('description') == 'Open terminal'))

    def test_security_preserves_all_walker_actions(self):
        import eitr_selfcheck
        import eitr_assistants
        helper = SimpleNamespace(authentication_summary=lambda: {'fingerprint': {'available': True, 'services': []}, 'fido2': {'available': True, 'services': ['sudo']}})
        with patch.object(settings, 'module', return_value=helper), \
                patch.object(eitr_assistants, 'assistant_access', return_value='ask'), \
                patch.object(eitr_selfcheck, 'check_security_firewall', return_value=('info', 'Firewall active', '', '')):
            result = settings.security()['items']
        # Settings > Users lists the accounts and changes the password, and AI Assistant sets
        # assistant access, so Security leaves those Walker rows out; the rest belong to a tab.
        self.assertEqual([entry['title'] for entry in result],
                         [entry['text'] for entry in settings.rows('security') if entry['text'] not in ('Update Password', 'Assistant Access', 'Users')])
        self.assertEqual({entry['title'] for entry in result}, set(settings.SECURITY_TABS))
        self.assertEqual({entry['tab'] for entry in result}, {'sign-in', 'protection'})
        self.assertEqual(next(entry for entry in result if entry['title'] == 'Firewall')['detail'], 'Firewall active')
        for entry in result:
            self.assertTrue(entry['menu'] or entry['actionMenu'])

    def test_diagnostics_are_explicit_and_reads_are_visibility_scoped(self):
        pages = ('SettingsSystemHost', 'SettingsCheckPage', 'SettingsUserPage', 'SettingsUpdatesPage')
        source = re.sub(r"\s+", " ", '\n'.join((SCRIPTS.parent / 'settings' / f'{name}.qml').read_text() for name in pages))
        self.assertIn('command: ["eitr", "check", "--json"]', source)
        self.assertEqual(source.count('check.running = true'), 1)
        self.assertIn('onClicked: if (view.live && !check.running) check.running = true', source)
        self.assertIn('if (!active || !live) return;', source)
        self.assertIn('Component.onDestruction: DesktopData.releaseOwner(hostView)', source)
        self.assertIn('ProfilePicture {', source)
        # Change picture asks the portal's file chooser, then crops in a sheet over the window.
        self.assertIn('Eitr.Paths.library("eitr_avatar.py"), "choose"', source)
        self.assertIn('parent: Overlay.overlay', source)
        self.assertNotIn('editingPicture', source)
        self.assertIn('ChoiceLists.updateChannels', source)
        self.assertIn('menu-action.py', source)

    def test_authentication_reader_ignores_comments_and_never_writes(self):
        helper = settings.module('settings_security_test', 'walker/scripts/actions/system/security.py')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / 'sudo').write_text('auth sufficient pam_u2f.so # active\n# auth sufficient pam_fprintd.so\n')
            result = helper.authentication_summary(path)
            self.assertEqual(result['fido2']['services'], ['sudo'])
            self.assertEqual(result['fingerprint']['services'], [])
            self.assertTrue(result['fingerprint']['available'])


class UsersPageTests(unittest.TestCase):
    def test_every_login_is_listed_with_yours_first(self):
        import grp
        import pwd
        accounts = [SimpleNamespace(pw_name='ana', pw_uid=1001, pw_gid=1001, pw_gecos='Ana Lima,,,'),
                    SimpleNamespace(pw_name='explorer', pw_uid=1000, pw_gid=1000, pw_gecos='')]
        import eitr_users
        with patch.object(eitr_users, 'human_users', return_value=accounts), \
                patch.object(grp, 'getgrnam', return_value=SimpleNamespace(gr_mem=['explorer'], gr_gid=998)), \
                patch('os.getuid', return_value=1000):
            summary = settings.users()
            items = summary['items']
            self.assertTrue(summary['administrator'])
        self.assertEqual([item['login'] for item in items], ['explorer', 'ana'])
        self.assertTrue(items[0]['current'])
        self.assertTrue(items[0]['administrator'])
        self.assertEqual((items[1]['title'], items[1]['initial'], items[1]['administrator']), ('Ana Lima', 'A', False))

    def test_standard_account_has_no_management_access(self):
        import eitr_users
        account = SimpleNamespace(pw_name='standard', pw_uid=1000, pw_gid=1000, pw_gecos='Standard')
        with patch.object(eitr_users, 'human_users', return_value=[account]), \
                patch.object(eitr_users, 'is_administrator', return_value=False), patch('os.getuid', return_value=1000):
            self.assertFalse(settings.users()['administrator'])
