"""Account switching probes use fake D-Bus; presentation runs without PAM or a lock."""
import importlib.util
import json
import configparser
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('switch_user', ROOT / 'scripts/switch-user.py')
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class SwitchUserTests(unittest.TestCase):
    def setUp(self):
        self.config_read = patch.object(helper.configparser.ConfigParser, 'read', return_value=[])
        self.config_read.start()
        self.addCleanup(self.config_read.stop)

    def test_discovery_requires_method_and_capability(self):
        for method, capability, expected in [(True, True, '/seat'), (False, True, ''), (True, False, '')]:
            xml = '<node><interface name="org.freedesktop.DisplayManager.Seat">' + ('<method name="SwitchToGreeter"/>' if method else '') + '</interface></node>'
            with self.subTest(method=method, capability=capability), patch.object(helper, 'property_value', side_effect=[['/seat'], capability]), patch.object(helper, 'bus', return_value=xml) as bus, patch.dict(os.environ, {'XDG_SEAT_PATH': ''}):
                self.assertEqual(helper.discover(), expected)
                self.assertNotIn('call', bus.call_args.args)

    def test_ambiguous_seats_are_hidden(self):
        with patch.object(helper, 'property_value', return_value=['/seat0', '/seat1']), patch.dict(os.environ, {'XDG_SEAT_PATH': ''}):
            self.assertEqual(helper.discover(), '')

    def test_only_multiple_accounts_probe_switching(self):
        user = SimpleNamespace(pw_name='astrid', pw_gecos='Astrid Solberg,Room', pw_uid=1000, pw_shell='/bin/bash')
        for count in [1, 3]:
            with patch.object(helper.pwd, 'getpwuid', return_value=user), patch.object(helper.pwd, 'getpwall', return_value=[user] * count), patch.object(helper, 'discover', return_value='/seat') as discover:
                result = helper.status()
                self.assertEqual(result['name'], 'Astrid Solberg')
                self.assertEqual(result['available'], count > 1)
                self.assertEqual(discover.call_count, int(count > 1))

    def test_unavailable_bus_hides_switch(self):
        user = SimpleNamespace(pw_name='astrid', pw_gecos='', pw_uid=1000, pw_shell='/bin/bash')
        with patch.object(helper.pwd, 'getpwuid', return_value=user), patch.object(helper.pwd, 'getpwall', return_value=[user] * 3), patch.object(helper, 'discover', side_effect=OSError):
            self.assertEqual(helper.status(), {'name': 'astrid', 'available': False, 'seat': ''})

    def test_explicit_switch_rechecks_and_never_calls_an_unavailable_seat(self):
        for available in [False, True]:
            with self.subTest(available=available), patch('sys.argv', ['switch-user.py', '--switch']), patch.object(helper, 'status', return_value={'available': available, 'seat': '/seat'}), patch.object(helper, 'bus') as bus:
                if available:
                    helper.main()
                    bus.assert_called_once_with('call', helper.SERVICE, '/seat', helper.INTERFACE, 'SwitchToGreeter')
                else:
                    with self.assertRaises(SystemExit):
                        helper.main()
                    bus.assert_not_called()

    def test_property_signatures(self):
        with patch.object(helper, 'bus', return_value='ao 2 "/seat0" "/seat1"'):
            self.assertEqual(helper.property_value('/', '', ''), ['/seat0', '/seat1'])
        with patch.object(helper, 'bus', return_value='b true'):
            self.assertIs(helper.property_value('/', '', ''), True)


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell needed for offscreen mocks')
class PresentationTests(unittest.TestCase):
    def test_preview_adapter_has_only_the_locked_user_and_no_switch_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'adapter.qml'
            fixture.write_text('''import QtQuick
import Quickshell
import "''' + ROOT.as_uri() + '''" as Lock
ShellRoot {
    Lock.AuthAdapter { id: auth; preview: true }
    Timer {
        interval: 100; running: true
        onTriggered: {
            if (auth.switchAvailable || auth.authenticating || auth.userModel.count !== 1) Qt.exit(1);
            else Qt.quit();
        }
    }
}
''')
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', XDG_RUNTIME_DIR=temporary,
                               XDG_CACHE_HOME=temporary, QML_IMPORT_PATH=str(ROOT.parent))
            result = subprocess.run(['quickshell', '-n', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('TypeError', result.stdout + result.stderr)

    def test_all_designs_with_one_and_three_users(self):
        with tempfile.TemporaryDirectory() as temporary:
            for count in [1, 3]:
                for design in sorted((ROOT / 'themes').rglob('Main.qml')):
                    with self.subTest(count=count, design=design.parent):
                        parser = configparser.ConfigParser(interpolation=None)
                        parser.optionxform = str
                        parser.read(design.parent / 'theme.conf')
                        settings = dict(parser['General'])
                        settings['reduceMotion'] = True
                        if settings.get('background') and not settings['background'].startswith('/'):
                            settings['background'] = (design.parent / settings['background']).as_uri()
                        environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                           QML_IMPORT_PATH=os.pathsep.join([str(ROOT.parent), str(ROOT / 'imports')]),
                                           EITR_RENDER_CONFIG=json.dumps(settings), XDG_RUNTIME_DIR=temporary, XDG_CACHE_HOME=temporary, EITR_RENDER_USERS=str(count),
                                           EITR_RENDER_DESIGN=design.as_uri(), EITR_RENDER_DELAY='150',
                                           EITR_RENDER_OUTPUT=str(Path(temporary) / 'render.png'))
                        result = subprocess.run(['quickshell', '-n', '-p', str(ROOT / 'references/render-preview.qml')],
                                                env=environment, capture_output=True, text=True, timeout=15)
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertNotIn('ReferenceError', result.stdout + result.stderr)
                        self.assertNotIn('TypeError', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
