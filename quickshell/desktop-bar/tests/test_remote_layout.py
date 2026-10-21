import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class RemoteLayoutTests(unittest.TestCase):
    def test_compact_controls_and_long_actions_in_both_themes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            for theme in ('dark', 'light'):
                renders = Path(os.environ.get('EITR_REMOTE_REVIEW_RENDERS') or folder)
                renders.mkdir(parents=True, exist_ok=True)
                capture = renders / (theme + '.png')
                background, foreground = ('#18212b', '#e9eef1') if theme == 'dark' else ('#f5f0e7', '#252936')
                state = {'tailscale': {'status': 'Verbunden', 'facts': [
                    {'label': 'Gerät', 'value': 'example-desktop'},
                    {'label': 'Tailscale-IP', 'value': '100.64.0.1'},
                    {'label': 'Netzwerk', 'value': 'example-network'}],
                    'actions': [{'menu': 'remote-away', 'source': 'Connect',
                                 'title': title, 'description': 'Eine ausführliche Beschreibung', 'icon': '\uf021'}
                                for title in ['Verbinden', 'Trennen', 'Detaillierter Status', 'Einrichtung für unterwegs zurücksetzen',
                                              'Gerät überprüfen', 'Zugriff einrichten']]}}
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 468; implicitHeight: 640
        Rectangle {
            id: sample
            anchors.fill: parent
            color: "BACKGROUND"
            Bar.RemoteAccessContent {
                id: panel
                x: 24; y: 24; width: 420
                kind: "tailscale"; state: STATE
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#7ee0b5"
            }
            Row {
                x: 24; y: 550; spacing: 8
                Bar.PanelButton { id: refresh; icon: true; text: "\\uf021"; loading: true; foreground: "FOREGROUND" }
                Bar.PanelSwitch { id: toggle; checked: true; foreground: "FOREGROUND"; accent: "#7ee0b5" }
            }
            Timer {
                interval: 700; running: true
                onTriggered: {
                    if (panel.implicitHeight > 500) throw new Error("Action grid grew too tall");
                    if (refresh.height !== toggle.height) throw new Error("Controls are not aligned");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        console.log("REMOTE_LAYOUT_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('STATE', json.dumps(state, ensure_ascii=False)).replace('BACKGROUND', background)
                    .replace('FOREGROUND', foreground).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='',
                                   LC_ALL='de_DE.UTF-8')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('REMOTE_LAYOUT_OK', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())
