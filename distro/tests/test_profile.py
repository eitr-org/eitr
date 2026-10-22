"""Organization profile boundaries, without touching the host."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'distro/lib'))


class RemovablePackages(unittest.TestCase):
    def test_protected_packages_are_never_removable(self):
        reviewed = json.loads((ROOT / 'distro/removable-apps.json').read_text())
        protected = {'eitr-desktop', 'eitr-artwork'}
        for manifest in ('packages.txt', 'aur-packages.txt', 'local-packages.txt'):
            protected.update(line.split('#')[0].strip() for line in
                             (ROOT / 'distro' / manifest).read_text().splitlines())
        protected.discard('eitr-sunshine')
        protected.discard('')
        protected.update(profile.protected_packages({'eitr-desktop': ['desktop-support'],
                                                     'desktop-support': ['bash>=5']}))
        self.assertIn('bash', protected)
        self.assertIn('desktop-support', protected)
        self.assertFalse(protected.intersection(reviewed))
        for package, review in reviewed.items():
            self.assertTrue(review['reason'], package)
        self.assertTrue({'eitr-sunshine', 'moonlight-qt', 'tailscale'} <= reviewed.keys())


import hashlib
import importlib.util
import subprocess
import tempfile
from unittest.mock import patch, Mock
import eitr_profile as profile
import eitr_policy as policy


def module(name, relative):
    specification = importlib.util.spec_from_file_location(name, ROOT / relative)
    loaded = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(loaded)
    return loaded


class ProfileFormat(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.drive = Path(self.temporary.name)
        self.value = {'version': 1, 'name': 'Office'}

    def validate(self, **values):
        self.value.update(values)
        (self.drive / 'eitr-profile.json').write_text(json.dumps(self.value))
        return profile.validate(self.drive)

    def file(self, name, content=b'example'):
        (self.drive / name).write_bytes(content)
        return {'file': name, 'sha256': hashlib.sha256(content).hexdigest()}

    def test_minimal_and_summary(self):
        selected = self.validate()
        self.assertIn('Office', profile.summary(selected))
        self.assertIn('first start with a network connection', profile.summary(selected, installer=True))
        self.assertNotIn('first start', profile.summary(selected))

    def test_unknown_and_duplicate_keys_refused(self):
        with self.assertRaisesRegex(profile.ProfileError, 'unknown keys'):
            self.validate(surprise=True)
        (self.drive / 'eitr-profile.json').write_text('{"version":1,"name":"A","name":"B"}')
        with self.assertRaisesRegex(profile.ProfileError, 'Duplicate'):
            profile.validate(self.drive)

    def test_protected_and_unknown_package_refused(self):
        for package in ('hyprland', 'eitr-desktop', 'eitr-artwork', 'eitr-cmux-tui-bin', 'not-an-eitr-app'):
            with self.subTest(package=package), self.assertRaisesRegex(profile.ProfileError, 'Protected or unknown'):
                self.validate(remove=[package])

    def test_recipe_refusals(self):
        for recipe in ('gaming/unknown', 'browsers/chrome', 'languages/java'):
            with self.subTest(recipe=recipe), self.assertRaises(profile.ProfileError):
                self.validate(add={'recipes': [recipe]})

    def test_checksum_missing_file_and_unsafe_paths(self):
        entry = self.file('setup.sh')
        self.validate(setup=entry)
        for change in ({'sha256': 'x'*64}, {'sha256': '0'*64}, {'file': 'missing'},
                       {'file': '../escape'}, {'file': '/etc/passwd'}, {'file': './setup.sh'}):
            with self.subTest(change=change), self.assertRaises(profile.ProfileError):
                self.validate(setup={**entry, **change})
        (self.drive / 'linked').symlink_to(self.drive / 'setup.sh')
        with self.assertRaisesRegex(profile.ProfileError, 'symlinks'):
            self.validate(setup={**entry, 'file': 'linked'})

    def test_policy_conflicts_and_types(self):
        with self.assertRaises(profile.ProfileError):
            self.validate(policies={'remote_access': 'false'})
        with self.assertRaises(profile.ProfileError):
            self.validate(policies={'update_channel': 'stable'}, defaults={'update_channel': 'testing'})
        self.value = {'version': 1, 'name': 'Office'}
        with self.assertRaisesRegex(profile.ProfileError, 'also removed'):
            self.validate(remove=['steam'], add={'packages': ['steam']})

    def test_group_policy_excludes_all_group_packages(self):
        result = self.validate(policies={'remote_access': False, 'gaming': False})
        self.assertTrue({'eitr-sunshine', 'moonlight-qt', 'tailscale', 'steam'} <= profile.removals(result))

    def test_unknown_nested_keys_and_bad_types(self):
        for values in ({'add': {'oops': []}}, {'defaults': {'oops': True}}, {'policies': {'oops': False}},
                       {'remove': 'steam'}, {'add': {'files': {}}}, {'version': True}):
            self.value = {'version': 1, 'name': 'Office'}
            with self.subTest(values=values), self.assertRaises(profile.ProfileError):
                self.validate(**values)

    def test_repository_requires_https_and_real_key(self):
        key = self.file('key.asc')
        for server in ('http://example.org/$arch', 'https://user:pass@example.org', 'https://example.org/\n[evil]'):
            with self.assertRaises(profile.ProfileError):
                self.validate(defaults={'repository': {'name': 'office', 'server': server, 'key': key}})
        with self.assertRaisesRegex(profile.ProfileError, 'OpenPGP'):
            self.validate(defaults={'repository': {'name': 'office', 'server': 'https://example.org/$arch', 'key': key}})

    def test_snapshot_rechecks_copied_files(self):
        self.validate(setup=self.file('setup.sh'))
        with tempfile.TemporaryDirectory() as destination:
            staged = profile.snapshot(self.drive, destination)
            self.assertEqual(staged, self.value)
            self.assertEqual((Path(destination)/'setup.sh').read_bytes(), b'example')

    def test_unknown_repository_package_is_read_only_refusal(self):
        selected = self.validate(add={'packages': ['unknown-package']})
        run = Mock(return_value=Mock(returncode=1, stderr='not found'))
        with self.assertRaisesRegex(profile.ProfileError, 'Unknown or unavailable'):
            profile.preflight_packages(selected, self.drive, run)
        self.assertEqual(run.call_args.args[0][:2], ['pacman', '-Si'])

    def test_unknown_flatpak_is_refused_with_an_isolated_home(self):
        selected = self.validate(add={'flathub': ['org.example.Unknown']})
        run = Mock(side_effect=[Mock(returncode=0), Mock(returncode=1, stderr='not found')])
        with self.assertRaisesRegex(profile.ProfileError, 'Unknown or unavailable Flatpak'):
            profile.preflight_flatpaks(selected, run)
        self.assertEqual(run.call_args.args[0][:2], ['flatpak', 'remote-info'])
        environment = run.call_args.kwargs['env']
        self.assertTrue(environment['XDG_DATA_HOME'].startswith(environment['HOME'] + '/'))
        self.assertEqual(environment['DBUS_SESSION_BUS_ADDRESS'], 'unix:path=/nonexistent')
        self.assertFalse(Path(environment['HOME']).exists())


class StickPackages(unittest.TestCase):
    """pacman -Qp prints "name version"; an earlier check passed an option it rejects."""
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.drive = Path(folder.name)
        (self.drive / 'packages').mkdir()
        (self.drive / 'packages/tool.pkg.tar.zst').write_bytes(b'not a package')
        self.profile = {'add': {'files': [{'file': 'packages/tool.pkg.tar.zst', 'sha256': '0' * 64}]}}

    def test_package_name_comes_from_pacman_query(self):
        answer = Mock(returncode=0, stdout='office-tools 1-1\n', stderr='')
        run = Mock(return_value=answer)
        profile.preflight_packages(self.profile, self.drive, run=run)
        self.assertEqual(run.call_args.args[0][:3], ['pacman', '-Qp', '--'])
        removed = {**self.profile, 'remove': ['office-tools']}
        with patch.object(profile, 'removals', return_value={'office-tools'}):
            with self.assertRaisesRegex(Exception, 'also removed'):
                profile.preflight_packages(removed, self.drive, run=run)

    @unittest.skipUnless(Path('/usr/bin/pacman').exists(), 'pacman required')
    def test_real_pacman_refuses_a_file_that_is_not_a_package(self):
        with self.assertRaisesRegex(Exception, 'Invalid package archive'):
            profile.preflight_packages(self.profile, self.drive)


class PolicyEnforcement(unittest.TestCase):
    def test_menu_rows_and_tools_both_refuse_remote_access(self):
        menus = module('profile_menu_actions', 'quickshell/desktop-bar/scripts/menu-action.py')
        remote = module('profile_remote', 'walker/scripts/actions/system/remote-access.py')
        root_remote = module('profile_root_remote', 'distro/system/eitr_remote.py')
        with patch.object(policy, 'load', return_value={'remote_access': False}):
            for menu in ('remote-access', 'remote-away', 'remote-share'):
                for row in menus.rows(menu):
                    self.assertFalse(policy.row_allowed({**row, 'provider': 'menus:' + menu}))
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                menus.command('remote-share', 'Start Sharing')
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                remote.main(['host', 'start'])
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                root_remote.dispatch('setup', 'tester')
            # Shutting remote access down is never refused.
            with patch.object(root_remote, 'sharing') as sharing:
                root_remote.dispatch('close', 'tester')
            sharing.assert_called_once_with('tester', False)
            with patch.object(remote, 'run'), patch.object(remote, 'root'):
                remote.main(['host', 'stop'])

    def test_channel_menu_and_root_tool_refuse_testing(self):
        helper = module('profile_root_helper', 'distro/system/eitr-system.py')
        with patch.object(policy, 'load', return_value={'update_channel': 'stable'}):
            self.assertFalse(policy.row_allowed({'submenu': 'update-channel'}))
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                helper.channel_set('testing')

    def test_assistants_menu_and_enable_refused(self):
        eitr_collaboration = module('profile_collaboration', 'distro/lib/eitr_collaboration.py')
        with patch.object(policy, 'load', return_value={'assistants_together': False}):
            self.assertFalse(policy.row_allowed({'text': 'Let assistants work together'}))
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                eitr_collaboration.enable(['codex'])
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                eitr_collaboration.dispatch({'jsonrpc': '2.0', 'method': 'tools/list', 'id': 1})

    def test_group_recipes_and_direct_install_refused(self):
        software = module('profile_software', 'walker/scripts/actions/install/software.py')
        with patch.object(policy, 'load', return_value={'gaming': False}), patch.object(policy, 'excluded', return_value=set()):
            self.assertFalse(policy.row_allowed({'submenu': 'gaming'}))
            self.assertEqual(software.recipes('gaming'), [])
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                software.recipe('gaming', 'steam')
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                software.install('pacman', ['steam'])

    def test_recorded_removals_block_tools_even_without_group_policy(self):
        with patch.object(policy, 'load', return_value={}), patch.object(policy, 'excluded', return_value={'moonlight-qt'}):
            with self.assertRaisesRegex(ValueError, 'Disabled'):
                policy.require_packages(['moonlight-qt'])

    def test_lua_filters_actual_rows(self):
        import subprocess
        script = '''
local policies = dofile('elephant/policies.lua')
policies.allowed = function(feature) return false end
for _, menu in ipairs({'remote-access', 'remote-away', 'remote-share', 'gaming', 'update-channel'}) do
    assert(#policies.filter({{Text='Example', Actions={open='command'}}}, menu) == 0, menu)
end
assert(#policies.filter({{Text='Let assistants work together'}}, 'ai-tools') == 0)
assert(#policies.filter({{Text='Example', SubMenu='remote-access'}}, 'shortcuts') == 0)
'''
        subprocess.run(['lua', '-'], input=script, text=True, check=True, cwd=ROOT)


class ProfileApplication(unittest.TestCase):
    def test_apply_records_exclusions_and_runs_setup_only_once(self):
        import eitr_profile_apply
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'etc').mkdir()
            (root / 'etc/pacman.conf').write_text('[options]\n[core]\nServer = https://example.org\n')
            drive = root / 'stick'
            drive.mkdir()
            (drive / 'setup.sh').write_text('exit 0\n')
            selected = {'version': 1, 'name': 'Office', 'remove': ['steam'],
                        'policies': {'remote_access': False},
                        'setup': {'file': 'setup.sh', 'sha256': 'a' * 64}}
            runner = Mock()
            account = Mock(pw_uid=1000, pw_dir=str(root / 'home'))
            with patch.object(eitr_profile_apply.pwd, 'getpwnam', return_value=account), \
                 patch.object(eitr_profile_apply.subprocess, 'run', return_value=Mock(stdout='steam\nfirefox\n')), \
                 patch.object(eitr_profile_apply.os, 'fchown'):
                for attempt in range(2):
                    eitr_profile_apply.execute(selected, drive, 'tester', Mock(), runner=runner, root=root)
            self.assertEqual(json.loads((root/'etc/eitr/profile.json').read_text()), selected)
            policies = root/'etc/eitr/policies.json'
            self.assertEqual(policies.stat().st_mode & 0o777, 0o644)
            self.assertEqual(json.loads(policies.read_text()), selected['policies'])
            commands = [call.args[0] for call in runner.call_args_list]
            self.assertEqual(commands.count(['/bin/bash', str(drive/'setup.sh')]), 1)
            self.assertIn(['pacman', '-R', '--noconfirm', '--', 'steam'], commands)
            self.assertEqual((root/'etc/eitr/profile-pacman.conf').read_text(), 'IgnorePkg = eitr-sunshine moonlight-qt steam tailscale\n')
            self.assertEqual((root/'etc/pacman.conf').read_text().count('Include = /etc/eitr/profile-pacman.conf'), 1)

    def test_cancellation_never_reaches_executor(self):
        import eitr_profile_apply
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root/'run').mkdir()
            (root/'etc').mkdir()
            (root/'etc/pacman.conf').write_text('[options]\n')
            drive = root/'stick'
            drive.mkdir()
            (drive/'eitr-profile.json').write_text('{"version":1,"name":"Office"}')
            with patch.object(eitr_profile_apply.os, 'geteuid', return_value=0), \
                 patch.object(eitr_profile_apply.pwd, 'getpwnam', return_value=Mock(pw_uid=1000)), \
                 patch('builtins.input', return_value='wrong'), \
                 patch.object(eitr_profile_apply, 'execute') as execute:
                with self.assertRaisesRegex(ValueError, 'Cancelled'):
                    eitr_profile_apply.apply(drive, Mock(), username='tester', root=root)
                execute.assert_not_called()
            self.assertFalse((root/'etc/eitr').exists())

    def test_invalid_profile_never_reaches_executor(self):
        import eitr_profile_apply
        with tempfile.TemporaryDirectory() as temporary:
            drive = Path(temporary)
            (drive/'eitr-profile.json').write_text('{"version":1,"name":"Unsafe","remove":["hyprland"]}')
            with patch.object(eitr_profile_apply.os, 'geteuid', return_value=0), \
                 patch.object(eitr_profile_apply.pwd, 'getpwnam', return_value=Mock(pw_uid=1000)), \
                 patch.object(eitr_profile_apply.tempfile, 'TemporaryDirectory', return_value=tempfile.TemporaryDirectory(dir=temporary)), \
                 patch.object(eitr_profile_apply, 'execute') as execute:
                with self.assertRaisesRegex(profile.ProfileError, 'Protected'):
                    eitr_profile_apply.apply(drive, Mock(), username='tester')
                execute.assert_not_called()


class DeferredFlatpaks(unittest.TestCase):
    def setUp(self):
        import eitr_profile_apply
        self.apply = eitr_profile_apply
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        (self.root / 'etc').mkdir()
        (self.root / 'etc/pacman.conf').write_text('[options]\n')
        self.account = Mock(pw_uid=1000, pw_dir=str(self.root / 'home'), pw_shell='/bin/bash')
        self.pending = self.root / self.apply.PENDING
        self.work = [{'name': 'flathub', 'url': 'https://dl.flathub.org/repo/flathub.flatpakrepo',
                      'apps': ['us.zoom.Zoom']}]

    def queue(self):
        self.pending.parent.mkdir(parents=True, exist_ok=True)
        self.pending.write_text(json.dumps({'user': 'tester', 'remotes': self.work}))
        self.pending.chmod(0o600)

    def finish(self, runner):
        actual_fstat = self.apply.os.fstat
        def root_metadata(descriptor):
            metadata = actual_fstat(descriptor)
            return Mock(st_mode=metadata.st_mode, st_uid=0, st_gid=0,
                        st_nlink=metadata.st_nlink, st_size=metadata.st_size)
        with patch.object(self.apply.pwd, 'getpwnam', return_value=self.account), \
             patch.object(self.apply.os, 'fstat', side_effect=root_metadata):
            self.apply.finish_flatpaks(root=self.root, runner=runner)

    def test_installer_queues_both_sources_but_installed_machine_runs_directly(self):
        selected = {'version': 1, 'name': 'Office',
                    'add': {'flathub': ['us.zoom.Zoom'], 'recipes': ['example']}}
        recipe = {'source': 'flatpak', 'remote': 'vendor', 'url': 'https://example.org/repo',
                  'packages': ['org.example.App'],
                  'runtime_remotes': [{'name': 'runtime', 'url': 'https://example.org/runtime'}]}
        with patch.object(self.apply.pwd, 'getpwnam', return_value=self.account), \
             patch.object(self.apply.profiles, 'recipes', return_value={'example': recipe}), \
             patch.object(self.apply.subprocess, 'run', return_value=Mock(stdout='')), \
             patch.object(self.apply.os, 'fchown'):
            runner = Mock()
            self.apply.execute(selected, self.root, 'tester', Mock(), runner=runner,
                               root=self.root, installer=True)
            commands = [call.args[0] for call in runner.call_args_list]
            self.assertFalse(any('flatpak' in command for command in commands))
            self.assertIn(['systemctl', 'enable', 'eitr-profile-flatpaks.timer'], commands)
            queued = json.loads(self.pending.read_text())
            self.assertEqual(queued['user'], 'tester')
            self.assertEqual([remote['name'] for remote in queued['remotes']], ['flathub', 'runtime', 'vendor'])
            self.assertEqual(queued['remotes'][2]['apps'], ['org.example.App'])
            self.assertEqual(self.pending.stat().st_mode & 0o777, 0o600)
            runner.reset_mock()
            self.apply.execute(selected, self.root, 'tester', Mock(), runner=runner, root=self.root)
            commands = [call.args[0] for call in runner.call_args_list]
            self.assertEqual(sum('install' in command and 'flatpak' in command for command in commands), 2)
            self.assertFalse(any(command[0] == 'systemctl' for command in commands))

    def test_installer_without_flatpaks_does_not_enable_unit(self):
        runner = Mock()
        with patch.object(self.apply.pwd, 'getpwnam', return_value=self.account), \
             patch.object(self.apply.subprocess, 'run', return_value=Mock(stdout='')), \
             patch.object(self.apply.os, 'fchown'):
            self.apply.execute({'version': 1, 'name': 'Office'}, self.root, 'tester', Mock(),
                               runner=runner, root=self.root, installer=True)
        self.assertFalse(self.pending.exists())
        runner.assert_not_called()

    def test_malformed_records_and_duplicate_keys_are_refused(self):
        for content in ('[]', '{', '{"user":"tester","remotes":[]}',
                        '{"user":"tester","user":"root","remotes":[]}'):
            self.queue()
            self.pending.write_text(content)
            runner = Mock()
            with self.assertRaises(ValueError):
                self.finish(runner)
            runner.assert_not_called()
            self.assertTrue(self.pending.exists())

    def test_success_removes_queue_and_uses_clean_user_environment(self):
        self.queue()
        runner = Mock()
        self.finish(runner)
        self.assertFalse(self.pending.exists())
        command = runner.call_args.args[0]
        self.assertEqual(command[:7], ['runuser', '-u', 'tester', '--', 'env', '-i', f'HOME={self.account.pw_dir}'])
        self.assertEqual(command[-6:], ['flatpak', 'install', '--user', '-y', 'flathub', 'us.zoom.Zoom'])

    def test_failure_retains_queue(self):
        self.queue()
        with self.assertRaises(RuntimeError):
            self.finish(Mock(side_effect=[None, RuntimeError('download failed')]))
        self.assertTrue(self.pending.exists())

    def test_offline_is_a_quiet_retry(self):
        # No network yet must not fail the unit (a degraded system); the timer retries.
        self.queue()
        failing = Mock(side_effect=subprocess.CalledProcessError(1, 'flatpak'))
        with patch('builtins.print'):
            self.finish(failing)
        self.assertTrue(self.pending.exists())

    def test_the_timer_retries_until_the_queue_is_gone(self):
        timer = (ROOT / 'distro/system/eitr-profile-flatpaks.timer').read_text()
        self.assertIn('OnBootSec=1min', timer)
        self.assertIn('OnUnitInactiveSec=5min', timer)
        self.assertIn('ConditionPathExists=/var/lib/eitr/profile-flatpaks.json', timer)

    def test_invalid_data_is_rejected_before_any_command(self):
        for field, value in [('url', 'http://example.org'), ('name', '--evil'),
                             ('apps', ['--command=evil']), ('apps', 'us.zoom.Zoom')]:
            with self.subTest(field=field, value=value):
                self.queue()
                pending = json.loads(self.pending.read_text())
                pending['remotes'].append(dict(self.work[0], **{field: value}))
                self.pending.write_text(json.dumps(pending))
                runner = Mock()
                with self.assertRaises(ValueError):
                    self.finish(runner)
                runner.assert_not_called()
                self.assertTrue(self.pending.exists())
        self.queue()
        self.account.pw_uid = 0
        with self.assertRaises(ValueError):
            self.finish(Mock())

    def test_tampered_permissions_owner_and_symlink_refused(self):
        self.queue()
        self.pending.chmod(0o644)
        with self.assertRaises(ValueError):
            self.finish(Mock())
        self.queue()
        with patch.object(self.apply.os, 'fstat', return_value=Mock(
                st_mode=0o100600, st_uid=1000, st_gid=1000, st_size=100, st_nlink=1)):
            with self.assertRaises(ValueError):
                self.apply.finish_flatpaks(root=self.root, runner=Mock())
        target = self.pending.with_suffix('.target')
        self.pending.rename(target)
        self.pending.symlink_to(target)
        with self.assertRaises(OSError):
            self.apply.finish_flatpaks(root=self.root, runner=Mock())


if __name__ == '__main__':
    unittest.main()
