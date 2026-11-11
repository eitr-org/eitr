"""Clicking a notification without its own action opens the app that sent it."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'notification-open.py'


def load():
    specification = importlib.util.spec_from_file_location('notification_open', SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class NotificationOpenTests(unittest.TestCase):
    def setUp(self):
        self.module = load()
        self.directory = tempfile.TemporaryDirectory()
        self.proc = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def process(self, pid, parent, argv):
        folder = self.proc / str(pid)
        folder.mkdir()
        (folder / 'stat').write_text(f'{pid} (a name) with spaces) S {parent} 1 1')
        (folder / 'cmdline').write_bytes(b'\0'.join(part.encode() for part in argv) + b'\0')

    def test_the_window_of_the_nearest_ancestor(self):
        self.process(100, 1, ['kitty'])
        self.process(200, 100, ['zsh'])
        self.process(300, 200, ['tool'])
        windows = [{'pid': 100, 'address': '0xa'}, {'pid': 999, 'address': '0xb'}]
        self.assertEqual(self.module.window_of(300, windows, self.proc)['address'], '0xa')
        self.assertIsNone(self.module.window_of(999999, windows, self.proc))

    def test_class_match_prefers_the_most_recent_window(self):
        windows = [{'class': 'Slack', 'focusHistoryID': 4, 'address': '0x1'},
                   {'class': 'slack', 'focusHistoryID': 1, 'address': '0x2'},
                   {'class': 'firefox', 'focusHistoryID': 0, 'address': '0x3'}]
        self.assertEqual(self.module.window_by_name(['slack.desktop', 'Slack'], windows)['address'], '0x2')
        self.assertIsNone(self.module.window_by_name(['Herdr'], windows))

    def test_herdr_clients_skip_its_server(self):
        self.process(10, 1, ['/home/user/.local/bin/herdr', 'server'])
        self.process(20, 1, ['/home/user/.local/bin/herdr'])
        self.process(30, 1, ['/usr/bin/kitty', '-e', '/home/user/.local/bin/herdr'])
        self.assertEqual(self.module.herdr_clients(self.proc), [20])

    def test_herdr_workspace_and_tab_by_label(self):
        workspaces = json.dumps({'result': {'workspaces': [{'label': 'Doola', 'workspace_id': 'w3'}, {'label': 'Personal', 'workspace_id': 'w4'}]}})
        tabs = json.dumps({'result': {'tabs': [{'label': 'Automations', 'tab_id': 'w3:t1'}, {'label': 'Reviewer', 'tab_id': 'w3:t3'}]}})
        self.assertEqual(self.module.herdr_find(workspaces, 'workspace', 'Personal'), 'w4')
        self.assertEqual(self.module.herdr_find(tabs, 'tab', 'Reviewer'), 'w3:t3')
        self.assertEqual(self.module.herdr_find(workspaces, 'workspace', 'Missing'), '')
        self.assertEqual(self.module.herdr_find('not json', 'workspace', 'Personal'), '')

    def test_herdr_names_skip_its_numbers(self):
        self.assertEqual(self.module.herdr_names('Doola · 1 · Automations'), ['Doola', 'Automations'])
        self.assertEqual(self.module.herdr_names('Personal · 2'), ['Personal', ''])
        self.assertEqual(self.module.herdr_names(''), ['', ''])


if __name__ == '__main__':
    unittest.main()
