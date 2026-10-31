import importlib.machinery
import importlib.util
from pathlib import Path
import tempfile
import unittest
import unittest.mock
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
loader = importlib.machinery.SourceFileLoader('eitr_launch', str(ROOT / 'distro/bin/eitr-launch'))
spec = importlib.util.spec_from_loader('eitr_launch', loader)
launch = importlib.util.module_from_spec(spec)
loader.exec_module(launch)


class LauncherTests(unittest.TestCase):
    def run_launcher(self, executable, arguments):
        with patch.object(launch.os, 'execvpe') as execute:
            launch.main(arguments, executable)
        return execute.call_args.args[1], execute.call_args.args[2]

    def test_options_pass_through_to_walker(self):
        command, _ = self.run_launcher('eitr-walker', ['--gapplication-service'])
        self.assertEqual(command[-1], '--gapplication-service')
        self.assertTrue(command[-2].endswith('walker/bin/walker'))
        command, _ = self.run_launcher('eitr-walker', ['--provider', 'menus:main'])
        self.assertEqual(command[-2:], ['--provider', 'menus:main'])

    def test_shell_options_and_ipc_reach_quickshell(self):
        command, _ = self.run_launcher('eitr-shell', ['desktop-bar', '--no-color'])
        self.assertEqual(command[:3], ['quickshell', '-n', '-p'])
        self.assertEqual(command[-1], '--no-color')
        command, _ = self.run_launcher('eitr-shell', ['desktop-bar', 'ipc', 'call', '--', 'panels', 'show', 'wifi'])
        self.assertEqual(command[:3], ['quickshell', 'ipc', '-p'])
        self.assertEqual(command[-5:], ['call', '--', 'panels', 'show', 'wifi'])

    def test_daemonized_starts_wait_for_each_other(self):
        with tempfile.TemporaryDirectory() as runtime, \
                patch.dict(launch.os.environ, {'XDG_RUNTIME_DIR': runtime}), \
                patch.object(launch.fcntl, 'flock') as flock, \
                patch.object(launch.subprocess, 'run', return_value=unittest.mock.Mock(returncode=0)) as run, \
                patch.object(launch.os, 'execvpe') as execute:
            self.assertEqual(launch.main(['desktop-bar', '--daemonize'], 'eitr-shell'), 0)
        execute.assert_not_called()
        flock.assert_called_once_with(unittest.mock.ANY, launch.fcntl.LOCK_EX)
        self.assertEqual(flock.call_args.args[0].name, f'{runtime}/eitr/shell-desktop-bar.lock')
        command = run.call_args.args[0]
        self.assertEqual(command[:3], ['quickshell', '-n', '-p'])
        self.assertEqual(command[-1], '--daemonize')

    def test_ipc_reaches_a_running_checkout_when_the_package_is_not_running(self):
        packaged = Path('/usr/share/eitr/quickshell/desktop-bar')
        checkout = '/home/me/eitr/quickshell/desktop-bar'
        def listing(*instances):
            entries = [{'config_path': path + '/shell.qml'} for path in instances]
            return unittest.mock.Mock(stdout=__import__('json').dumps(entries))
        with patch.object(launch, 'shell_path', return_value=packaged):
            with patch.object(launch.subprocess, 'run', return_value=listing(checkout)):
                command, _ = self.run_launcher('eitr-shell', ['desktop-bar', 'ipc', 'call', '--', 'controlCenter', 'toggle'])
            self.assertEqual(command[:4], ['quickshell', 'ipc', '-p', checkout])
            with patch.object(launch.subprocess, 'run', return_value=listing(str(packaged), checkout)):
                command, _ = self.run_launcher('eitr-shell', ['desktop-bar', 'ipc', 'call', '--', 'controlCenter', 'toggle'])
            self.assertEqual(command[3], str(packaged))
            with patch.object(launch.subprocess, 'run', side_effect=OSError):
                command, _ = self.run_launcher('eitr-shell', ['desktop-bar', 'ipc', 'call', '--', 'controlCenter', 'toggle'])
            self.assertEqual(command[3], str(packaged))
            with patch.object(launch.subprocess, 'run', return_value=listing(checkout)):
                command, _ = self.run_launcher('eitr-shell', ['desktop-bar'])
            self.assertEqual(command[:4], ['quickshell', '-n', '-p', str(packaged)])

    def test_only_checkouts_and_overrides_reload_quickshell_live(self):
        with patch.object(launch, 'ROOT', Path('/usr/share/eitr')), \
                patch.object(launch, 'shell_path', return_value=Path('/usr/share/eitr/quickshell/desktop-bar')):
            _, environment = self.run_launcher('eitr-shell', ['desktop-bar'])
        self.assertEqual(environment['EITR_LIVE_RELOAD'], '0')
        with patch.object(launch, 'ROOT', Path('/usr/share/eitr')), \
                patch.object(launch, 'shell_path', return_value=Path('/home/me/.config/eitr/overrides/quickshell/desktop-bar')):
            _, environment = self.run_launcher('eitr-shell', ['desktop-bar'])
        self.assertEqual(environment['EITR_LIVE_RELOAD'], '1')
        _, environment = self.run_launcher('eitr-shell', ['--repo', str(ROOT), 'desktop-bar'])
        self.assertEqual(environment['EITR_LIVE_RELOAD'], '1')
        for shell in sorted((ROOT / 'quickshell').glob('*/shell.qml')):
            with self.subTest(shell=shell.parent.name):
                self.assertIn('Quickshell.watchFiles = Quickshell.env("EITR_LIVE_RELOAD") === "1"', shell.read_text())

    def test_children_of_a_checkout_stay_on_it(self):
        with patch.object(launch, 'ROOT', Path('/usr/share/eitr')), \
                patch.dict(launch.os.environ, {'EITR_CODE_ROOT': str(ROOT)}):
            command, environment = self.run_launcher('eitr-shell', ['wallpaper-transition'])
        self.assertEqual(command[-1], str(ROOT / 'quickshell/wallpaper-transition'))
        self.assertEqual(environment['EITR_LIVE_RELOAD'], '1')

    def test_only_a_leading_repo_selects_a_checkout(self):
        command, environment = self.run_launcher('eitr-run', ['--repo', str(ROOT), 'fastfetch/eitr.py', '--repo', 'x'])
        self.assertEqual(environment['EITR_CODE_ROOT'], str(ROOT))
        self.assertEqual(command[-2:], ['--repo', 'x'])
        with self.assertRaises(ValueError):
            launch.main(['--repo'], 'eitr-run')


if __name__ == '__main__':
    unittest.main()
