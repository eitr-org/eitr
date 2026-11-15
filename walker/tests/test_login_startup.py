"""Isolated login checks: no live compositor or services."""
import json
import os
from pathlib import Path
import runpy
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch, Mock
import contextlib
import io

ROOT = Path(__file__).resolve().parents[2]


def lua_literal(value):
    if isinstance(value, dict):
        return '{' + ','.join('[' + json.dumps(key) + ']=' + lua_literal(item) for key, item in value.items()) + '}'
    if isinstance(value, list):
        return '{' + ','.join(lua_literal(item) for item in value) + '}'
    return json.dumps(value)


class LoginStartupTests(unittest.TestCase):
    def test_schema_matches_helpers(self):
        subprocess.run(['python3', str(ROOT / 'tools/login-settings.py'), '--check'], check=True)

    def test_lua_settings_match_python(self):
        schema = json.loads((ROOT / 'quickshell/desktop-bar/login-settings.json').read_text())
        scripts = {'bar-settings.py': 'quickshell/desktop-bar/scripts/bar-settings.py',
                   'desktop-style.py': 'quickshell/desktop-bar/scripts/desktop-style.py',
                   'terminal.py': 'walker/scripts/actions/style/terminal.py'}
        with tempfile.TemporaryDirectory() as directory:
            environment = dict(os.environ, XDG_CONFIG_HOME=directory, EITR_CODE_ROOT=str(ROOT),
                               EITR_LIBRARY_ROOT=str(ROOT / 'distro/lib'))
            for script, definition in schema.items():
                target = Path(directory) / definition['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                for data in ({}, {'layout': 'split'}, {key: 'invalid' for key in definition['defaults']},
                             {key: values[-1] for key, values in definition['options'].items()}):
                    target.write_text(json.dumps(data))
                    # Supply Elephant's JSON API with decoded fixtures; exercise the actual Lua reader.
                    fixtures = {json.dumps(data): data, (ROOT / 'quickshell/desktop-bar/login-settings.json').read_text(): schema}
                    source = 'local fixtures=' + lua_literal(fixtures) + '\njsonDecode=function(raw) return fixtures[raw] end\n'
                    source += 'local read=dofile(' + json.dumps(str(ROOT / 'elephant/setting-value.lua')) + ')\n'
                    for key in definition['defaults']:
                        expected = subprocess.check_output(['python3', str(ROOT / scripts[script]), 'get', key], env=environment, text=True).strip()
                        source += 'assert(read(' + json.dumps(script) + ',' + json.dumps(key) + ')==' + json.dumps(expected) + ')\n'
                    subprocess.run(['lua', '-'], input=source, text=True, env=environment, check=True)

    def test_plugin_snapshot_keeps_all_three_results(self):
        helper = runpy.run_path(str(ROOT / 'walker/scripts/actions/install/plugins.py'))
        manager = Mock()
        manager.ui.return_value = [{'plugin': 'sample'}]
        manager.installed.return_value = [{'id': 'sample'}]
        manager.placements.return_value = {'widgets': [], 'barItems': []}
        output = io.StringIO()
        with patch.dict(helper['main'].__globals__, Plugins=Mock(return_value=manager)), contextlib.redirect_stdout(output):
            helper['main'](['snapshot'])
        self.assertEqual(json.loads(output.getvalue()), dict(entries=manager.ui.return_value,
                         installed=manager.installed.return_value, placements=manager.placements.return_value))
        manager.ensure_bundled.assert_called_once()

    def test_keyboard_domain_no_devices_and_shared_contract(self):
        domain = runpy.run_path(str(ROOT / 'quickshell/desktop-bar/scripts/keyboard-domain.py'))['KeyboardDomain']()
        domain.helper = {'keyboards': Mock(return_value=[]), 'options': Mock(return_value=[])}
        self.assertEqual(domain.read('keyboard.layouts'), {'layouts': [], 'active': -1})
        keyboard = {'main': True, 'active_layout_index': 1}
        layouts = [{'index': 0, 'label': 'English', 'code': 'US'}]
        domain.helper['keyboards'].return_value = [keyboard]
        domain.helper['options'].return_value = layouts
        self.assertEqual(domain.read('keyboard.layouts'), {'layouts': layouts, 'active': 1})
        broker = runpy.run_path(str(ROOT / 'quickshell/desktop-bar/scripts/bar-data.py'))['Broker']
        instance = broker(lambda frame: None)
        self.assertIn('keyboard', instance.domain_locks)
        instance.executor.shutdown(wait=False)

    def test_complete_polkit_poll_bounds_slow_ipc(self):
        source = (ROOT / 'hypr/scripts/polkit-fallback.sh').read_text()
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'eitr-shell'
            fake.write_text('#!/bin/bash\nsleep 5\n')
            fake.chmod(0o755)
            # Shorten only the test's deadline; the slow command must be interrupted.
            source = source.replace('15s bash', '0.2s bash').replace('exec env -u QT_STYLE_OVERRIDE /usr/lib/polkit-kde-authentication-agent-1', 'printf fallback')
            started = time.monotonic()
            result = subprocess.run(['bash', '-c', source], env=dict(os.environ, PATH=directory + ':' + os.environ['PATH']), capture_output=True, text=True, timeout=2)
            self.assertEqual(result.stdout, 'fallback')
            self.assertLess(time.monotonic() - started, 1)

    def test_bar_waits_at_most_a_second_for_the_wallpaper(self):
        source = (ROOT / 'hypr/scripts/session-start.sh').read_text()
        wait = next(line for line in source.splitlines() if line.startswith('timeout -s KILL 1s') and 'wallpaper_settled' in line)
        self.assertLess(source.index(wait), source.index('eitr-shell desktop-bar --daemonize'))
        # The probe and Hyprpaper run in the background; a missing marker must not hold the bar.
        self.assertIn('eitr-hyprpaper &', source[source.index('(rendering=$('):source.index(wait)])
        started = time.monotonic()
        subprocess.run(['bash', '-c', 'wallpaper_settled=/nonexistent/settled; ' + wait], timeout=3)
        self.assertLess(time.monotonic() - started, 1.5)

    def test_bar_poll_interrupts_a_slow_command(self):
        source = (ROOT / 'hypr/scripts/session-start.sh').read_text()
        poll = next(line for line in source.splitlines() if line.startswith('if timeout') and 'bar workspaces' in line)
        poll = poll.removeprefix('if ').removesuffix('; then').replace('8s bash', '0.2s bash')
        with tempfile.TemporaryDirectory() as directory:
            fake = Path(directory) / 'eitr-shell'
            fake.write_text('#!/bin/bash\nsleep 5\n')
            fake.chmod(0o755)
            started = time.monotonic()
            result = subprocess.run(['bash', '-c', poll], env=dict(os.environ, PATH=directory + ':' + os.environ['PATH']),
                                    capture_output=True, timeout=2)
            self.assertNotEqual(result.returncode, 0)
            self.assertLess(time.monotonic() - started, 1)

    def test_timing_format_and_shared_clock(self):
        timing = runpy.run_path(str(ROOT / 'distro/lib/eitr_login_timing.py'))
        with tempfile.TemporaryDirectory() as directory, patch.dict(os.environ, XDG_STATE_HOME=directory):
            target = Path(directory) / 'eitr'
            target.mkdir()
            subprocess.run(['bash', '-c', 'source "$1"; login_mark session-start', 'bash', str(ROOT / 'hypr/scripts/login-timing.sh')], check=True)
            timing['mark']('search-index-committed')
            rows = [json.loads(line) for line in (target / 'login-timing.jsonl').read_text().splitlines()]
            self.assertEqual([row['event'] for row in rows], ['session-start', 'search-index-committed'])
            self.assertLess(abs(rows[1]['monotonic'] - rows[0]['monotonic']), 1)
            self.assertTrue(all(row['wall'] > 0 for row in rows))


if __name__ == '__main__':
    unittest.main()
