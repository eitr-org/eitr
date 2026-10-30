"""All PC-check evidence is mocked; no host queries, privileges or services."""
import contextlib
import importlib.machinery
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, patch

import eitr_selfcheck as check

ROOT = Path(__file__).resolve().parents[2]


class Evidence(check.Context):
    def __init__(self, files=None, commands=None, globs=None, disks=None):
        self.state = Path('/fixture-state')
        self.files = files or {}
        self.commands = commands or {}
        self.globs = globs or {}
        self.disks = disks or {}
        self.calls = []

    def read(self, path):
        if str(path) not in self.files:
            raise check.Unavailable('fixture file missing or unreadable')
        return self.files[str(path)]

    def read_bytes(self, path):
        return self.read(path).encode('latin-1')

    def exists(self, path):
        return str(path) in self.files

    def glob(self, pattern):
        return self.globs.get(pattern, [])

    def disk(self, path):
        if path not in self.disks:
            raise check.Unavailable('fixture filesystem missing')
        return self.disks[path]

    def now(self):
        return 1793000000

    def run(self, *arguments, allowed=(0,), **kwargs):
        self.calls.append((arguments, kwargs))
        if arguments not in self.commands:
            raise check.Unavailable('fixture tool missing')
        status, output = self.commands[arguments]
        if status not in allowed:
            raise check.Unavailable('fixture query refused')
        return status, output


