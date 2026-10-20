import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('git_accounts', ROOT / 'walker/scripts/actions/development/git-accounts.py')
accounts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(accounts)


class GitAccountTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        environment = dict(os.environ, HOME=str(self.home), XDG_CONFIG_HOME=str(self.home / 'config'),
                           XDG_STATE_HOME=str(self.home / 'state'), GIT_CONFIG_NOSYSTEM='1')
        for key in list(environment):
            if key.startswith('GIT_CONFIG_') and key != 'GIT_CONFIG_NOSYSTEM':
                del environment[key]
        self.env = patch.dict(os.environ, environment, clear=True)
        self.env.start()
        self.addCleanup(self.env.stop)
        self.personal, self.work, self.nested = 'a' * 32, 'b' * 32, 'c' * 32
        self.model = {'version': 1, 'unknown': 'preserve', 'default': self.personal,
                      'folders': [], 'accounts': {}}
        for identifier, label in ((self.personal, 'Personal'), (self.work, 'Work'), (self.nested, 'Nested')):
            self.model['accounts'][identifier] = {'label': label, 'provider': 'github', 'host': 'github.com',
                                                 'name': label, 'email': label.lower() + '@example.com', 'key': ''}

    def repo(self, name):
        path = self.home / name
        path.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(path)], check=True)
        return path

    def value(self, repo, key):
        return subprocess.check_output(['git', '-C', str(repo), 'config', '--get', key], text=True).strip()

    def test_real_git_default_folder_nested_local_and_removal(self):
        original = '# keep comments\n[user]\n name = Existing\n email = existing@example.com\n[alias]\n st = status\n'
        (self.home / '.gitconfig').write_text(original)
        general = self.repo('personal/project')
        work = self.repo('work/one')
        nested = self.repo('work/special/project')
        sibling = self.repo('work-other/project')
        self.model['folders'] = [{'path': str(self.home / 'work'), 'account': self.work},
                                 {'path': str(self.home / 'work/special'), 'account': self.nested}]
        accounts.apply(self.model)
        self.assertEqual(self.value(general, 'user.name'), 'Personal')
        self.assertEqual(self.value(work, 'user.name'), 'Work')
        self.assertEqual(self.value(nested, 'user.name'), 'Nested')
        self.assertEqual(self.value(sibling, 'user.name'), 'Personal')
        self.assertEqual(self.value(work, 'alias.st'), 'status')
        subprocess.run(['git', '-C', str(work), 'config', 'user.name', 'Local'], check=True)
        self.assertEqual(self.value(work, 'user.name'), 'Local')
        self.assertEqual(accounts.load()['unknown'], 'preserve')
        self.model['default'] = None
        self.model['folders'] = []
        accounts.apply(self.model)
        self.assertEqual(self.value(general, 'user.name'), 'Existing')
        self.assertEqual((self.home / '.gitconfig').read_text(), original)

    def test_spaces_and_quotes_do_not_inject_git_config(self):
        repo = self.repo('projects with spaces/one')
        self.model['accounts'][self.work]['name'] = 'Work "User"'
        self.model['folders'] = [{'path': str(repo.parent), 'account': self.work}]
        accounts.apply(self.model)
        self.assertEqual(self.value(repo, 'user.name'), 'Work "User"')
        bad = copy.deepcopy(self.model)
        bad['accounts'][self.work]['email'] = 'mail\n[core]\nsshCommand=evil'
        with self.assertRaises(ValueError):
            accounts.apply(bad)

    def test_backups_and_global_symlink_refusal(self):
        (self.home / '.gitconfig').write_text('[user]\nname=Old\n')
        accounts.apply(self.model)
        backups = list((self.home / 'state/eitr/git-account-backups').glob('*/0'))
        self.assertEqual(backups[0].read_text(), '[user]\nname=Old\n')
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o600)
        (self.home / '.gitconfig').unlink()
        target = self.home / 'elsewhere'
        target.write_text('untouched')
        (self.home / '.gitconfig').symlink_to(target)
        with self.assertRaises(ValueError):
            accounts.apply(self.model)
        self.assertEqual(target.read_text(), 'untouched')

    def test_edited_managed_block_aborts(self):
        accounts.apply(self.model)
        global_file = self.home / '.gitconfig'
        global_file.write_text(global_file.read_text().replace('active.gitconfig', 'my.gitconfig'))
        before = global_file.read_text()
        with self.assertRaises(ValueError):
            accounts.apply(self.model)
        self.assertEqual(global_file.read_text(), before)

    def test_cli_profiles_are_isolated_and_environment_tokens_removed(self):
        with patch.dict(os.environ, {'GH_TOKEN': 'do-not-use', 'GITLAB_TOKEN': 'do-not-use'}):
            personal = accounts.cli_environment(self.personal, self.model['accounts'][self.personal])
            work = accounts.cli_environment(self.work, self.model['accounts'][self.work])
            self.assertNotIn('GH_TOKEN', work)
            self.assertNotIn('GITLAB_TOKEN', work)
            self.assertNotEqual(personal['GH_CONFIG_DIR'], work['GH_CONFIG_DIR'])
            gitlab = dict(self.model['accounts'][self.work], provider='gitlab', host='gitlab.com')
            environment = accounts.cli_environment(self.work, gitlab)
            self.assertIn('GLAB_CONFIG_DIR', environment)
            self.assertNotIn('GH_CONFIG_DIR', environment)

    def test_key_is_not_inherited_by_a_keyless_folder_account(self):
        key = self.home / 'key'
        key.write_text('test key, never read')
        key.chmod(0o600)
        self.model['accounts'][self.personal]['key'] = str(key)
        work = self.repo('work/project')
        self.model['folders'] = [{'path': str(work.parent), 'account': self.work}]
        accounts.apply(self.model)
        self.assertEqual(self.value(work, 'core.sshCommand'), 'ssh')

    def test_ssh_matching_host_isolated_other_hosts_unchanged(self):
        key = self.home / 'key'
        key.write_text('never read')
        key.chmod(0o600)
        account = dict(self.model['accounts'][self.personal], key=str(key))
        result = subprocess.CompletedProcess([], 0, 'hostname github.com\nuser git\nport 22\n')
        with patch.object(accounts.subprocess, 'run', return_value=result):
            command = accounts.ssh_args(self.personal, account, ['git@github.com'])
            self.assertIn(str(key), command)
            self.assertIn('/dev/null', command)
        result.stdout = 'hostname gitlab.com\nuser git\nport 22\n'
        with patch.object(accounts.subprocess, 'run', return_value=result):
            self.assertEqual(accounts.ssh_args(self.personal, account, ['git@gitlab.com']), ['ssh', 'git@gitlab.com'])

    def test_future_version_is_read_only(self):
        accounts.settings_path().parent.mkdir(parents=True)
        accounts.settings_path().write_text('{"version":2}')
        with self.assertRaises(ValueError):
            accounts.load()

    def test_stale_preview_and_future_schema_cannot_overwrite_settings(self):
        stale = copy.deepcopy(self.model)
        accounts.apply(self.model)
        before = accounts.settings_path().read_text()
        with self.assertRaises(ValueError):
            accounts.apply(stale)
        self.assertEqual(accounts.settings_path().read_text(), before)
        accounts.settings_path().write_text('{"version":2}')
        with self.assertRaises(ValueError):
            accounts.apply(self.model)
        self.assertEqual(accounts.settings_path().read_text(), '{"version":2}')

    def test_apply_failure_restores_original_files(self):
        original = '[user]\nname=Old\n'
        (self.home / '.gitconfig').write_text(original)
        real_atomic = accounts.atomic

        def failing(path, text, mode=0o600):
            if path == self.home / '.gitconfig' and accounts.BEGIN in text:
                raise OSError('simulated write error')
            return real_atomic(path, text, mode)

        with patch.object(accounts, 'atomic', side_effect=failing), self.assertRaises(OSError):
            accounts.apply(self.model)
        self.assertEqual((self.home / '.gitconfig').read_text(), original)
        self.assertFalse(accounts.settings_path().exists())
        self.assertFalse((accounts.root() / 'active.gitconfig').exists())

    def answer(self, *values):
        answers = iter(values)
        return patch('builtins.input', side_effect=lambda prompt='': next(answers))

    def test_add_form_sets_default_and_folder_in_one_pass(self):
        projects = self.home / 'Development/personal'
        projects.mkdir(parents=True)
        with self.answer('', 'Personal', 'Erick', 'me@example.com', '', '', '', str(projects), ''):
            self.assertTrue(accounts.add_form(copy.deepcopy(accounts.load())))
        model = accounts.load()
        (identifier, account), = model['accounts'].items()
        self.assertEqual((account['label'], account['provider'], account['host']), ('Personal', 'github', 'github.com'))
        self.assertEqual(model['default'], identifier)
        self.assertEqual(model['folders'], [{'path': str(projects.resolve()), 'account': identifier}])

    def test_add_form_keeps_an_existing_default_unless_asked(self):
        accounts.apply(self.model)
        before = accounts.load()
        with self.answer('2', 'Lab', 'Erick', 'lab@example.com', '', '', '', '', 'y'):
            accounts.add_form(copy.deepcopy(before))
        after = accounts.load()
        self.assertEqual(after['default'], before['default'])
        self.assertIn('gitlab.com', [account['host'] for account in after['accounts'].values()])

    def test_declining_the_form_saves_nothing(self):
        with self.answer('', 'Personal', 'Erick', 'me@example.com', '', '', '', '', 'n'), \
                patch.object(accounts, 'apply') as apply:
            self.assertFalse(accounts.add_form(copy.deepcopy(accounts.load())))
            apply.assert_not_called()
        self.assertFalse(accounts.settings_path().exists())
        self.assertFalse((self.home / '.gitconfig').exists())

    def test_rows_say_where_each_account_applies(self):
        projects = self.home / 'Development/work'
        projects.mkdir(parents=True)
        self.model['folders'] = [{'path': str(projects), 'account': self.work}]
        accounts.apply(self.model)
        details = {row['label']: row['detail'] for row in accounts.rows()}
        self.assertEqual(details, {'Personal': 'Default', 'Work': 'work', 'Nested': 'Not used yet'})

    def test_walker_actions_change_default_and_folders_after_confirmation(self):
        accounts.apply(self.model)
        projects = self.home / 'Development/work'
        projects.mkdir(parents=True)
        choices = iter(['Confirm'])
        with patch.object(accounts, 'walker', side_effect=lambda options, placeholder: next(choices)), \
                patch.object(accounts, 'notify') as notify:
            accounts.perform(self.work, 'Make Default')
        self.assertEqual(accounts.load()['default'], self.work)
        notify.assert_called_once_with('Work is now the default account')
        choices = iter(['~/Development/work', 'Confirm'])
        with patch.object(accounts, 'walker', side_effect=lambda options, placeholder: next(choices)), \
                patch.object(accounts, 'notify'):
            accounts.perform(self.nested, 'Add Folder')
        self.assertEqual(accounts.load()['folders'], [{'path': str(projects.resolve()), 'account': self.nested}])
        choices = iter(['~/Development/work', 'Cancel'])
        with patch.object(accounts, 'walker', side_effect=lambda options, placeholder: next(choices)), \
                patch.object(accounts, 'notify') as notify:
            accounts.perform(self.nested, 'Remove Folder')
        self.assertEqual(len(accounts.load()['folders']), 1)
        notify.assert_not_called()

    def test_typing_actions_open_a_terminal_form(self):
        accounts.apply(self.model)
        with patch.object(accounts, 'in_terminal') as terminal:
            accounts.perform(self.work, 'Edit Name and Email')
        terminal.assert_called_once_with('edit', self.work)

    def test_key_actions_appear_only_with_a_key_and_clone_check_are_gone(self):
        names = accounts.account_actions(self.model, self.work)
        self.assertNotIn('Show Public Key', names)
        self.assertEqual(names, sorted(names, key=str.casefold))
        key = self.home / 'key'
        key.write_text('private')
        key.chmod(0o600)
        self.model['accounts'][self.work]['key'] = str(key)
        self.assertIn('Show Public Key', accounts.account_actions(self.model, self.work))
        menu = (ROOT / 'elephant/menus/git-accounts.lua').read_text()
        self.assertNotIn('clone', menu)
        self.assertNotIn('check', menu)
        self.assertIn('" rows"', menu)
        self.assertIn('SubMenu = "git-account"', menu)
        submenu = (ROOT / 'elephant/menus/git-account.lua').read_text()
        self.assertIn('Parent = "git-accounts"', submenu)
        self.assertIn('lastMenuValue("git-accounts")', submenu)
        self.assertIn('" do "', submenu)

    def test_unavailable_or_unknown_actions_are_refused(self):
        accounts.apply(self.model)
        with self.assertRaises(ValueError):
            accounts.perform(self.work, 'Show Public Key')
        self.assertEqual(accounts.action_rows('f' * 32), [])
        rows = accounts.action_rows(self.work)
        self.assertTrue(all(row['hint'] and row['icon'] for row in rows))

    def test_provider_defaults_and_key_permissions(self):
        key = self.home / 'key'
        key.write_text('private content must never enter backups')
        key.chmod(0o644)
        with self.assertRaises(ValueError):
            accounts.private_key(key)
        key.chmod(0o600)
        self.model['accounts'][self.work].update(provider='gitlab', host='gitlab.com', key=str(key))
        self.model['default'] = self.work
        repo = self.repo('gitlab/project')
        accounts.apply(self.model)
        self.assertEqual(self.value(repo, 'user.name'), 'Work')
        self.assertIn(self.work, self.value(repo, 'core.sshCommand'))
        self.assertEqual(self.value(repo, 'ssh.variant'), 'ssh')
        for backup in (self.home / 'state/eitr/git-account-backups').rglob('*'):
            if backup.is_file():
                self.assertNotIn('private content must never enter backups', backup.read_text())


