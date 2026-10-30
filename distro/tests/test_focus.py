"""Focus conversion and recovery without touching the compositor."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from eitr_focus import Hypr, clients_by_monitor, spread_plan, change, enabled, gather, tab_action

ROOT = Path(__file__).resolve().parents[2]


def client(number, monitor=0, workspace='1', grouped=None, hidden=False):
    return {'address': hex(number), 'monitor': monitor, 'mapped': True, 'workspace': {'name': workspace},
            'grouped': grouped or [], 'hidden': hidden, 'title': 'Example'}


class FakeHypr:
    def __init__(self, clients=None):
        self.clients = clients or []
        self.commands = []
        self.active = self.clients[0] if self.clients else {}

    def query(self, kind):
        if kind == 'clients':
            return copy.deepcopy(self.clients)
        if kind == 'activewindow':
            return copy.deepcopy(self.active)
        if kind == 'monitors':
            return [{'id': 0, 'name': 'Test-0', 'activeWorkspace': {'name': 'eitr-focus-0'}},
                    {'id': 1, 'name': 'Test-1', 'activeWorkspace': {'name': 'eitr-focus-1'}}]
        raise AssertionError(kind)

    def run(self, *arguments):
        self.commands.append(arguments)

    def ensure_bar(self):
        self.commands.append(('bar',))

    def option(self, name):
        if name.endswith(('gaps_in', 'gaps_out')):
            return {'css': '6 8 10 12'}
        if name == 'general:layout':
            return {'str': 'dwindle'}
        if name in ('general:border_size', 'decoration:rounding'):
            return {'int': 1}
        return {'bool': True}

    def evaluate(self, text):
        self.commands.append(text)

    def window(self, address, text):
        self.commands.append((address, text))


class FocusTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.environment = patch.dict(os.environ, XDG_CONFIG_HOME=self.temporary.name,
                                      XDG_STATE_HOME=self.temporary.name, EITR_CODE_ROOT=str(ROOT))
        self.environment.start()
        self.addCleanup(self.environment.stop)

    def test_preference_and_off_recovery(self):
        hypr = FakeHypr([client(1), client(2, 1)])
        self.assertFalse(enabled())
        change('on', hypr)
        self.assertTrue(enabled())
        change('off', hypr)
        self.assertFalse(enabled())
        self.assertIn(('reload', 'config-only'), hypr.commands)
        self.assertIn(('bar',), hypr.commands)
        self.assertTrue(any('workspace=1' in str(command) for command in hypr.commands))
        change('off', hypr)
        self.assertFalse(enabled())

    def test_spread_two_per_workspace_preserves_monitors(self):
        clients = [client(number, number % 2) for number in range(1, 10)]
        plan = spread_plan(clients)
        counts = {}
        monitor_by_workspace = {}
        for _, monitor, workspace in plan:
            counts[workspace] = counts.get(workspace, 0) + 1
            self.assertEqual(monitor_by_workspace.setdefault(workspace, monitor), monitor)
        self.assertEqual(len(plan), 9)
        self.assertLessEqual(max(counts.values()), 2)
        self.assertEqual(spread_plan([]), [])

    def test_reconcile_preserves_split_and_adds_new_windows(self):
        residents = [client(1, workspace='eitr-focus-0', grouped=['0x1', '0x2']),
                     client(2, workspace='eitr-focus-0', grouped=['0x1', '0x2'], hidden=True),
                     client(3, workspace='eitr-focus-0', grouped=['0x3'])]
        hypr = FakeHypr(residents)
        gather(hypr)
        self.assertEqual(hypr.commands, [])
        hypr.clients.append(client(4))
        gather(hypr)
        self.assertTrue(any('anchor.group:add(window)' in str(command) for command in hypr.commands))
        self.assertTrue(all(not isinstance(command, tuple) or command[0] == '0x4' for command in hypr.commands))

    def test_floating_windows_stay_floating_and_out_of_tabs(self):
        dialog = {**client(5), 'floating': True}
        hypr = FakeHypr([client(4), dialog])
        gather(hypr)
        dialog_commands = [text for address, text in (command for command in hypr.commands if isinstance(command, tuple))
                           if address == '0x5']
        self.assertEqual(len(dialog_commands), 1)
        self.assertIn('window.move', dialog_commands[0])
        # Hyprland treats an unknown float or pin action as a toggle.
        self.assertNotIn('"unset"', ''.join(str(command) for command in hypr.commands))

    def test_empty_and_four_pane_limit(self):
        hypr = FakeHypr()
        change('on', hypr)
        tab_action('horizontal', '', hypr)
        hypr.clients = [client(number, grouped=[hex(number)]) for number in range(1, 5)]
        hypr.active = hypr.clients[0]
        hypr.commands.clear()
        tab_action('horizontal', '', hypr)
        self.assertEqual(hypr.commands, [])

    def test_crash_leaves_recoverable_preference(self):
        hypr = FakeHypr()
        with patch.object(hypr, 'run', side_effect=RuntimeError('compositor unavailable')):
            with self.assertRaises(RuntimeError):
                change('on', hypr)
        self.assertTrue(enabled())
        change('off', hypr)
        self.assertFalse(enabled())

    def test_command_and_no_compositor_status(self):
        command = ROOT / 'distro/bin/eitr'
        result = subprocess.run(['python3', str(command), 'focus', 'status'], text=True,
                                capture_output=True, env=os.environ)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), 'off')
        from importlib.machinery import SourceFileLoader
        specification = importlib.util.spec_from_loader('eitr_command', SourceFileLoader('eitr_command', str(command)))
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        arguments = module.parser().parse_args(['focus', 'on'])
        self.assertEqual(module.plan(arguments, ROOT)[-1], 'on')
        self.assertTrue(module.plan(arguments, ROOT)[1].endswith('eitr_focus.py'))

    def test_fake_hyprctl_process_and_address_validation(self):
        executable = Path(self.temporary.name) / 'hyprctl'
        executable.write_text('#!/usr/bin/env python3\nimport json,sys\nprint(json.dumps([]) if sys.argv[1:]==["-j","clients"] else "ok")\n')
        executable.chmod(0o755)
        with patch.dict(os.environ, PATH=self.temporary.name + os.pathsep + os.environ['PATH']):
            self.assertEqual(Hypr().query('clients'), [])
            self.assertEqual(Hypr().window('0x123', 'window.group:remove(window)').strip(), 'ok')
            with self.assertRaises(ValueError):
                Hypr().window('0x123); os.execute("bad")', '')

    def test_unmapped_not_in_spread(self):
        self.assertEqual(clients_by_monitor([dict(client(1), mapped=False)]), {})

    def test_snapshot_survives_repeated_on_and_corner_change(self):
        hypr = FakeHypr([client(1)])
        change('on', hypr)
        journal = Path(self.temporary.name) / 'eitr/focus-session.json'
        saved = json.loads(journal.read_text())
        with patch.object(hypr, 'option', side_effect=AssertionError('must not replace original settings')):
            change('on', hypr)
        self.assertEqual(json.loads(journal.read_text()), saved)
        from eitr_paths import write_settings
        write_settings(Path(self.temporary.name) / 'eitr/style.json', {'corners': 'square'})
        hypr.commands.clear()
        change('off', hypr)
        restored = next(command for command in hypr.commands if isinstance(command, str) and 'general.gaps_in' in command)
        self.assertIn('["left"]=12.0', restored)
        self.assertNotIn('decoration.rounding', restored)
        self.assertFalse(json.loads(journal.read_text())['pending'])

    def test_lua_strings_preserve_unicode_and_literal_code(self):
        import shutil
        if not shutil.which('lua'):
            self.skipTest('Lua required')
        from eitr_focus import lua
        value = 'Monitor \\"; os.execute("false") -- 日本語\n'
        result = subprocess.run(['lua', '-e', 'io.write(' + lua(value) + ')'], text=True, capture_output=True, check=True)
        self.assertEqual(result.stdout, value)
