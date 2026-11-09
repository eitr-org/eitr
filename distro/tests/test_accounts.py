"""Account changes are exercised with every host command and policy write mocked."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
import eitr_accounts as accounts
from test_users import ui


class AccountTests(unittest.TestCase):
    def setUp(self):
        self.alex = SimpleNamespace(pw_name='alex', pw_uid=1000, pw_gid=1000)
        self.ana = SimpleNamespace(pw_name='ana', pw_uid=1001, pw_gid=1001)
        self.command = Mock(return_value=SimpleNamespace(stdout=''))
        self.atomic = Mock()
        for patcher in (
                patch.object(accounts, 'human_users', return_value=[self.alex, self.ana]),
                patch.object(accounts, 'is_administrator', side_effect=lambda account: account.pw_name == 'alex'),
                patch.dict(os.environ, SUDO_USER='alex'),
                patch.object(accounts.os, 'geteuid', return_value=0),
                patch.object(accounts.fcntl, 'flock'), patch.object(Path, 'open', unittest.mock.mock_open()),
                patch.object(Path, 'unlink'), patch.object(Path, 'exists', return_value=False)):
            patcher.start()
            self.addCleanup(patcher.stop)

    def apply(self, action, **request):
        accounts.dispatch('user-' + action, io.StringIO(json.dumps(request)), self.command, self.atomic)

    def test_promotion_validates_then_writes_atomic_policy_and_grants_wheel(self):
        self.apply('set-type', username='ana', account_type='administrator')
        self.assertEqual(self.command.call_args_list[0].args[0], ['visudo', '-cf', '-'])
        self.assertEqual(self.atomic.call_args.args, (Path('/etc/sudoers.d/eitr-user-ana'), 'ana ALL=(ALL) ALL\n'))
        self.assertEqual(self.atomic.call_args.kwargs, dict(mode=0o440, directory_mode=0o750))
        self.assertEqual(self.command.call_args_list[1].args[0], ['usermod', '--append', '--groups', 'wheel', '--', 'ana'])

    def test_invalid_policy_never_grants_membership_or_writes(self):
        self.command.side_effect = subprocess.CalledProcessError(1, ['visudo'])
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply('set-type', username='ana', account_type='administrator')
        self.atomic.assert_not_called()
        self.assertEqual(self.command.call_count, 1)

    def test_membership_failure_cleans_new_policy(self):
        self.command.side_effect = [None, subprocess.CalledProcessError(1, ['usermod'])]
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply('set-type', username='ana', account_type='administrator')
        Path.unlink.assert_called_once_with(missing_ok=True)

    def test_demotion_and_policy_cleanup(self):
        with patch('grp.getgrnam', return_value=SimpleNamespace(gr_mem=['ana', 'alex'], gr_gid=998)):
            self.apply('set-type', username='ana', account_type='standard')
        self.command.assert_called_once_with(['gpasswd', '--delete', 'ana', 'wheel'])
        Path.unlink.assert_called_once_with(missing_ok=True)

    def test_last_administrator_cannot_be_demoted_or_removed(self):
        for action, fields in [('set-type', dict(account_type='standard')), ('remove', dict(delete_home=False))]:
            with self.subTest(action=action), patch.dict(os.environ, SUDO_USER=''), \
                    patch.object(accounts, 'is_administrator', return_value=True):
                with patch.object(accounts, 'human_users', return_value=[self.alex]):
                    with self.assertRaisesRegex(ValueError, 'last administrator'):
                        self.apply(action, username='alex', **fields)
        self.command.assert_not_called()

    def test_self_password_and_removal_refused(self):
        for action, fields in [('set-password', dict(password='new-password')), ('remove', dict(delete_home=True))]:
            with self.assertRaisesRegex(ValueError, 'own account'):
                self.apply(action, username='alex', **fields)
        self.command.assert_not_called()

    def test_password_only_in_stdin(self):
        self.apply('set-password', username='ana', password='new-password')
        self.command.assert_called_once_with(['chpasswd'], input='ana:new-password\n', text=True)
        self.assertNotIn('new-password', repr(self.command.call_args.args))

    def test_remove_home_choice_and_cleanup_after_success(self):
        for delete in (False, True):
            self.command.reset_mock()
            self.apply('remove', username='ana', delete_home=delete)
            self.assertEqual(self.command.call_args.args[0], ['userdel', *(['--remove'] if delete else []), '--', 'ana'])
        self.command.side_effect = subprocess.CalledProcessError(1, ['loginctl'])
        Path.unlink.reset_mock()
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply('remove', username='ana', delete_home=False)
        Path.unlink.assert_not_called()

    def test_active_session_or_unverifiable_output_refuses_deletion(self):
        for output in ('3 1001 ana seat0 tty2 active yes -', 'unexpected output'):
            self.command.reset_mock()
            self.command.return_value.stdout = output
            with self.assertRaises(ValueError):
                self.apply('remove', username='ana', delete_home=False)
            self.assertEqual(self.command.call_count, 1)
            Path.unlink.assert_not_called()

    def test_invalid_and_nonhuman_accounts_refused_for_all_actions(self):
        for action, fields in [('set-password', dict(password='new-password')),
                               ('set-type', dict(account_type='standard')), ('remove', dict(delete_home=False))]:
            for username in ('root', '../ana', '-ana', 'service', 'a' * 33):
                with self.subTest(action=action, username=username), self.assertRaises(ValueError):
                    self.apply(action, username=username, **fields)
        self.command.assert_not_called()

    def test_request_bounds_and_extra_keys(self):
        for document in ('x' * 32769, '[]', '{"username":"ana","password":"new-password","extra":true}'):
            with self.assertRaises(ValueError):
                accounts.dispatch('user-set-password', io.StringIO(document), self.command, self.atomic)
        self.command.assert_not_called()

    def test_invalid_fields_and_unauthorized_invoker(self):
        for action, fields in [('set-type', dict(account_type='wheel')), ('remove', dict(delete_home='yes')),
                               ('set-password', dict(password='bad\npassword'))]:
            with self.assertRaises(ValueError):
                self.apply(action, username='ana', **fields)
        with patch.dict(os.environ, SUDO_USER='ana'), self.assertRaisesRegex(ValueError, 'administrators'):
            self.apply('set-password', username='alex', password='new-password')
        self.command.assert_not_called()

    def test_failed_removal_keeps_sudoers(self):
        self.command.side_effect = [SimpleNamespace(stdout=''), subprocess.CalledProcessError(1, ['userdel'])]
        with self.assertRaises(subprocess.CalledProcessError):
            self.apply('remove', username='ana', delete_home=True)
        Path.unlink.assert_not_called()

    def test_nonroot_and_missing_fields_refused(self):
        with patch.object(accounts.os, 'geteuid', return_value=1000), self.assertRaises(ValueError):
            self.apply('remove', username='ana', delete_home=False)
        for document in ('{}', '{"username":"ana"}', 'null'):
            with self.assertRaises(ValueError):
                accounts.dispatch('user-remove', io.StringIO(document), self.command, self.atomic)
        self.command.assert_not_called()

    def test_primary_wheel_is_not_silently_left_administrative(self):
        self.ana.pw_gid = 998
        with patch('grp.getgrnam', return_value=SimpleNamespace(gr_mem=[], gr_gid=998)), self.assertRaises(ValueError):
            self.apply('set-type', username='ana', account_type='standard')
        self.command.assert_not_called()
        Path.unlink.assert_not_called()


class AccountPromptTests(unittest.TestCase):
    def test_cancel_and_invalid_cli_never_execute(self):
        with patch.object(ui, 'read_key', return_value='\x1b'), patch.object(ui.subprocess, 'run') as run:
            ui.manage(['remove', 'ana'])
            run.assert_not_called()
        with patch.object(ui.subprocess, 'run') as run, self.assertRaises(ValueError):
            ui.manage(['set-type', 'ana'])
        run.assert_not_called()

    def test_cli_password_twice_and_no_secret_in_argv(self):
        with patch.object(ui, 'read_key', return_value='\r'), \
                patch.object(ui.getpass, 'getpass', side_effect=['new-password', 'new-password']), \
                patch.object(ui.subprocess, 'run') as run:
            ui.manage(['set-password', 'ana'])
        self.assertEqual(run.call_args.args[0], ['sudo', ui.HELPER, 'user-set-password'])
        self.assertEqual(json.loads(run.call_args.kwargs['input']), dict(username='ana', password='new-password'))

    def test_cli_password_mismatch_and_invalid_password(self):
        for passwords in (['new-password', 'different-password'], ['short', 'short']):
            with patch.object(ui, 'read_key', return_value='\n'), \
                    patch.object(ui.getpass, 'getpass', side_effect=passwords), \
                    patch.object(ui.subprocess, 'run') as run, self.assertRaises(ValueError):
                ui.manage(['set-password', 'ana'])
            run.assert_not_called()

    def test_cli_type_and_remove_payloads(self):
        for arguments, expected in [(['set-type', 'ana', '--account-type', 'administrator'], dict(username='ana', account_type='administrator')),
                                    (['remove', 'ana'], dict(username='ana', delete_home=False)),
                                    (['remove', 'ana', '--delete-home'], dict(username='ana', delete_home=True))]:
            with patch.object(ui, 'read_key', return_value='\n'), patch.object(ui.subprocess, 'run') as run:
                ui.manage(arguments)
            self.assertEqual(json.loads(run.call_args.kwargs['input']), expected)
