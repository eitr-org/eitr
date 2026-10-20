import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / 'scripts/power-profile.py'
spec = importlib.util.spec_from_file_location('power_profile', SCRIPT)
power_profile = importlib.util.module_from_spec(spec)
spec.loader.exec_module(power_profile)

class PowerProfileTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.supplies = self.root / 'power_supply'
        self.supplies.mkdir()
        self.binaries = self.root / 'bin'
        self.binaries.mkdir()
        self.log = self.root / 'calls'
        self.state = self.root / 'active'
        self.state.write_text('balanced')

    def add_supply(self, name, kind):
        (self.supplies / name).mkdir()
        (self.supplies / name / 'type').write_text(kind + '\n')

    def mock_powerprofilesctl(self, profiles=('performance', 'balanced', 'power-saver')):
        lines = ''.join(f'''if [ "$(cat '{self.state}')" = {name} ]; then echo '* {name}:'; else echo '  {name}:'; fi
echo '    CpuDriver: mock'
''' for name in profiles)
        script = self.binaries / 'powerprofilesctl'
        script.write_text(f'''#!/bin/sh
echo "$*" >> '{self.log}'
case "$1" in
  list) {lines.strip() or ':'} ;;
  set) printf '%s' "$2" > '{self.state}' ;;
esac
''')
        script.chmod(0o755)

    def run_script(self, *args):
        stdout = io.StringIO()
        path = str(self.binaries) + os.pathsep + os.environ['PATH']
        with patch.object(power_profile, 'POWER_SUPPLY', self.supplies), \
                patch.dict(os.environ, {'PATH': path}), \
                contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
            try:
                code = power_profile.main(['power-profile.py', *args])
            except (ValueError, subprocess.SubprocessError):
                code = 1
        return SimpleNamespace(returncode=code, stdout=stdout.getvalue(), stderr='')

    def test_desktop_without_system_battery_is_unavailable(self):
        self.add_supply('AC', 'Mains')
        self.add_supply('hidpp_battery_0', 'Battery')
        self.mock_powerprofilesctl()
        result = self.run_script('status')
        self.assertEqual(json.loads(result.stdout), {'available': False, 'active': '', 'profiles': []})
        self.assertFalse(self.log.exists(), 'powerprofilesctl must not run without a laptop battery')

    def test_missing_daemon_is_unavailable(self):
        self.add_supply('BAT0', 'Battery')
        with patch.object(power_profile, 'POWER_SUPPLY', self.supplies), \
                patch.object(power_profile.shutil, 'which', return_value=None):
            self.assertFalse(power_profile.status()['available'])

    def test_status_parses_active_profile_in_display_order(self):
        self.add_supply('BAT0', 'Battery')
        self.mock_powerprofilesctl()
        result = self.run_script('status')
        self.assertEqual(json.loads(result.stdout), {
            'available': True, 'active': 'balanced', 'profiles': ['power-saver', 'balanced', 'performance']})

    def test_set_uses_argv_and_reports_new_state(self):
        self.add_supply('BAT1', 'Battery')
        self.mock_powerprofilesctl()
        result = self.run_script('set', 'power-saver')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['active'], 'power-saver')
        self.assertIn('set power-saver', self.log.read_text())

    def test_unsupported_profile_is_rejected_without_calling_set(self):
        self.add_supply('BAT0', 'Battery')
        self.mock_powerprofilesctl(profiles=('balanced', 'power-saver'))
        for name in ('performance', 'turbo; reboot'):
            with self.subTest(name=name):
                result = self.run_script('set', name)
                self.assertEqual(result.returncode, 1)
                self.assertNotIn('set ', self.log.read_text())

    def test_usage_error(self):
        self.assertEqual(self.run_script('toggle').returncode, 2)


if __name__ == '__main__':
    unittest.main()
