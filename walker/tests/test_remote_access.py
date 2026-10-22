import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import Mock, patch
from home_isolation import setUpModule, tearDownModule

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('walker_remote_access', ROOT / 'walker/scripts/actions/system/remote-access.py')
remote = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remote)


class RemoteAccessTests(unittest.TestCase):
    def test_cancel_never_starts_sharing(self):
        with patch('builtins.input', return_value='no'), patch.object(remote, 'run') as run:
            remote.host('start')
        run.assert_not_called()

    def test_stop_disables_login_and_closes_ports(self):
        with patch.object(remote, 'run') as run, patch.object(remote, 'root') as root:
            remote.host('stop')
        run.assert_called_once_with(['systemctl', '--user', 'disable', '--now', remote.SERVICE])
        root.assert_called_once_with('close')

    def test_installs_are_only_through_recipes(self):
        software = Mock()
        with patch.object(remote, 'software', return_value=software), patch.object(remote, 'root') as root, \
                patch.object(remote.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1)), \
                patch.object(remote.Path, 'is_file', return_value=False):
            remote.host('setup')
            remote.away('setup')
        self.assertEqual(software.recipe.call_args_list[0].args, ('remote-access', 'sunshine'))
        self.assertEqual(software.recipe.call_args_list[1].args, ('remote-access', 'tailscale'))
        self.assertEqual([call.args for call in root.call_args_list], [('setup',), ('tailscale',)])

    def test_diagnostic_reports_wait_for_escape_but_actions_close(self):
        for provider, handler in (('host', 'host'), ('away', 'away')):
            with self.subTest(provider=provider), patch.object(remote, handler) as action, \
                    patch.object(remote, 'wait_for_escape') as wait:
                remote.main([provider, 'status'])
                action.assert_called_once_with('status')
                wait.assert_called_once_with()
            with patch.object(remote, handler), patch.object(remote, 'wait_for_escape') as wait:
                remote.main([provider, 'stop' if provider == 'host' else 'disconnect'])
                wait.assert_not_called()

    def test_signed_out_status_and_direct_relay_paths(self):
        data = {'BackendState': 'NeedsLogin', 'TailscaleIPs': [], 'Peer': {
            'one': {'Online': True, 'Active': True, 'HostName': 'direct', 'CurAddr': '192.168.0.1:123', 'Relay': 'fra'},
            'two': {'Online': True, 'Active': True, 'HostName': 'relay', 'Relay': 'fra'}}}
        with patch.object(remote, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(data))), patch('builtins.print') as printed:
            remote.status()
        text = '\n'.join(str(call.args[0]) for call in printed.call_args_list)
        for expected in ('No Tailscale address', 'direct: Direct', 'relay: Relayed', 'Choose Sign In'):
            self.assertIn(expected, text)

    def test_only_tailscale_https_login_urls_open(self):
        self.assertEqual(remote.auth_url('Visit https://login.tailscale.com/a/test\n'), 'https://login.tailscale.com/a/test')
        for line in ('https://evil.test/', 'http://login.tailscale.com/', 'https://login.tailscale.com.evil.test/', 'https://user@login.tailscale.com/'):
            self.assertIsNone(remote.auth_url(line))

    def test_connect_signed_out_uses_browser_flow(self):
        result = subprocess.CompletedProcess([], 0, '{"BackendState":"NeedsLogin"}')
        with patch.object(remote, 'run', return_value=result), patch.object(remote, 'login') as login, \
                patch.object(remote, 'tailscale_control') as control:
            remote.away('connect')
        login.assert_called_once()
        control.assert_called_once_with('up')

    def test_operator_switches_without_password_and_others_fall_back_to_sudo(self):
        allowed = subprocess.CompletedProcess([], 0, '', '')
        with patch.object(remote.subprocess, 'run', return_value=allowed) as plain, patch.object(remote, 'run') as run:
            remote.away('disconnect')
        self.assertEqual(plain.call_args.args[0], ['tailscale', 'down'])
        run.assert_not_called()
        denied = subprocess.CompletedProcess([], 1, '', 'Access denied: prefs write access denied\n')
        with patch.object(remote.subprocess, 'run', return_value=denied), patch.object(remote, 'run') as run:
            remote.away('disconnect')
        run.assert_called_once_with(['sudo', 'tailscale', 'down'])
        failed = subprocess.CompletedProcess([], 1, '', 'backend error\n')
        with patch.object(remote.subprocess, 'run', return_value=failed), patch.object(remote, 'run') as run:
            with self.assertRaisesRegex(RuntimeError, 'backend error'):
                remote.away('disconnect')
        run.assert_not_called()

    def test_failed_install_does_not_enable_service(self):
        software = Mock()
        software.recipe.side_effect = subprocess.CalledProcessError(1, 'pacman')
        with patch.object(remote, 'software', return_value=software), patch.object(remote, 'root') as root:
            with self.assertRaises(subprocess.CalledProcessError):
                remote.away('setup')
        root.assert_not_called()

    def test_first_start_stops_if_password_step_is_declined(self):
        with patch('builtins.input', side_effect=['yes', 'no']), \
                patch.object(remote, 'run') as run, patch.object(remote, 'root') as root:
            remote.host('start')
        root.assert_not_called()
        self.assertEqual(run.call_args.args[0], ['systemctl', '--user', 'stop', remote.SERVICE])

    def test_login_opens_printed_url_once_and_reports_failures(self):
        process = Mock()
        process.stdout = iter(['https://login.tailscale.com/a/test\n', 'https://login.tailscale.com/a/test\n'])
        process.wait.return_value = 1
        context = Mock()
        context.__enter__ = Mock(return_value=process)
        context.__exit__ = Mock(return_value=False)
        with patch.object(remote.subprocess, 'Popen', return_value=context) as popen, patch.object(remote, 'open_page') as page:
            with self.assertRaisesRegex(RuntimeError, 'sign-in failed'):
                remote.login()
        # The user is Tailscale's operator after Away Access Setup: no sudo, no password.
        self.assertEqual(popen.call_args.args[0], ['tailscale', 'login'])
        page.assert_called_once_with('https://login.tailscale.com/a/test')


    def test_idle_peer_is_not_reported_as_relayed(self):
        data = {'Peer': {'idle': {'HostName': 'idle', 'Online': True, 'Active': False, 'Relay': 'fra'}}}
        with patch.object(remote, 'run', return_value=subprocess.CompletedProcess([], 0, json.dumps(data))), patch('builtins.print') as printed:
            remote.status()
        self.assertIn('Idle; ping to check', printed.call_args.args[0])

    def test_user_service_always_closes_ports_on_exit(self):
        unit = (ROOT / 'systemd/user/eitr-sunshine.service').read_text()
        self.assertIn('ExecStopPost=/usr/bin/sudo -n /usr/lib/eitr/eitr-system remote-close %u', unit)
        self.assertNotIn('Restart=always', unit)
        self.assertNotIn('enable', unit)


if __name__ == '__main__':
    unittest.main()
