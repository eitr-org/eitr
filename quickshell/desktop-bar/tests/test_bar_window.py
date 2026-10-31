"""Guard the explicit boundary between shell wiring and each screen's bar."""
from pathlib import Path
import re
import unittest

from test_islands_layout import qml_block

BAR = Path(__file__).resolve().parents[1]


class BarWindowTests(unittest.TestCase):
    def test_frame_dependencies_are_explicit_and_do_not_shadow_instance_ids(self):
        shell = (BAR / 'shell.qml').read_text()
        frame = (BAR / 'BarWindow.qml').read_text()
        instance = qml_block(shell, 'BarWindow {')
        dependencies = {
            'host': 'shell',
            'networkServiceRef': 'networkOwner',
            'notificationsRef': 'notificationsService',
            'remoteServiceRef': 'remoteAccessService',
            'dockClientsRef': 'dockClients',
            'idleLockProcessRef': 'toggleIdleLock',
        }
        required = set(re.findall(r'required property var (\w+)', frame))
        self.assertEqual(required, set(dependencies) | {'modelData'})
        for name, outside_id in dependencies.items():
            self.assertIn(f'{name}: {outside_id}', instance)
            self.assertNotEqual(name, outside_id)
            self.assertNotRegex(frame, rf'\b{outside_id}\b')
        self.assertNotRegex(frame, r'\bhost:\s*host\b')
        self.assertIn('host: bar.host', frame)
        self.assertIn('id: bar', frame)
        self.assertIn('Component.onCompleted: host.registerBar(bar)', frame)
        self.assertIn('Component.onDestruction: host.unregisterBar(bar)', frame)
        self.assertIn('target: host\n', frame)
        self.assertIn('function onHandbookOpened() { bar.closePanels(); }', frame)
        self.assertNotIn('PanelWindow {', shell)
        self.assertIn('BarWindow BarWindow.qml', (BAR / 'qmldir').read_text())
