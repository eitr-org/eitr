"""Remote system operations never reach the host: files and processes are mocked."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('remote_system', ROOT / 'distro/system/eitr_remote.py')
remote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remote)


class RemoteSystemTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        for name, value in {'ROOT': self.root, 'STATE': self.root / 'state',
                            'RULES': self.root / 'run/firewall.d/remote-access.nft',
                            'GUARD': self.root / 'etc/remote-access.nft',
                            'BINARY': self.root / 'sunshine'}.items():
            patcher = patch.object(remote, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        remote.BINARY.write_text('native')

        patcher = patch.object(remote.grp, 'getgrnam', return_value=SimpleNamespace(gr_gid=2345, gr_mem=['tester']))
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(remote.pwd, 'getpwall', return_value=[])
        patcher.start()
        self.addCleanup(patcher.stop)
        self.commands = []
        patcher = patch.object(remote, 'run', side_effect=self.run_command)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(remote, 'native_binary', return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(remote, 'firewall_active', return_value=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(remote, 'account')
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_command(self, command, **options):
        self.commands.append(command)
        return subprocess.CompletedProcess(command, 0, '', '')

    def setup_sharing(self):
        with patch.object(remote, 'output', return_value=''), patch('builtins.input', return_value='yes'):
            remote.setup('tester')

    def test_confirmation_refusal_writes_nothing(self):
        with patch.object(remote, 'output', return_value=''), patch('builtins.input', return_value='no'):
            with self.assertRaisesRegex(RuntimeError, 'Nothing'):
                remote.setup('tester')
        self.assertFalse(remote.STATE.exists())
        self.assertEqual(self.commands, [])

    def test_scopes_exclude_default_public_and_virtual_routes(self):
        routes = [dict(dev='enp1s0', dst='192.168.1.0/24', scope='link'),
                  dict(dev='enp1s0', dst='8.8.8.0/24', scope='link'),
                  dict(dev='enp1s0', dst='default', gateway='192.168.1.1'),
                  dict(dev='wg0', dst='10.0.0.0/8', scope='link'),
                  dict(dev='enp1s0', dst='0.0.0.0/0', scope='link'),
                  dict(dev='enp1s0', dst='fd00::/64', scope='link')]
        self.assertEqual(remote.scopes(routes), ['iifname "enp1s0" ip saddr 192.168.1.0/24',
                                                'iifname "enp1s0" ip6 saddr fd00::/64'])

    def test_scopes_accept_routes_as_ip_lists_them(self):
        # `ip -j route show scope link` omits the scope of the routes it shows.
        routes = [dict(dst='192.168.31.0/24', dev='wlan0', protocol='kernel', metric=1024, flags=[])]
        self.assertEqual(remote.scopes(routes, {'wlan0'}), ['iifname "wlan0" ip saddr 192.168.31.0/24'])

    @unittest.skipUnless(shutil.which('nft') and shutil.which('unshare'), 'nft and unshare required')
    def test_firewall_files_parse_with_nft(self):
        _, opened = remote.firewall_text(['iifname "wlan0" ip saddr 192.168.31.0/24'])
        _, closed = remote.firewall_text([])
        for text in (opened, closed):
            with tempfile.NamedTemporaryFile('w', suffix='.nft') as rules:
                rules.write(text)
                rules.flush()
                # A private network namespace lets nft check the syntax without root.
                check = subprocess.run(['unshare', '-rn', 'nft', '-c', '-f', rules.name],
                                       capture_output=True, text=True)
                if 'Operation not permitted' in check.stderr:
                    self.skipTest('user namespaces are unavailable')
                self.assertEqual(check.returncode, 0, check.stderr)

    def test_no_remote_web_opening_and_guard_precedes_connection_tracking(self):
        openings, guard = remote.firewall_text(['iifname "enp1s0" ip saddr 192.168.1.0/24'])
        self.assertNotIn('47990', openings)
        self.assertIn('iifname != "lo" tcp dport 47990 drop', guard)
        self.assertIn('priority -10', guard)
        self.assertIn('tailscale0', openings)
        self.assertNotIn('ct state established', guard)
        for line in openings.splitlines():
            self.assertIn('iifname ', line)
        self.assertIn('47998-48000', openings)

    def test_setup_is_idempotent_and_journal_precedes_mutations(self):
        self.setup_sharing()
        previous = remote.journal('sunshine')
        self.assertEqual(previous['user'], 'tester')
        self.assertIn(['setcap', 'cap_sys_admin+p', str(remote.BINARY)], self.commands)
        count = len(self.commands)
        with patch.object(remote, 'capture_ready', return_value=True):
            remote.setup('tester')
        self.assertEqual(len(self.commands), count)
        sudoers = (self.root / 'etc/sudoers.d/eitr-remote-access').read_text()
        self.assertNotIn('ALL)', sudoers)
        self.assertNotIn('remote-setup', sudoers)

    def test_close_revokes_all_interfaces_and_is_idempotent(self):
        self.setup_sharing()
        remote.RULES.parent.mkdir(parents=True, exist_ok=True)
        remote.RULES.write_text('opening')
        remote.sharing('tester', False)
        remote.sharing('tester', False)
        self.assertFalse(remote.RULES.exists())
        guard = remote.GUARD.read_text()
        self.assertNotIn(' return', guard)
        self.assertIn('47990 drop', guard)

    def test_open_failure_closes_rules(self):
        self.setup_sharing()
        def fail_once(command, **options):
            self.commands.append(command)
            if '-c' in command:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)
        previous = remote.journal('sunshine')
        previous['armed'] = True
        remote.save('sunshine', previous)
        with patch.object(remote, 'capture_ready', return_value=True), patch.object(remote, 'firewall_active', return_value=True), patch.object(remote, 'output', side_effect=lambda command: str(remote.BINARY) + ' cap_sys_admin=p' if command[0] == 'getcap' else '[]'), patch.object(remote, 'run', side_effect=fail_once):
            with self.assertRaises(subprocess.CalledProcessError):
                remote.sharing('tester', True)
        self.assertFalse(remote.RULES.exists())
        self.assertNotIn(' return', remote.GUARD.read_text())

    def test_tailscale_restores_original_operator_and_service_states(self):
        remote.save('tailscale', {'user': 'tester', 'enabled': False, 'active': False, 'operator': 'previous'})
        with patch('builtins.input', return_value='yes'):
            remote.tailscale('tester', undo=True)
        self.assertIn(['tailscale', 'set', '--operator=previous'], self.commands)
        self.assertIn(['systemctl', 'stop', 'tailscaled.service'], self.commands)
        self.assertIn(['systemctl', 'disable', 'tailscaled.service'], self.commands)
        self.assertIsNone(remote.journal('tailscale'))

    def test_existing_tailscaled_is_not_stopped_on_undo(self):
        remote.save('tailscale', {'user': 'tester', 'enabled': True, 'active': True, 'operator': ''})
        with patch('builtins.input', return_value='yes'):
            remote.tailscale('tester', undo=True)
        self.assertFalse(any('stop' in command or 'disable' in command for command in self.commands))

    def test_unarmed_first_start_has_no_network_openings(self):
        self.setup_sharing()
        remote.sharing('tester', True)
        self.assertFalse(remote.RULES.exists())
        self.assertNotIn(' return', remote.GUARD.read_text())

    def test_arm_follows_start_sharing_without_another_question(self):
        with self.assertRaisesRegex(RuntimeError, 'Sharing Setup'):
            remote.arm('tester')
        self.setup_sharing()
        with patch('builtins.input', side_effect=AssertionError('arm must not ask again')):
            remote.arm('tester')
        self.assertTrue(remote.journal('sunshine')['armed'])

    def test_failed_setup_restores_original_files(self):
        original = self.root / 'etc/modules-load.d/eitr-remote-input.conf'
        original.parent.mkdir(parents=True)
        original.write_text('original module setting')
        original.chmod(0o640)
        def fail_validation(command, **options):
            if command[0] == 'visudo':
                raise subprocess.CalledProcessError(1, command)
            return self.run_command(command, **options)
        with patch.object(remote, 'run', side_effect=fail_validation), \
                patch.object(remote, 'output', return_value=''), \
                patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), \
                patch('builtins.input', return_value='yes'):
            with self.assertRaises(subprocess.CalledProcessError):
                remote.setup('tester')
        self.assertEqual(original.read_text(), 'original module setting')
        self.assertEqual(original.stat().st_mode & 0o777, 0o640)
        self.assertFalse((self.root / 'etc/sudoers.d/eitr-remote-access').exists())
        self.assertIsNone(remote.journal('sunshine'))

    def test_tailscale_setup_failure_rolls_back_service(self):
        def service_state(command, **options):
            return subprocess.CompletedProcess(command, 1, 'disabled\n', '')
        def fail_operator(command, **options):
            self.commands.append(command)
            if command == ['tailscale', 'set', '--operator=tester']:
                raise subprocess.CalledProcessError(1, command)
            return subprocess.CompletedProcess(command, 0)
        with patch.object(remote.subprocess, 'run', side_effect=service_state), \
                patch.object(remote, 'output', return_value='{"OperatorUser":"previous"}'), \
                patch.object(remote, 'run', side_effect=fail_operator), patch('builtins.input', return_value='yes'):
            with self.assertRaises(subprocess.CalledProcessError):
                remote.tailscale('tester')
        for command in (['tailscale', 'set', '--operator=previous'],
                        ['systemctl', 'stop', remote.UNIT], ['systemctl', 'disable', remote.UNIT]):
            self.assertIn(command, self.commands)
        self.assertIsNone(remote.journal('tailscale'))

    def test_undo_unloads_only_the_module_loaded_by_setup(self):
        self.setup_sharing()
        (self.root / 'sys/module/uinput').mkdir(parents=True)
        with patch.object(remote, 'output', return_value=''), \
                patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), \
                patch('builtins.input', return_value='yes'):
            remote.undo_sunshine('tester')
        self.assertIn(['modprobe', '-r', 'uinput'], self.commands)
        self.assertIsNone(remote.journal('sunshine'))

    def test_upgraded_binary_requires_confirmed_regrant(self):
        self.setup_sharing()
        original = remote.journal('sunshine')
        with patch.object(remote, 'output', return_value=''), patch('builtins.input', return_value='no'):
            with self.assertRaisesRegex(RuntimeError, 'Nothing'):
                remote.setup('tester')
        with patch.object(remote, 'output', return_value=''), patch('builtins.input', return_value='yes'):
            remote.setup('tester')
        self.assertEqual(remote.journal('sunshine'), original)
        self.assertEqual(self.commands[-1], ['setcap', 'cap_sys_admin+p', str(remote.BINARY)])

    def test_grant_restricts_execution_before_capability_without_service_restart(self):
        self.setup_sharing()
        owner = ['chown', 'root:eitr-sharing', str(remote.BINARY)]
        mode = ['chmod', '0750', str(remote.BINARY)]
        capability = ['setcap', 'cap_sys_admin+p', str(remote.BINARY)]
        self.assertLess(self.commands.index(owner), self.commands.index(capability))
        self.assertLess(self.commands.index(mode), self.commands.index(capability))
        self.assertIn(['usermod', '-a', '-G', 'eitr-sharing', 'tester'], self.commands)
        self.assertFalse(any(command[0] == 'systemctl' for command in self.commands))

    def test_capture_status_rejects_global_mode_wrong_group_and_extra_capabilities(self):
        metadata = SimpleNamespace(st_gid=2345, st_mode=0o100750)
        with patch.object(remote.BINARY.__class__, 'stat', return_value=metadata), \
                patch.object(remote, 'output', return_value=str(remote.BINARY) + ' cap_sys_admin=p'):
            self.assertTrue(remote.capture_ready('tester'))
            metadata.st_mode = 0o100755
            self.assertFalse(remote.capture_ready('tester'))
            metadata.st_mode = 0o104750
            self.assertFalse(remote.capture_ready('tester'))
            metadata.st_mode = 0o100750
            metadata.st_gid = 0
            self.assertFalse(remote.capture_ready('tester'))
            metadata.st_gid = 2345
            with patch.object(remote, 'output', return_value=str(remote.BINARY) + ' cap_sys_admin,cap_net_admin=p'):
                self.assertFalse(remote.capture_ready('tester'))

    def test_setup_refuses_other_group_members_before_mutations(self):
        with patch.object(remote.grp, 'getgrnam', return_value=SimpleNamespace(gr_gid=2345, gr_mem=['other'])):
            with self.assertRaisesRegex(RuntimeError, 'only the sharing account'):
                remote.setup('tester')
        self.assertEqual(self.commands, [])
        self.assertFalse(remote.STATE.exists())

    def test_old_global_grant_is_repaired_even_when_capability_exists(self):
        self.setup_sharing()
        original = remote.journal('sunshine')
        self.commands.clear()
        with patch.object(remote, 'capture_ready', return_value=False), \
                patch.object(remote, 'output', return_value=str(remote.BINARY) + ' cap_sys_admin=p'), \
                patch('builtins.input', return_value='yes'):
            remote.setup('tester')
        self.assertEqual(self.commands[0], ['setcap', '-r', str(remote.BINARY)])
        self.assertEqual(self.commands[-1], ['setcap', 'cap_sys_admin+p', str(remote.BINARY)])
        self.assertEqual(remote.journal('sunshine'), original)

    def test_restore_removes_membership_and_never_restores_global_capability(self):
        self.setup_sharing()
        previous = remote.journal('sunshine')
        previous['capabilities'] = str(remote.BINARY) + ' cap_sys_admin=p'
        remote.save('sunshine', previous)
        self.commands.clear()
        with patch.object(remote, 'output', return_value=str(remote.BINARY) + ' cap_sys_admin=p'), \
                patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            remote.undo_sunshine('tester', ask=False)
        self.assertEqual(self.commands[:3], [['setcap', '-r', str(remote.BINARY)],
                                            ['chown', 'root:root', str(remote.BINARY)],
                                            ['chmod', '0755', str(remote.BINARY)]])
        self.assertIn(['gpasswd', '-d', 'tester', 'eitr-sharing'], self.commands)
        self.assertNotIn(['setcap', 'cap_sys_admin+p', str(remote.BINARY)], self.commands)
        self.assertIsNone(remote.journal('sunshine'))

    def test_restore_after_package_removal_still_revokes_membership(self):
        self.setup_sharing()
        remote.BINARY.unlink()
        self.commands.clear()
        with patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)):
            remote.undo_sunshine('tester', ask=False)
        self.assertIn(['gpasswd', '-d', 'tester', 'eitr-sharing'], self.commands)
        self.assertFalse(any(command[0] == 'setcap' for command in self.commands))

    def test_package_declares_system_group_without_capability_install_hook(self):
        package = ROOT / 'distro/pkg/eitr-sunshine'
        self.assertEqual((package / 'eitr-sharing.conf').read_text(), 'g eitr-sharing -\n')
        recipe = (package / 'PKGBUILD').read_text()
        self.assertIn('/usr/lib/sysusers.d/eitr-sharing.conf', recipe)
        self.assertNotIn('setcap', recipe)

    def test_packaged_root_import_with_isolated_python(self):
        library = self.root / 'usr/lib/eitr'
        library.mkdir(parents=True)
        shared = self.root / 'usr/share/eitr/lib'
        shutil.copytree(ROOT / 'distro/lib', shared)
        for source, target in [('eitr-system.py', 'eitr-system'), ('eitr_remote.py', 'eitr_remote.py')]:
            shutil.copy2(ROOT / 'distro/system' / source, library / target)
        (library / 'eitr_bootstrap.py').symlink_to(shared / 'eitr_bootstrap.py')
        result = subprocess.run(['python3', '-I', str(library / 'eitr-system'), '--help'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = subprocess.run(['python3', '-I', '-c',
                                 'import sys; sys.path.insert(0, sys.argv[1]); import eitr_bootstrap; import eitr_remote',
                                 str(library)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == '__main__':
    unittest.main()