class ImportExistingSetupTests(unittest.TestCase):
    setUp, repo, value = GitAccountTests.setUp, GitAccountTests.repo, GitAccountTests.value

    def manual_setup(self):
        git = self.home / 'config/git'
        git.mkdir(parents=True)
        for folder in ('personal', 'work'):
            (self.home / 'Development' / folder).mkdir(parents=True)
        (git / 'config').write_text(
            '[user]\n\tname = Erick\n\temail = me@example.com\n'
            '[includeIf "gitdir:~/Development/personal/**"]\n\tpath = ~/config/git/personal.inc\n'
            '[includeIf "gitdir:~/Development/work/"]\n\tpath = work.inc\n'
            '[includeIf "gitdir:~/Development/*/legacy/"]\n\tpath = work.inc\n')
        (git / 'personal.inc').write_text('[user]\n\tname = Erick\n\temail = me@example.com\n'
                                          '[url "git@github-personal:"]\n\tinsteadOf = git@github.com:\n')
        (git / 'work.inc').write_text('[user]\n\tname = Erick Work\n\temail = me@work.example\n'
                                      '[url "git@github-work:"]\n\tinsteadOf = git@github.com:\n')

    def route(self, alias):
        return 'github.com', str(self.home / f'.ssh/{alias}')

    def test_manual_identities_folders_and_keys_are_found(self):
        self.manual_setup()
        with patch.object(accounts, 'ssh_route', side_effect=self.route):
            found = accounts.existing_setup()
        self.assertEqual(found['default']['email'], 'me@example.com')
        folders = {Path(entry['path']).name: entry for entry in found['folders']}
        self.assertEqual(sorted(folders), ['personal', 'work'])
        self.assertTrue(folders['personal']['key'].endswith('github-personal'))
        self.assertEqual(folders['work']['email'], 'me@work.example')
        self.assertEqual(found['skipped'], ['gitdir:~/Development/*/legacy/'])

    def test_import_creates_accounts_rules_and_reuses_identities(self):
        self.manual_setup()
        with patch.object(accounts, 'ssh_route', side_effect=self.route):
            found = accounts.existing_setup()
        model = accounts.import_setup(copy.deepcopy(accounts.load()), found)
        labels = sorted(account['label'] for account in model['accounts'].values())
        self.assertEqual(labels, ['Personal', 'Work'])
        personal = next(key for key, account in model['accounts'].items() if account['label'] == 'Personal')
        self.assertEqual(model['default'], personal)
        self.assertEqual(len(model['folders']), 2)
        accounts.apply(model)
        repo = self.repo('Development/work/app')
        self.assertEqual(self.value(repo, 'user.email'), 'me@work.example')
        again = accounts.import_setup(copy.deepcopy(accounts.load()), found)
        self.assertEqual(len(again['accounts']), 2)
        self.assertEqual(len(again['folders']), 2)

    def test_import_never_reads_back_eitr_managed_rules(self):
        accounts.apply(self.model)
        found = accounts.existing_setup()
        self.assertEqual(found['folders'], [])


if __name__ == '__main__':
    unittest.main()
