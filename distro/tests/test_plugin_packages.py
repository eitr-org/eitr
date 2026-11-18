"""Package declarations and privileged transaction boundaries with mocked pacman."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'lib'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'system'))
import eitr_plugin_packages as packages
import eitr_plugin_packages_root as root


class PackageTests(unittest.TestCase):
    def test_names(self):
        self.assertEqual(packages.names(['wireguard-tools', 'lib32-foo', 'a_b+1.2']), ['wireguard-tools', 'lib32-foo', 'a_b+1.2'])
        for value in ('foo', ['-flag'], ['repo/foo'], ['./foo'], ['https://foo'], ['a>=1'], ['a b'], ['a', 'a'], [None], ['a'] * 33):
            with self.subTest(value=value), self.assertRaises(ValueError):
                packages.names(value)

    def test_unavailable_aur_and_custom_repo_refused(self):
        with patch.object(packages, 'query', return_value=Mock(returncode=1)) as query:
            with self.assertRaises(ValueError):
                packages.repository('aur-only')
            self.assertEqual({call.args[1].split('/')[0] for call in query.call_args_list}, packages.REPOSITORIES)

    def test_review_and_install_record_only_missing(self):
        with patch.object(packages, 'repository', return_value='extra'), patch.object(packages, 'query', side_effect=[Mock(returncode=0), Mock(returncode=1)]):
            facts = packages.review({'packages': ['existing', 'missing']})
        self.assertEqual([item['installed'] for item in facts], [True, False])
        with patch.object(packages, 'review', return_value=facts), patch.object(packages, 'root') as privileged:
            self.assertEqual(packages.install({}, ['earlier']), ['earlier', 'missing'])
            privileged.assert_called_once_with('install', ['missing'])

    @staticmethod
    def pacman(database, removals):
        """A fake `pacman -Qi` / `pacman -Rsp` over {name: (reason, required_by, optional_for)}."""
        def query(*arguments):
            if arguments[0] == '-Rsp':
                return Mock(returncode=0, stdout='\n'.join(removals.get(arguments[-1], [arguments[-1]])) + '\n')
            blocks = []
            for name in arguments[2:]:
                if name in database:
                    reason, required, optional = database[name]
                    blocks.append(f'Name            : {name}\nRequired By     : {"  ".join(required) or "None"}\n'
                                  f'Optional For    : {"  ".join(optional) or "None"}\n'
                                  f'Install Reason  : {reason}\n')
            return Mock(returncode=0, stdout='\n'.join(blocks))
        return query

    def test_cleanup_includes_pulled_in_dependencies_and_keeps_what_others_use(self):
        dependency, explicit = packages.DEPENDENCY, 'Explicitly installed'
        # Real shape: networkmanager-openvpn pulled in its plugin, openvpn and libnma.
        database = {
            'networkmanager-openvpn': (dependency, [], []),
            'networkmanager-vpn-plugin-openvpn': (dependency, ['networkmanager-openvpn'], []),
            'openvpn': (dependency, ['networkmanager-vpn-plugin-openvpn'], []),
            'libnma': (dependency, ['networkmanager-vpn-plugin-openvpn'], ['other-app']),
            'shared-lib': (dependency, ['networkmanager-vpn-plugin-openvpn', 'firefox'], []),
            'my-tool': (explicit, ['networkmanager-vpn-plugin-openvpn'], []),
            'required': (dependency, ['app'], []),
        }
        removals = {'networkmanager-openvpn': ['networkmanager-openvpn', 'networkmanager-vpn-plugin-openvpn',
                                               'openvpn', 'libnma', 'shared-lib', 'my-tool']}
        with patch.object(packages, 'query', side_effect=self.pacman(database, removals)):
            self.assertEqual(packages.removable(['networkmanager-openvpn', 'required', 'shared'], ['shared']),
                             ['networkmanager-openvpn', 'networkmanager-vpn-plugin-openvpn', 'openvpn'])
            # libnma is optionally used, shared-lib required elsewhere, my-tool explicitly installed.
            trio = {'networkmanager-openvpn', 'networkmanager-vpn-plugin-openvpn', 'openvpn'}
            self.assertEqual(packages.closed(trio), trio)
            # Part of the set alone is refused: its requirers would stay behind.
            self.assertEqual(packages.closed(['openvpn']), set())

    def test_root_revalidates(self):
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root, 'repository', side_effect=ValueError('unknown')), patch.object(root.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                root.dispatch('install', io.StringIO('["unknown"]'))
            run.assert_not_called()
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                root.dispatch('install', io.StringIO('["--bad"]'))
            run.assert_not_called()

    def test_root_refuses_cleanup_when_package_became_required(self):
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root, 'closed', return_value=set()), patch.object(root.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                root.dispatch('remove', io.StringIO('["wireguard-tools"]'))
            run.assert_not_called()

    def test_root_removes_exactly_the_reviewed_closed_list(self):
        reviewed = ['networkmanager-openvpn', 'networkmanager-vpn-plugin-openvpn', 'openvpn']
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root, 'closed', return_value=set(reviewed)), \
                patch.object(root, 'repository') as repository, patch.object(root.subprocess, 'run') as run:
            root.dispatch('remove', io.StringIO(json.dumps(reviewed)))
        run.assert_called_once_with(['/usr/bin/pacman', '-R', '--noconfirm', '--', *reviewed], check=True)
        repository.assert_not_called()

    def test_root_does_not_reinstall_existing_package(self):
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root, 'repository', return_value='extra'), patch.object(root, 'query', return_value=Mock(returncode=0)), patch.object(root.subprocess, 'run') as run:
            root.dispatch('install', io.StringIO('["wireguard-tools"]'))
            run.assert_not_called()

    def test_root_filters_dependency_repositories(self):
        with patch.object(root.os, 'geteuid', return_value=0), patch.object(root, 'repository', return_value='extra'), patch.object(root, 'query', return_value=Mock(returncode=1)), patch.object(root.subprocess, 'check_output', return_value='[options]\nArchitecture = auto\n[extra]\nServer = https://official.invalid\n[custom]\nServer = https://custom.invalid\n'), patch.object(root.subprocess, 'run') as run:
            def inspect(command, **kwargs):
                content = Path(command[2]).read_text()
                self.assertNotIn('custom', content)
                self.assertIn('[extra]', content)
                self.assertEqual(command[-1], 'extra/wireguard-tools')
            run.side_effect = inspect
            root.dispatch('install', io.StringIO(json.dumps(['wireguard-tools'])))


if __name__ == '__main__':
    unittest.main()