def load_cli():
    loader = importlib.machinery.SourceFileLoader('selfcheck_cli', str(ROOT / 'distro/bin/eitr'))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class SelfcheckTests(unittest.TestCase):
    def assert_status(self, function, fixture, expected):
        actual = function(fixture)
        self.assertEqual(actual[0], expected, actual)
        if expected in ('warning', 'problem'):
            self.assertTrue(actual[2], actual)
        return actual

    def test_all_missing_checks_skip_independently(self):
        with patch('eitr_plugins.Plugins') as plugins:
            results = check.collect(Evidence())
            plugins.assert_not_called()
        self.assertEqual(len(results), len(check.CHECKS))
        self.assertTrue(all(item.status == 'skipped' for item in results))
        self.assertTrue(all(item.message and item.source for item in results))

    def test_each_check_still_runs_after_bad_input(self):
        for error in (OSError('unreadable'), ValueError('bad format'), KeyError('missing field')):
            with self.subTest(error=error), patch.object(check, 'CHECKS', [
                ('Fixture', 'bad', Mock(side_effect=error), 'fixture'),
                ('Fixture', 'good', Mock(return_value=('ok', 'healthy', '')), 'fixture')
            ]):
                checks = check.collect(Evidence())
                self.assertEqual([item.status for item in checks[:2]], ['skipped', 'ok'])

    def test_deeper_merge_and_action(self):
        from test_system_safety import system
        self.assertIn('selfcheck-deeper', system.READ_ONLY_ACTIONS)
        payload = check.collect_deeper(Evidence())
        self.assertEqual({entry['name'] for entry in payload['checks']}, check.DEEP_NAMES)
        original = [check.Result('Recovery', 'snapper', 'skipped', 'permission', 'mock'),
                    check.Result('Recovery', 'boot-guard', 'ok', 'keep', 'mock')]
        merged = check.merge_deeper(original, payload)
        self.assertEqual(next(entry for entry in merged if entry.name == 'boot-guard').message, 'keep')
        self.assertEqual(len({entry.name for entry in merged}), len(merged))
        with patch.object(check, 'collect_deeper', return_value=payload), contextlib.redirect_stdout(io.StringIO()) as output:
            system.selfcheck_deeper()
        self.assertEqual(json.loads(output.getvalue()), payload)
        with self.assertRaises(ValueError):
            check.merge_deeper(original, {'checks': []})

    def test_esp_never_checks_writable_mount(self):
        device = '/dev/fixture'
        fixture = Evidence(commands={
            ('lsblk', '--json', '--paths', '--output', 'PATH,PARTTYPE,FSTYPE'): (0, json.dumps({'blockdevices': [
                {'path': device, 'parttype': 'c12a7328-f81f-11d2-ba4b-00a0c93ec93b', 'fstype': 'vfat'}]})),
            ('findmnt', '-rn', '-S', device, '-o', 'OPTIONS'): (0, 'rw,relatime')})
        with self.assertRaisesRegex(check.Unavailable, 'unmounted'):
            check.check_esp_filesystem(fixture)
        self.assertFalse(any(arguments[0] == 'fsck.vfat' for arguments, _ in fixture.calls))
        fixture.commands[('findmnt', '-rn', '-S', device, '-o', 'OPTIONS')] = (1, '')
        fixture.commands[('fsck.vfat', '-n', device)] = (0, '')
        self.assert_status(check.check_esp_filesystem, fixture, 'ok')

    def test_keyring_expiry_and_failed_unit_names(self):
        fingerprint = 'A' * 40
        fixture = Evidence(files={f'/usr/share/pacman/keyrings/{ring}-trusted': fingerprint + ':4:' for ring in ('archlinux', 'eitr')},
            commands={('pacman-key', '--list-keys', fingerprint):
                (0, 'pub rsa4096 2026-01-01 [SC]\n' + fingerprint)})
        self.assert_status(check.check_keyring, fixture, 'ok')
        fixture.commands[('pacman-key', '--list-keys', fingerprint)] = (0, 'pub rsa4096 2026-01-01 [SC] [expired: 2026-01-02]\n' + fingerprint)
        self.assert_status(check.check_keyring, fixture, 'warning')
        arguments = ('systemctl', '--user', '--failed', '--no-legend', '--plain', '--no-pager')
        answer = check.check_user_units(Evidence(commands={arguments: (0, 'broken.service loaded failed failed')}))
        self.assertIn('1 failed unit: broken.service.', answer[1])
        self.assertIn('systemctl --user status broken.service', answer[2])
        answer = check.check_user_units(Evidence(commands={arguments: (0, '\n'.join(f'unit{number}.service failed' for number in range(5)))}))
        self.assertIn('and 2 more', answer[1])
        self.assertNotIn('unit3.service', answer[1])

    def test_permission_reasons_keep_details_only_in_json(self):
        for error in (PermissionError('denied'),):
            with patch.object(subprocess, 'run', side_effect=error):
                with self.assertRaisesRegex(check.Unavailable, 'needs your password'):
                    check.Context().run('snapper')
        completed = subprocess.CompletedProcess([], 1, '', 'Operation not permitted: private detail')
        with patch.object(subprocess, 'run', return_value=completed):
            with self.assertRaises(check.Unavailable) as caught:
                check.Context().run('snapper')
        entry = check.Result('Recovery', 'snapper', 'skipped', str(caught.exception), 'snapper')
        self.assertIn('private detail', entry.message)
        self.assertIn('needs your password: run deeper checks', check.plain([entry]))
        self.assertNotIn('private detail', check.plain([entry]))

    def test_deeper_prompt_merges_and_copies_without_running_sudo(self):
        original = [check.Result('Recovery', 'snapper', 'skipped', 'permission', 'mock')]
        payload = check.collect_deeper(Evidence())
        next(entry for entry in payload['checks'] if entry['name'] == 'snapper').update(
            status='ok', message='Root Snapper configuration is readable.')
        report = Mock()
        report.redact.side_effect = lambda text: text
        with patch.object(check, 'collect', return_value=original), \
             patch.object(check, 'deeper_checks', return_value=payload) as deeper, \
             patch.object(check, 'report_module', return_value=report), \
             patch.object(check.sys.stdin, 'isatty', return_value=True), \
             patch.object(check, 'read_key', side_effect=['\r', '\r', '\x1b']), \
             contextlib.redirect_stdout(io.StringIO()) as output:
            check.main([])
        deeper.assert_called_once_with()
        self.assertIn('Root Snapper configuration is readable.', output.getvalue())
        self.assertIn('Root Snapper configuration is readable.', report.copy.call_args.args[0])

    def test_kernel_for_every_gpu(self):
        for vendor in ('0x1002', '0x8086', '0x10de', '0x1af4'):
            for release, expected in (('new', 'ok'), ('old', 'warning')):
                fixture = Evidence(commands={('uname', '-r'): (0, release)},
                                   globs={'/usr/lib/modules/*/pkgbase': ['/usr/lib/modules/new/pkgbase']})
                self.assert_status(check.check_kernel, fixture, expected)
        with self.assertRaises(check.Unavailable):
            check.check_kernel(Evidence(commands={('uname', '-r'): (0, 'old')}))

    def graphics_fixture(self, vendor):
        return Evidence(files={'/pci/class': '0x030000', '/pci/vendor': vendor},
                        globs={'/sys/bus/pci/devices/*': ['/pci']})

    def test_nvidia_only_and_version_comparison(self):
        fixture = self.graphics_fixture('0x10de')
        fixture.files['/sys/module/nvidia/version'] = '580.1'
        fixture.commands[('pacman', '-Q', 'nvidia-utils')] = (0, 'nvidia-utils 580.1-2')
        self.assert_status(check.check_nvidia, fixture, 'ok')
        fixture.files['/sys/module/nvidia/version'] = '570.1'
        self.assert_status(check.check_nvidia, fixture, 'warning')
        for vendor in ('0x1002', '0x8086', '0x1af4'):
            with self.assertRaises(check.Unavailable):
                check.check_nvidia(self.graphics_fixture(vendor))
        fixture.files.pop('/sys/module/nvidia/version')
        with self.assertRaises(check.Unavailable):
            check.check_nvidia(fixture)

    def test_amd_intel_restart_and_hybrid(self):
        for vendor in ('0x1002', '0x8086'):
            fixture = self.graphics_fixture(vendor)
            fixture.files['/proc/uptime'] = '3600 100'
            fixture.files['/var/log/pacman.log'] = ''
            self.assert_status(check.check_graphics, fixture, 'ok')
            for package in ('mesa', 'lib32-mesa', 'linux-firmware-amdgpu'):
                fixture.files['/var/log/pacman.log'] = f'[2026-10-26T07:13:20+00:00] [ALPM] upgraded {package} (1 -> 2)'
                self.assert_status(check.check_graphics, fixture, 'warning')
            fixture.files['/var/log/pacman.log'] = '[2020-01-01T00:00:00+00:00] [ALPM] upgraded mesa (1 -> 2)'
            self.assert_status(check.check_graphics, fixture, 'ok')
        fixture = self.graphics_fixture('0x10de')
        fixture.globs['/sys/bus/pci/devices/*'].append('/integrated')
        fixture.files.update({'/integrated/class': '0x030000', '/integrated/vendor': '0x8086',
                              '/proc/uptime': '1000', '/var/log/pacman.log': ''})
        self.assert_status(check.check_graphics, fixture, 'ok')
        with self.assertRaises(check.Unavailable):
            check.check_graphics(self.graphics_fixture('0x10de'))

    def test_root_and_esp_thresholds(self):
        mib = 1048576
        for free, expected in ((1000, 'ok'), (999, 'warning')):
            self.assert_status(check.check_root_space, Evidence(disks={'/': (10000, 0, free)}), expected)
        for total, free, expected in ((1000, 150, 'ok'), (1000, 149, 'warning'),
                                      (500, 99, 'warning'), (500, 100, 'ok')):
            fixture = Evidence(commands={('findmnt', '-n', '-o', 'FSTYPE', '-M', '/boot'): (0, 'vfat')},
                               disks={'/boot': (total * mib, 0, free * mib)})
            self.assert_status(check.check_esp_space, fixture, expected)
        fixture = Evidence(commands={('findmnt', '-n', '-o', 'FSTYPE', '-M', mount): (1, '')
                                     for mount in ('/boot', '/efi', '/boot/efi')})
        with self.assertRaises(check.Unavailable):
            check.check_esp_space(fixture)

    def recovery_fixture(self, rows):
        return Evidence(commands={('findmnt', '-n', '-o', 'FSTYPE', '-T', '/'): (0, 'btrfs'),
                                  ('snapper', '--no-dbus', '--logger-type', 'none', '--csvout', '--separator', ',',
                                   '--no-headers', '--iso', '-c', 'root', 'list', '--columns',
                                   'number,pre-number,date,description'): (0, rows)})

    def test_snapshot_space_excludes_unrelated_subvolumes(self):
        fixture = self.recovery_fixture('')
        fixture.commands[('btrfs', 'qgroup', 'show', '--raw', '/.snapshots')] = (0, '0/1 99999999 99999999\n0/2 1048576 524288\n')
        fixture.commands[('btrfs', 'subvolume', 'list', '-o', '/.snapshots')] = (0, 'ID 2 gen 4 top level 5 path @/.snapshots/1/snapshot')
        answer = self.assert_status(check.check_snapshot_space, fixture, 'info')
        self.assertIn('1 MiB referenced', answer[1])
        fixture.commands[('findmnt', '-n', '-o', 'FSTYPE', '-T', '/')] = (0, 'ext4')
        with self.assertRaises(check.Unavailable):
            check.check_snapshot_space(fixture)

    def test_snapper_pairs_and_last_success(self):
        fixture = self.recovery_fixture('1,,2026-10-01,Eitr before package upgrade\n2,1,2026-10-01,Eitr after package upgrade\n3,1,2026-10-02,Eitr after failed package upgrade')
        self.assert_status(check.check_snapper, fixture, 'ok')
        self.assert_status(check.check_snapshot_pair, fixture, 'ok')
        last = self.assert_status(check.check_last_update, fixture, 'info')
        self.assertIn('2026-10-01', last[1])
        self.assertNotIn('2026-10-02', last[1])
        self.assert_status(check.check_snapshot_pair, self.recovery_fixture(''), 'warning')
        with self.assertRaises(check.Unavailable):
            check.check_last_update(self.recovery_fixture(''))

    def test_recovery_records_never_mount(self):
        self.assert_status(check.check_boot_guard, Evidence(files={'/var/lib/eitr/boot-guard.json': '{"snapshot":"42"}'}), 'info')
        fixture = Evidence(commands={('findmnt', '--json', '-o', 'TARGET,FSROOT,FSTYPE'):
                                     (0, '{"filesystems":[{"target":"/fixture", "fsroot":"/@eitr-factory"}]}')},
                           files={'/fixture/manifest.json': '{"version":1}'})
        self.assert_status(check.check_factory, fixture, 'info')
        self.assertEqual(len(fixture.calls), 1)
        fixture.commands[('findmnt', '--json', '-o', 'TARGET,FSROOT,FSTYPE')] = (
            0, '{"filesystems":[{"target":"/top", "fsroot":"/", "fstype":"btrfs"}]}')
        fixture.files['/top/@eitr-factory/manifest.json'] = '{"version":1}'
        self.assert_status(check.check_factory, fixture, 'info')
        fixture.commands[('findmnt', '--json', '-o', 'TARGET,FSROOT,FSTYPE')] = (0, '{"filesystems":[]}')
        with self.assertRaises(check.Unavailable):
            check.check_factory(fixture)

    def test_channel_lock_signatures(self):
        self.assert_status(check.check_channel, Evidence(commands={(check.HELPER, 'channel-status'): (0, 'testing')}), 'info')
        fixture = Evidence(files={'/var/lib/pacman/local/ALPM_DB_VERSION': '9'})
        self.assert_status(check.check_pacman_lock, fixture, 'ok')
        fixture.files['/var/lib/pacman/db.lck'] = ''
        for status, expected in ((0, 'info'), (1, 'warning')):
            fixture.commands[('pgrep', '-x', 'pacman')] = (status, '')
            self.assert_status(check.check_pacman_lock, fixture, expected)
        fixture.files['/var/log/pacman.log'] = 'database signature is invalid'
        self.assert_status(check.check_signatures, fixture, 'warning')
        fixture.files['/var/log/pacman.log'] = 'installed linux'
        with self.assertRaises(check.Unavailable):
            check.check_signatures(fixture)

    def test_cached_updates_only_use_temporary_database(self):
        with tempfile.TemporaryDirectory() as directory:
            database = Path(directory) / 'core.db'
            database.write_text('fixture')
            for status, output, expected in ((0, 'linux 1 -> 2', 'warning'), (2, '', 'ok')):
                fixture = Evidence(globs={'/var/lib/pacman/sync/*.db': [str(database)],
                                          '/var/lib/pacman/sync/*.db*': [str(database)]},
                                   commands={('checkupdates', '--nosync'): (status, output)})
                self.assert_status(check.check_updates, fixture, expected)
                arguments, kwargs = fixture.calls[-1]
                self.assertEqual(arguments, ('checkupdates', '--nosync'))
                self.assertEqual(kwargs['timeout'], 12)
                temporary = Path(kwargs['env']['CHECKUPDATES_DB'])
                self.assertFalse(temporary.exists())

    def test_failed_units_and_processes(self):
        for function, arguments in ((check.check_system_units, ('systemctl', '--failed', '--no-legend', '--plain', '--no-pager')),
                                    (check.check_user_units, ('systemctl', '--user', '--failed', '--no-legend', '--plain', '--no-pager'))):
            for output, expected in (('', 'ok'), ('broken.service loaded failed failed', 'problem')):
                self.assert_status(function, Evidence(commands={arguments: (0, output)}), expected)
        for status, expected in ((0, 'ok'), (1, 'problem')):
            self.assert_status(check.check_elephant, Evidence(commands={('pgrep', '-x', 'elephant'): (status, '')}), expected)
        for status in (0, 1):
            self.assert_status(check.check_idle, Evidence(commands={('pgrep', '-x', 'hypridle'): (status, '')}), 'info')
        for arguments, expected in (('walker\x00--gapplication-service\x00', 'ok'), ('walker\x00', 'problem')):
            self.assert_status(check.check_walker, Evidence(commands={('pgrep', '-x', 'walker'): (0, '42')},
                                                          files={'/proc/42/cmdline': arguments}), expected)
        self.assert_status(check.check_walker, Evidence(commands={('pgrep', '-x', 'walker'): (1, '')}), 'problem')
        with self.assertRaises(check.Unavailable):
            check.check_walker(Evidence(commands={('pgrep', '-x', 'walker'): (0, '42')}))
        bar = ('eitr-shell', 'desktop-bar', 'ipc', 'call', 'notifications', 'status')
        self.assert_status(check.check_bar, Evidence(commands={bar: (0, '{"count":0}')}), 'ok')

        class FlakyBar(Evidence):
            # A reloading bar can fail once; the check retries.
            def run(self, *arguments, **options):
                self.calls.append(arguments)
                return (255, '{"cou') if len(self.calls) == 1 else (0, '{"count":0}')
        self.assert_status(check.check_bar, FlakyBar(), 'ok')
        with self.assertRaises(check.Unavailable):
            check.check_bar(Evidence(commands={bar: (0, 'not json')}))

    def test_memory_pressure_swap_oom_and_crashes(self):
        for number, expected in ((0, 'ok'), (10, 'warning')):
            self.assert_status(check.check_pressure, Evidence(files={'/proc/pressure/memory': f'some avg10={number} avg60=0 total=0'}), expected)
        for used, expected in ((100, 'ok'), (900, 'warning')):
            self.assert_status(check.check_swap, Evidence(files={'/proc/swaps': f'Filename Type Size Used Priority\n/dev/zram0 partition 1000 {used} 100'}), expected)
        self.assert_status(check.check_swap, Evidence(files={'/proc/swaps': 'Filename Type Size Used Priority\n'}), 'info')
        for output, expected in (('Linux booted', 'ok'), ('oom-kill: task\nKilled process 42', 'problem')):
            self.assert_status(check.check_oom, Evidence(commands={('journalctl', '-k', '-b', '--no-pager', '-o', 'cat', '--quiet'): (0, output)}), expected)
        for output, expected in (('', 'ok'), ('one crash', 'warning')):
            self.assert_status(check.check_coredumps, Evidence(commands={('coredumpctl', '--no-pager', '--no-legend', 'list', '--since=-7d'): (0, output)}), expected)

    def test_dns_clock_firewall_and_desktop(self):
        for status, expected in ((0, 'ok'), (2, 'problem')):
            fixture = Evidence(commands={('getent', 'ahosts', 'archlinux.org'): (status, 'resolved' if status == 0 else '')})
            self.assert_status(check.check_dns, fixture, expected)
            self.assertEqual(fixture.calls[0][1]['timeout'], 3)
        for value, expected in (('yes', 'ok'), ('no', 'warning')):
            self.assert_status(check.check_clock, Evidence(commands={('timedatectl', 'show', '--property=NTPSynchronized', '--value'): (0, value)}), expected)
        for status, expected in ((0, 'ok'), (3, 'warning')):
            fixture = Evidence(commands={(check.HELPER, 'firewall-status'): (status, ''),
                                         ('systemctl', 'show', 'eitr-firewall.service', '--property=LoadState', '--value'): (0, 'loaded')})
            self.assert_status(check.check_firewall, fixture, expected)
            self.assert_status(check.check_security_firewall, fixture, 'info')
        for output, expected in (('', 'ok'), ('bad option', 'problem')):
            self.assert_status(check.check_hyprland, Evidence(commands={('hyprctl', 'configerrors'): (0, output)}), expected)
        for status, output, expected in ((0, 'media.class = "Audio/Sink"', 'ok'), (1, '', 'problem')):
            fixture = Evidence(commands={('pgrep', '-x', 'pipewire'): (0, ''),
                                         ('wpctl', 'inspect', '@DEFAULT_AUDIO_SINK@'): (status, output)})
            self.assert_status(check.check_audio, fixture, expected)

    def test_security_information(self):
        for value in ('\x00', '\x01'):
            fixture = Evidence(globs={'/sys/firmware/efi/efivars/SecureBoot-*': ['/efi-variable']},
                               files={'/efi-variable': '\x07\x00\x00\x00' + value})
            self.assert_status(check.check_secure_boot, fixture, 'info')
        for kind in ('crypt', 'disk'):
            fixture = Evidence(commands={('findmnt', '-n', '-o', 'SOURCE', '-T', mount): (0, '/dev/test[/@]') for mount in ('/', '/home')})
            fixture.commands[('lsblk', '--json', '--inverse', '--output', 'TYPE', '/dev/test')] = (0, json.dumps({'blockdevices': [{'type': 'part', 'children': [{'type': kind}]}]}))
            answer = self.assert_status(check.check_encryption, fixture, 'info')
            self.assertIn('encrypted block ancestry' if kind == 'crypt' else 'no block encryption', answer[1])
        for output in ('LISTEN 0 1 0.0.0.0:22 0.0.0.0:*', 'LISTEN 0 1 *:2222 *:* users:(("sshd",pid=1))', ''):
            fixture = Evidence(commands={('systemctl', 'is-enabled', 'sshd.service'): (1, 'disabled'), ('ss', '-H', '-ltnp'): (0, output)})
            self.assert_status(check.check_ssh, fixture, 'info')

    def test_plugin_owner_is_read_only_and_hooks_tail(self):
        fixture = Evidence(files={'/fixture-state/eitr/plugins.json': '{}'})
        with patch('eitr_plugins.Plugins') as plugins:
            for blocked, expected in (({}, 'ok'), ({'fixture': ('policy', 'blocked')}, 'warning')):
                plugins.return_value.blocked.return_value = blocked
                self.assert_status(check.check_plugins, fixture, expected)
            self.assertEqual(plugins.return_value.method_calls, [unittest.mock.call.blocked(), unittest.mock.call.blocked()])
        for output, expected in (('', 'ok'), ('demo login: exited with 1\n', 'warning'),
                                  ('demo after-update: timeout after 30 seconds\n', 'warning'),
                                  ('demo login: exited with 1\n' + 'success\n' * 100, 'ok')):
            fixture.files['/fixture-state/eitr/plugin-hooks.log'] = output
            self.assert_status(check.check_plugin_hooks, fixture, expected)

    def test_json_output_plain_alignment_and_colors(self):
        checks = [check.Result('Fixture', 'fixture', status, 'A short diagnostic.', 'mock', check.REPORT if status in ('warning', 'problem') else '')
                  for status in ('ok', 'warning', 'problem', 'info', 'skipped')]
        with patch.object(check, 'collect', return_value=checks), contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(check.main(['--json']), 0)
            data = json.loads(output.getvalue())
        self.assertEqual(data['counts'], dict.fromkeys(('ok', 'warning', 'problem', 'info', 'skipped'), 1))
        self.assertEqual(data['checks'][2]['source'], 'mock')
        plain = check.plain(checks)
        self.assertNotIn('\x1b', plain)
        lines = [line for line in plain.splitlines() if 'fixture ' in line]
        self.assertEqual(len({line.index('A short') for line in lines}), 1)
        self.assertIn('\x1b[31m', check.plain(checks, color=True))
        self.assertTrue(all(len(line) <= 120 for line in plain.splitlines()))
        self.assertIn('Summary:', plain.splitlines()[-1])

    def test_enter_copies_reusing_problem_report_redaction_escape_closes(self):
        report = check.report_module()
        raw = 'fixture-user fixture-host /home/fixture-user/a 10.1.2.3 aa:bb:cc:dd:ee:ff person@example.net'
        redacted = report.redact(raw, user='fixture-user', host='fixture-host', home='/home/fixture-user')
        for private in ('fixture-user', 'fixture-host', '/home/', '10.1.2.3', 'aa:bb:', 'person@example.net'):
            self.assertNotIn(private, redacted)
        with patch.object(check, 'collect', return_value=[]), patch.object(check, 'plain', return_value=raw), \
             patch.object(check, 'report_module', return_value=report), patch.object(report, 'redact', return_value=redacted) as redact, \
             patch.object(report, 'copy', return_value=True) as copy, patch.object(check.sys.stdin, 'isatty', return_value=True), \
             patch.object(check, 'read_key', side_effect=['\x1b', '\r', '\x1b']), contextlib.redirect_stdout(io.StringIO()):
            check.main([])
        redact.assert_called_once_with(raw)
        copy.assert_called_once_with(redacted)

    def test_menu_cli_manifest_report_and_fixes(self):
        cli = load_cli()
        self.assertEqual(cli.plan(cli.parser().parse_args(['check']), ROOT), ['python3', str(ROOT / 'distro/lib/eitr_selfcheck.py')])
        self.assertEqual(cli.plan(cli.parser().parse_args(['check', '--json']), ROOT)[-1], '--json')
        rows = json.loads((ROOT / 'elephant/menu-rows/system-maintenance.json').read_text())
        actions = [row['text'] for row in rows if 'submenu' not in row]
        self.assertEqual(actions, sorted(actions, key=str.casefold))
        row = next(row for row in rows if row['text'] == 'Check This PC')
        self.assertIn('/task-terminal.py eitr check', row['actions']['open'])
        self.assertNotIn('--hold', row['actions']['open'])
        self.assertIn('scoped-menu.lua', (ROOT / 'elephant/menus/system-maintenance.lua').read_text())
        rules = json.loads((ROOT / 'distro/layout-manifest.json').read_text())['rules']
        self.assertTrue(any(rule['pattern'] == 'distro/lib/eitr_selfcheck.py' and rule['runtime'] for rule in rules))
        # Every menu fix is resolved by following the real menu tree.
        for path in (check.UPDATE, check.REPORT, check.RESTART, check.CLEANUP, check.FIREWALL, 'Plugins > Installed Plugins'):
            parts = path.removeprefix('Main > ').split(' > ')
            menu = 'main'
            for title in parts:
                entries = json.loads((ROOT / f'elephant/menu-rows/{menu}.json').read_text())
                found = next(row for row in entries if row['text'] == title)
                menu = found.get('submenu', '')
        chapters = {chapter['id']: chapter for chapter in json.loads(
            (ROOT / 'quickshell/desktop-bar/handbook/chapters.json').read_text())}
        for chapter in ('recovery', 'network-backends'):
            self.assertTrue((ROOT / chapters[chapter]['source']).is_file())
        report = check.report_module()
        with patch.object(check, 'collect', return_value=[]), patch.object(report, 'command', return_value=''), \
             patch.object(report, 'file_tail', return_value=''), patch.object(report, 'latest_file', return_value=''), \
             patch.object(Path, 'is_file', return_value=False):
            self.assertIn('## Self-check summary\n', report.collect())

    def test_command_boundary_timeouts_errors_and_no_privilege(self):
        for error in (FileNotFoundError(), subprocess.TimeoutExpired('tool', 3), PermissionError()):
            with patch.object(subprocess, 'run', side_effect=error), self.assertRaises(check.Unavailable):
                check.Context().run('fixture-read-only-tool')
        with patch.object(subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, 'ok', '')) as run:
            check.Context().run('fixture-read-only-tool')
            self.assertEqual(run.call_args.kwargs['timeout'], 5)
            self.assertEqual(run.call_args.kwargs['env']['LC_ALL'], 'C')
        source = (ROOT / 'distro/lib/eitr_selfcheck.py').read_text()
        self.assertIn("['sudo', HELPER, 'selfcheck-deeper']", source)
        self.assertNotIn("'restart'", source)
        self.assertNotIn("'mount'", source)


if __name__ == '__main__':
    unittest.main()
