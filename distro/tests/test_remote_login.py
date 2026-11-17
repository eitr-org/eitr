"""Share the Login Screen: session rules, hand-over, identity copy and undo, all mocked."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/system'))
import eitr_remote as remote  # noqa: E402
import eitr_remote_login as login  # noqa: E402

GREETER = {'session': 'c1', 'uid': 966, 'user': 'sddm', 'seat': 'seat0', 'class': 'greeter'}
DESKTOP = {'session': '2', 'uid': 1000, 'user': 'tester', 'seat': 'seat0', 'class': 'user'}
SSH = {'session': '7', 'uid': 1000, 'user': 'tester', 'seat': None, 'class': 'user'}
MANAGER = {'session': '3', 'uid': 1000, 'user': 'tester', 'seat': None, 'class': 'manager'}


class SessionRuleTests(unittest.TestCase):
    def test_only_a_local_user_session_counts_as_signed_in(self):
        self.assertFalse(login.user_signed_in([GREETER]))
        self.assertFalse(login.user_signed_in([GREETER, SSH, MANAGER]))
        self.assertTrue(login.user_signed_in([GREETER, DESKTOP]))
        self.assertTrue(login.user_signed_in([{**DESKTOP, 'class': 'user-early'}]))
        self.assertFalse(login.user_signed_in([]))


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.runner = login.Runner('tester')
        self.events = []
        for name in ('start', 'stop'):
            patcher = patch.object(self.runner, name, side_effect=lambda name=name: self.events.append(name))
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_starts_at_the_greeter_and_stops_when_someone_signs_in(self):
        self.runner.step([GREETER])
        self.runner.step([GREETER, DESKTOP])
        self.assertEqual(self.events, ['start', 'stop'])

    def test_retries_a_crashing_sunshine_after_a_growing_pause(self):
        self.runner.child = SimpleNamespace(poll=lambda: 134, returncode=134)
        self.runner.stop.side_effect = lambda: (self.events.append('stop'), setattr(self.runner, 'child', None))
        self.runner.step([GREETER], now=100)
        self.assertEqual(self.events, ['stop'])
        self.runner.step([GREETER], now=102)
        self.assertEqual(self.events, ['stop'])
        self.runner.step([GREETER], now=103)
        self.assertEqual(self.events, ['stop', 'start'])
        self.runner.child = SimpleNamespace(poll=lambda: 134, returncode=134)
        self.runner.started = 103
        self.runner.step([GREETER], now=110)
        self.assertEqual(self.runner.next_start, 116)
        self.runner.child = SimpleNamespace(poll=lambda: 134, returncode=134)
        self.runner.started = 120
        self.runner.step([GREETER], now=500)
        self.assertEqual(self.runner.next_start, 503)

    def test_a_running_sunshine_is_left_alone(self):
        self.runner.child = SimpleNamespace(poll=lambda: None)
        self.runner.step([GREETER])
        self.assertEqual(self.events, [])


class HandOverTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        patches = [patch.object(login, 'STATE', self.root / 'login-screen'), patch.object(login, 'STATUS', self.root / 'run/status.json'),
                   patch.object(login, 'copy_identity'), patch.object(login, 'user_sunshine_running', return_value=False)]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.calls = []
        patcher = patch.object(login.remote, 'sharing', side_effect=lambda *arguments, **options: self.calls.append(('sharing', arguments, options)))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(login.subprocess, 'run', side_effect=lambda command, **_: self.calls.append(('run', command)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_ports_open_for_the_login_screen_and_close_with_it(self):
        child = SimpleNamespace(terminate=lambda: self.calls.append('terminate'), wait=lambda *_: 0, kill=lambda: None)
        with patch.object(login.subprocess, 'Popen', return_value=child) as popen:
            runner = login.Runner('tester')
            runner.start()
            self.assertTrue(json.loads(login.STATUS.read_text())['streaming'])
            runner.stop()
        options = popen.call_args.kwargs
        self.assertEqual(options['user'], login.ACCOUNT)
        self.assertEqual(options['env']['HOME'], str(login.STATE))
        self.assertEqual(popen.call_args.args[0], ['/usr/bin/sunshine', str(login.STATE / 'sunshine.conf')])
        self.assertIn(('sharing', ('tester', True), {'owner': 'login-screen'}), self.calls)
        self.assertIn(('sharing', ('tester', False), {'owner': 'login-screen'}), self.calls)
        self.assertLess(self.calls.index('terminate'), self.calls.index(('sharing', ('tester', False), {'owner': 'login-screen'})))
        self.assertFalse(json.loads(login.STATUS.read_text())['streaming'])

    def test_waits_while_the_users_own_sunshine_still_runs(self):
        with patch.object(login, 'user_sunshine_running', return_value=True), patch.object(login.subprocess, 'Popen') as popen:
            runner = login.Runner('tester')
            runner.start()
        popen.assert_not_called()
        self.assertIsNone(runner.child)


class IdentityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.home = self.root / 'home'
        sunshine = self.home / '.config/sunshine'
        (sunshine / 'credentials').mkdir(parents=True)
        (sunshine / 'sunshine_state.json').write_text(json.dumps({'root': {'uniqueid': 'id', 'named_devices': [{'name': 'Mac'}]}}))
        (sunshine / 'credentials/cacert.pem').write_text('certificate')
        (sunshine / 'credentials/cakey.pem').write_text('key')
        account = SimpleNamespace(pw_dir=str(self.home), pw_uid=os.getuid(), pw_gid=os.getgid())
        patcher = patch.object(login.pwd, 'getpwnam', return_value=account)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_copies_the_identity_and_writes_safe_settings(self):
        target = self.root / 'login-screen'
        login.copy_identity('tester', target)
        self.assertEqual((target / 'credentials/cakey.pem').read_text(), 'key')
        self.assertEqual((target / 'credentials/cakey.pem').stat().st_mode & 0o777, 0o600)
        settings = dict(line.split(' = ', 1) for line in (target / 'sunshine.conf').read_text().splitlines())
        self.assertEqual(settings['upnp'], 'off')
        self.assertEqual(settings['stream_audio'], 'false')
        self.assertEqual(settings['capture'], 'kms')
        self.assertEqual(settings['origin_web_ui_allowed'], 'pc')
        self.assertEqual(settings['system_tray'], 'disabled')
        self.assertEqual(settings['file_state'], str(target / 'sunshine_state.json'))
        self.assertEqual(json.loads((target / 'apps.json').read_text())['apps'][0]['name'], 'Desktop')
        self.assertEqual(login.paired_devices('tester'), 1)

    def test_refuses_a_linked_file_in_the_users_home(self):
        state = self.home / '.config/sunshine/sunshine_state.json'
        state.unlink()
        state.symlink_to('/etc/shadow')
        with self.assertRaises(OSError):
            login.copy_identity('tester', self.root / 'login-screen')

    def test_refuses_a_linked_folder_in_the_users_home(self):
        elsewhere = self.root / 'elsewhere'
        (self.home / '.config/sunshine').rename(elsewhere)
        (self.home / '.config/sunshine').symlink_to(elsewhere)
        with self.assertRaises(OSError):
            login.copy_identity('tester', self.root / 'login-screen')


class SwitchTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        patches = [patch.object(remote, 'STATE', self.root / 'state'), patch.object(login, 'STATE', self.root / 'state/login-screen'),
                   patch.object(login, 'STATUS', self.root / 'run/status.json'),
                   patch.object(remote, 'account', return_value=SimpleNamespace(pw_uid=1000))]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.commands = []
        for module in (login.remote, login.subprocess):
            patcher = patch.object(module, 'run', side_effect=lambda command, **_: self.commands.append(command) or SimpleNamespace(returncode=0))
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_requires_setup_the_password_step_and_a_paired_device(self):
        with self.assertRaises(RuntimeError):
            login.enable('tester')
        remote.save('sunshine', {'user': 'tester'})
        with self.assertRaises(RuntimeError):
            login.enable('tester')
        remote.save('sunshine', {'user': 'tester', 'armed': True})
        with patch.object(remote, 'capture_ready', return_value=True), patch.object(login, 'paired_devices', return_value=0):
            with self.assertRaises(RuntimeError):
                login.enable('tester')
        self.assertEqual(self.commands, [])

    def test_turning_it_off_leaves_nothing_behind(self):
        login.STATE.mkdir(parents=True)
        (login.STATE / 'sunshine.conf').write_text('upnp = off\n')
        remote.save('login-screen', {'user': 'tester'})
        with patch.object(login.pwd, 'getpwnam', return_value=SimpleNamespace()):
            login.disable('tester', ask=False)
        self.assertIn(['systemctl', 'disable', '--now', login.UNIT], self.commands)
        self.assertIn(['userdel', login.ACCOUNT], self.commands)
        self.assertFalse(login.STATE.exists())
        self.assertIsNone(remote.journal('login-screen'))


class PortOwnerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        patches = [patch.object(remote, 'STATE', self.root / 'state'), patch.object(remote, 'RULES', self.root / 'rules.nft'),
                   patch.object(remote, 'GUARD', self.root / 'guard.nft'), patch.object(remote, 'account'),
                   patch.object(remote, 'run'), patch.object(remote, 'firewall_active', return_value=False)]
        for patcher in patches:
            patcher.start()
            self.addCleanup(patcher.stop)
        remote.save('sunshine', {'user': 'tester', 'armed': True})
        remote.RULES.write_text('openings\n')

    def test_a_close_never_shuts_ports_the_other_side_opened_since(self):
        remote.save('sharing', {'user': 'tester', 'openings': '', 'owner': 'login-screen'})
        remote.sharing('tester', False, 'session')
        self.assertTrue(remote.RULES.exists())
        remote.sharing('tester', False, 'login-screen')
        self.assertFalse(remote.RULES.exists())

    def test_restore_closes_whatever_is_open(self):
        remote.save('sharing', {'user': 'tester', 'openings': '', 'owner': 'login-screen'})
        remote.sharing('tester', False)
        self.assertFalse(remote.RULES.exists())


if __name__ == '__main__':
    unittest.main()
