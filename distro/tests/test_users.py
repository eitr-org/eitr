"""Account management tests never execute host account commands."""
import importlib.util
import io
import json
import os
from pathlib import Path
import pwd
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))
import eitr_users


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


system = load('user_system', ROOT / 'distro/system/eitr-system.py')
ui = load('user_ui', ROOT / 'walker/scripts/actions/system/users.py')


class UserTests(unittest.TestCase):
    def request(self, **changes):
        values = dict(username='new_desktop_test', full_name='Desktop Test', account_type='standard', password='test-passphrase')
        values.update(changes)
        return io.StringIO(json.dumps(values))

    def test_validation(self):
        for name in ('alex', '_test', 'a' * 32, 'user-2'):
            self.assertTrue(eitr_users.valid_username(name))
        for name in ('root', '', '-name', 'Aname', 'a' * 33, 'a:b', 'a\n', '../name'):
            self.assertFalse(eitr_users.valid_username(name))
        for value in ('Name:injection', 'Name\nextra', 'name\0', 'name,other', 'x' * 257):
            self.assertFalse(eitr_users.valid_full_name(value))
        self.assertTrue(eitr_users.valid_full_name(''))
        self.assertTrue(eitr_users.valid_full_name('Élodie Example'))
        for value in ('short', 'longpass\nroot:bad', 'longpass\r', 'longpass\0'):
            self.assertFalse(eitr_users.valid_password(value))

    def test_installer_uses_shared_validation(self):
        source = (ROOT / 'distro/archinstall/installer-ui.py').read_text()
        self.assertIn('from eitr_users import valid_username', source)
        self.assertNotIn('def valid_username', source)

    def test_standard_creation_and_skeleton(self):
        calls = []
        def command(arguments, **options):
            calls.append((arguments, options))
            if arguments[0] == 'useradd':
                skeleton = Path(arguments[arguments.index('--skel') + 1])
                self.assertEqual(sorted(str(path.relative_to(skeleton)) for path in skeleton.rglob('*') if path.is_file()),
                                 ['.config/uwsm/env-hyprland', '.local/state/eitr/seed-pending'])
                hook = (skeleton / '.config/uwsm/env-hyprland').read_text()
                self.assertIn('/usr/share/eitr/lib/eitr_users.py', hook)
                # A failed first-login setup must never abort the login itself.
                self.assertTrue(hook.rstrip().endswith('|| true'))
                self.assertNotIn('exit', hook)
        with patch.object(system.pwd, 'getpwnam', side_effect=KeyError), patch.object(system, 'run', side_effect=command), patch.object(system, 'atomic') as atomic:
            system.create_user(self.request())
        arguments = calls[0][0]
        self.assertEqual(arguments[-2:], ['--', 'new_desktop_test'])
        self.assertIn('/usr/bin/zsh', arguments)
        self.assertNotIn('wheel', arguments)
        self.assertNotIn('--groups', arguments)
        self.assertEqual(calls[1], (['chpasswd'], {'input': 'new_desktop_test:test-passphrase\n', 'text': True}))
        self.assertNotIn('test-passphrase', repr([call[0] for call in calls]))
        atomic.assert_not_called()

    def test_administrator(self):
        with patch.object(system.pwd, 'getpwnam', side_effect=KeyError), patch.object(system, 'run') as command, patch.object(system, 'atomic') as atomic:
            system.create_user(self.request(account_type='administrator'))
        self.assertIn('wheel', command.call_args_list[0].args[0])
        self.assertEqual(command.call_args_list[2].args[0], ['visudo', '-cf', '-'])
        self.assertEqual(atomic.call_args.args[1], 'new_desktop_test ALL=(ALL) ALL\n')
        self.assertEqual(atomic.call_args.kwargs['mode'], 0o440)

    def test_refusals_before_commands(self):
        for changes in (dict(username='root'), dict(full_name='test\ninjection'), dict(password='bad\npassword'),
                        dict(account_type='wheel,root'), dict(extra='bad')):
            with self.subTest(changes=changes), patch.object(system, 'run') as command:
                with self.assertRaises(ValueError):
                    system.create_user(self.request(**changes))
                command.assert_not_called()
        with patch.object(system.pwd, 'getpwnam', return_value=object()), patch.object(system, 'run') as command:
            with self.assertRaisesRegex(ValueError, 'already exists'):
                system.create_user(self.request())
            command.assert_not_called()
        for target in ('/home/new_desktop_test', '/etc/sudoers.d/eitr-user-new_desktop_test'):
            with patch.object(system.pwd, 'getpwnam', side_effect=KeyError), patch.object(Path, 'exists', lambda path: str(path) == target), patch.object(system, 'run') as command:
                with self.assertRaises(ValueError):
                    system.create_user(self.request())
                command.assert_not_called()

    def test_failure_locks_without_deleting(self):
        def command(arguments, **options):
            if arguments == ['chpasswd']:
                raise subprocess.CalledProcessError(1, arguments)
        with patch.object(system.pwd, 'getpwnam', side_effect=KeyError), patch.object(system, 'run', side_effect=command) as run:
            with self.assertRaisesRegex(RuntimeError, 'locked and expired'):
                system.create_user(self.request())
        self.assertEqual(run.call_args.args[0], ['usermod', '--lock', '--expiredate', '1', '--', 'new_desktop_test'])

    def test_human_users_read_only(self):
        accounts = [types.SimpleNamespace(pw_uid=uid, pw_name=name) for uid, name in ((0, 'root'), (1000, 'zeta'), (1001, 'alex'), (65534, 'nobody'))]
        with patch.object(eitr_users.pwd, 'getpwall', return_value=accounts), patch.object(subprocess, 'run') as run:
            self.assertEqual([entry['Text'] for entry in ui.entries()], ['alex', 'zeta'])
            self.assertTrue(all(entry['Actions'] == {} for entry in ui.entries()))
            run.assert_not_called()

    def test_cancel_never_applies(self):
        with patch.object(sys, 'argv', ['users.py']), patch.object(Path, 'is_file', return_value=True), patch.object(ui, 'collect', side_effect=KeyboardInterrupt), patch.object(subprocess, 'run') as run:
            with self.assertRaises(KeyboardInterrupt):
                ui.main()
            run.assert_not_called()
        self.assertTrue(ui.steps()[-1].password)
        self.assertTrue(ui.steps()[1].optional)

    def test_seeding_once_and_retry(self):
        for fails in (False, True):
            with self.subTest(fails=fails), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                pending = home / '.local/state/eitr/seed-pending'
                pending.parent.mkdir(parents=True)
                pending.write_text('1\n')
                with patch.object(os, 'geteuid', return_value=1000), patch.object(Path, 'home', return_value=home), patch.object(pwd, 'getpwuid', return_value=types.SimpleNamespace(pw_dir=str(home))), patch.object(subprocess, 'run') as run:
                    if fails:
                        run.side_effect = subprocess.CalledProcessError(1, 'seed')
                        with self.assertRaises(subprocess.CalledProcessError):
                            eitr_users.seed_first_login()
                        self.assertTrue(pending.exists())
                    else:
                        eitr_users.seed_first_login()
                        self.assertFalse(pending.exists())
                        self.assertEqual(run.call_args_list[1].args[0], ['bash', '/usr/share/eitr/distro/install.sh', '--seed-user'])
                        self.assertEqual(run.call_args_list[0].args[0], ['eitr-config', 'adopt-layout', '--apply'])
                        eitr_users.seed_first_login()
                        self.assertEqual(run.call_count, 2)

    def test_seed_refuses_root_and_wrong_home(self):
        with patch.object(os, 'geteuid', return_value=0), patch.object(subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                eitr_users.seed_first_login()
            run.assert_not_called()
        with patch.object(os, 'geteuid', return_value=1000), patch.object(Path, 'home', return_value=Path('/different')), patch.object(pwd, 'getpwuid', return_value=types.SimpleNamespace(pw_dir='/home/test')):
            with self.assertRaises(ValueError):
                eitr_users.seed_first_login()
