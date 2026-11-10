"""Default per-user tools install once at login, retry after failures and stay removed."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from home_isolation import setUpModule, tearDownModule
import eitr_user_tools as tools
from eitr_paths import read_settings


class UserToolsTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.home = Path(temporary.name)
        environment = dict(HOME=str(self.home), XDG_STATE_HOME=str(self.home / 'state'), PATH='/usr/bin:/bin')
        for patcher in (patch.dict(os.environ, environment), patch('pathlib.Path.home', return_value=self.home)):
            patcher.start()
            self.addCleanup(patcher.stop)
        self.calls = []

    def install(self, tool):
        self.calls.append(tool)
        binary = self.home / '.local/bin' / tools.TOOLS[tool]['command']
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text('#!/bin/sh\n')
        binary.chmod(0o755)

    def recorded(self):
        return read_settings(tools.record()).get('tools', {})

    def test_installs_once_and_never_reinstalls_a_removed_tool(self):
        self.assertEqual(tools.ensure(runner=self.install), ['herdr'])
        self.assertEqual(self.recorded(), {'herdr': 'installed'})
        (self.home / '.local/bin/herdr').unlink()
        self.assertEqual(tools.ensure(runner=self.install), [])
        self.assertEqual(self.calls, ['herdr'])

    def test_failure_records_nothing_and_retries_next_login(self):
        def offline(tool):
            raise subprocess.CalledProcessError(6, ['curl'])
        self.assertEqual(tools.ensure(runner=offline), [])
        self.assertEqual(self.recorded(), {})
        self.assertEqual(tools.ensure(runner=self.install), ['herdr'])

    def test_an_installer_that_installs_nothing_is_retried(self):
        self.assertEqual(tools.ensure(runner=lambda tool: None), [])
        self.assertEqual(self.recorded(), {})

    def test_existing_install_is_recorded_without_running_the_installer(self):
        self.install('herdr')
        self.calls.clear()
        self.assertEqual(tools.ensure(runner=self.install), [])
        self.assertEqual(self.calls, [])
        self.assertEqual(self.recorded(), {'herdr': 'installed'})

    def test_installer_is_the_official_https_script_into_local_bin(self):
        commands = []
        def fake_run(command, **options):
            commands.append((command, options.get('env', {})))
            if command[0] == 'curl':
                Path(command[-1]).write_text('true\n')
            return subprocess.CompletedProcess(command, 0, stdout='https://herdr.dev/install.sh\n')
        with patch.object(tools.subprocess, 'run', side_effect=fake_run):
            tools.run_installer('herdr')
        self.assertIn('https://herdr.dev/install.sh', commands[1][0])
        self.assertIn('--proto', commands[1][0])
        self.assertEqual(commands[2][0][0], 'sh')
        self.assertEqual(commands[2][1]['HERDR_INSTALL_DIR'], str(self.home / '.local/bin'))

    def test_installers_json_lists_herdr(self):
        import json
        installers = json.loads((Path(__file__).resolve().parents[2] / 'distro/installers.json').read_text())
        self.assertEqual(installers['herdr'], 'https://herdr.dev/install.sh')


if __name__ == '__main__':
    unittest.main()
