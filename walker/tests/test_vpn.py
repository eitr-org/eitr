import contextlib
import io
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
from eitr_vpn import import_arguments, wireguard_summary

ROOT = Path(__file__).resolve().parents[2]


class VPNTests(unittest.TestCase):
    def test_menu(self):
        rows = json.loads((ROOT / 'elephant/menu-rows/vpn.json').read_text())
        self.assertEqual([row['text'] for row in rows], ['NetworkManager VPN', 'Tailscale', 'WireGuard'])
        self.assertTrue(all(row['subtext'] for row in rows))
        self.assertTrue(all('task-terminal.py' in row['actions']['open'] for row in rows))

    def test_packages(self):
        catalog = json.loads((ROOT / 'distro/software.json').read_text())['vpn']
        self.assertEqual(catalog['wireguard']['packages'], ['wireguard-tools'])
        self.assertEqual(catalog['networkmanager']['packages'], ['networkmanager-openvpn', 'networkmanager-openconnect'])
        transactions = (ROOT / 'distro/payload/transactions.txt').read_text().splitlines()
        for item in catalog.values():
            self.assertIn(' '.join(item['packages']), transactions)

    def test_redaction_and_multiple_peers(self):
        summary = wireguard_summary('vpn0', '[Interface]\nPrivateKey=SECRET\n[Peer]\nPublicKey=PUBLIC\nPresharedKey=SECRET2\nEndpoint=vpn.example:51820\n[Peer]\nPublicKey=OTHER')
        self.assertEqual(summary, 'vpn0 · vpn.example:51820 · 2')
        for secret in ('SECRET', 'PUBLIC', 'OTHER'):
            self.assertNotIn(secret, summary)

    def test_hooks_and_names_rejected(self):
        for line in ('PreUp=touch /tmp/unwanted', 'PostDown=SECRET', 'SaveConfig=true'):
            with self.assertRaises(ValueError) as failure:
                wireguard_summary('vpn0', '[Interface]\n' + line + '\n[Peer]')
            self.assertNotIn('SECRET', str(failure.exception))
        with self.assertRaises(ValueError):
            wireguard_summary('../bad', '[Interface]\n[Peer]')

    def test_import_arguments(self):
        self.assertEqual(import_arguments('openvpn', '/tmp/a b.ovpn'),
                         ['nmcli', 'connection', 'import', 'type', 'openvpn', 'file', '/tmp/a b.ovpn'])
        with self.assertRaises(ValueError):
            import_arguments('--bad', 'secret')

    def root_module(self):
        specification = importlib.util.spec_from_file_location('vpn_root_test', ROOT / 'distro/system/eitr_vpn_root.py')
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        return module

    def test_wg_import_private_and_never_connects_by_default(self):
        import io
        import tempfile
        from types import SimpleNamespace
        module = self.root_module()
        payload = {'name': 'vpn0', 'kind': 'wireguard', 'backend': 'wg-quick',
                   'content': '[Interface]\nPrivateKey=SECRET\n[Peer]\nPublicKey=PUBLIC'}
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'wireguard'
            with patch.object(module, 'DIRECTORY', target), patch.object(module.sys, 'stdin', io.StringIO(json.dumps(payload))), \
                    patch.object(module.os, 'geteuid', return_value=0), \
                    patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=3)), \
                    patch.object(module, 'run') as run:
                # A temporary test directory belongs to the test user.
                with patch.object(module, 'trusted_directory', return_value=True):
                    module.dispatch('import')
                self.assertEqual((target / 'vpn0.conf').stat().st_mode & 0o777, 0o600)
                run.assert_not_called()

    def test_nm_import_disables_autoconnect_and_uses_uuid(self):
        import io
        from types import SimpleNamespace
        module = self.root_module()
        identifier = '12345678-1234-1234-1234-123456789abc'
        payload = {'name': 'vpn0', 'kind': 'openvpn', 'backend': 'networkmanager', 'content': 'secret'}
        with patch.object(module.sys, 'stdin', io.StringIO(json.dumps(payload))), \
                patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                patch.object(module, 'run', side_effect=[identifier, '']) as run:
            module.dispatch('import')
        self.assertEqual(run.call_count, 2)
        self.assertEqual(run.call_args_list[1].args[0], ['nmcli', 'connection', 'modify', 'uuid', identifier,
                          'connection.id', 'vpn0', 'connection.autoconnect', 'no'])
        self.assertNotIn('secret', str(run.call_args_list))

    def test_iwd_plugin_flow_never_installs(self):
        from types import SimpleNamespace
        specification = importlib.util.spec_from_file_location('vpn_flow_test', ROOT / 'walker/scripts/actions/install/vpn.py')
        module = importlib.util.module_from_spec(specification)
        software = SimpleNamespace(WALKER='/mock/walker')
        with patch.dict(sys.modules, {'software': software}):
            specification.loader.exec_module(module)
        with contextlib.redirect_stdout(io.StringIO()), \
                patch.object(module, 'networkmanager_active', return_value=False), \
                patch.object(module, 'read_key', return_value='\r'), \
                patch.object(module.subprocess, 'run') as run:
            module.main('networkmanager')
        run.assert_called_once_with(['/mock/walker', '-m', 'menus:network-backend'], check=True)
        with contextlib.redirect_stdout(io.StringIO()), \
                patch.object(module, 'networkmanager_active', return_value=False), \
                patch.object(module, 'read_key', return_value='\x1b'), \
                patch.object(module.subprocess, 'run') as run:
            module.main('networkmanager')
        run.assert_not_called()

    def test_nm_wireguard_is_converted_offline_before_loading(self):
        import io
        from types import SimpleNamespace
        module = self.root_module()
        payload = {'name': 'vpn0', 'kind': 'wireguard', 'backend': 'networkmanager',
                   'content': '[Interface]\nPrivateKey=SECRET\n[Peer]\nPublicKey=PUBLIC'}
        with patch.object(module.sys, 'stdin', io.StringIO(json.dumps(payload))), \
                patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                patch.object(module, 'import_nm_wireguard', return_value='uuid') as convert, \
                patch.object(module, 'run') as run:
            module.dispatch('import')
        convert.assert_called_once()
        run.assert_not_called()

    def test_non_vpn_connection_cannot_be_disconnected(self):
        import io
        from types import SimpleNamespace
        module = self.root_module()
        payload = {'name': 'ethernet', 'backend': 'networkmanager'}
        with patch.object(module.sys, 'stdin', io.StringIO(json.dumps(payload))), \
                patch.object(module.subprocess, 'run', return_value=SimpleNamespace(returncode=0)), \
                patch.object(module, 'run', return_value='802-3-ethernet') as run:
            with self.assertRaises(ValueError):
                module.dispatch('down')
        self.assertEqual(run.call_count, 1)

    def test_nm_keyfile_is_manual_and_private_before_daemon_load(self):
        import tempfile
        from types import SimpleNamespace
        from unittest.mock import Mock
        module = self.root_module()
        identifier = '12345678-1234-1234-1234-123456789abc'
        setting = Mock()
        setting.get_uuid.return_value = identifier
        connection = Mock()
        connection.get_setting_connection.return_value = setting
        keyfile = Mock()
        keyfile.to_data.return_value = ('[connection]\nautoconnect=false\n', 30)
        nm = SimpleNamespace(conn_wireguard_import=Mock(return_value=connection),
                             keyfile_write=Mock(return_value=keyfile),
                             KeyfileHandlerFlags=SimpleNamespace(NONE=0))
        gi = SimpleNamespace(require_version=Mock())
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            # Keep filesystem writes in the fixture while exercising the ownership check.
            original_stat = Path.stat

            def fixture_stat(path, **kwargs):
                result = original_stat(path, **kwargs)
                if path == target:
                    return SimpleNamespace(st_uid=0, st_mode=result.st_mode)
                return result

            def load(arguments):
                setting.set_property.assert_any_call('autoconnect', False)
                saved = Path(arguments[-1])
                self.assertEqual(saved.stat().st_mode & 0o777, 0o600)
                self.assertIn('autoconnect=false', saved.read_text())

            with patch.dict(sys.modules, {'gi': gi, 'gi.repository': SimpleNamespace(NM=nm)}), \
                    patch.object(module, 'NM_DIRECTORY', target), patch.object(module, 'run', side_effect=load), \
                    patch.object(Path, 'stat', fixture_stat):
                self.assertEqual(module.import_nm_wireguard('/mock/profile.conf', 'vpn0'), identifier)
