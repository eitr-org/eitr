import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required for offscreen rendering')
class AiUsageLayoutTests(unittest.TestCase):
    def test_one_and_two_providers(self):
        # Replace only the Wayland popup host; render the actual panel content.
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary)
            preference = folder / 'quickshell/desktop-bar/ai-usage-settings.json'
            preference.parent.mkdir(parents=True)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            (folder / 'ThemedPopup.qml').write_text('''import QtQuick
Item {
    property Item target
    property bool opened: false
    property color foreground
    property color background
    property color accent
    width: implicitWidth; height: implicitHeight
}
''')
            for count in (1, 2):
                capture = folder / 'capture.png'
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 468; implicitHeight: 520
        Rectangle {
            id: sample
            anchors.fill: parent; color: "#18212b"
            Bar.AiUsageMenu {
                id: panel
                target: sample
                foreground: "#e9eef1"; background: "#18212b"; accent: "#c4914f"
                maximumHeight: 500
            }
            Timer {
                interval: 300; running: true
                onTriggered: {
                    panel.usage = {providers: [
                        {name: "Claude", plan: "Max", windows: [{label: "5h window", used: 42}, {label: "Weekly", used: 68}]},
                        {name: "Codex", plan: "Plus", error: "Example offline error", windows: [{label: "Session", used: 23}]}
                    ]};
                    panel.selectedProviders = ["Claude"];
                    panel.toggleProvider(COUNT === 1 ? "Claude" : "Codex");
                    captureDelay.start();
                }
            }
            Timer {
                id: captureDelay
                interval: 300
                onTriggered: {
                    if (panel.height > panel.maximumHeight || panel.enabledProviders.length !== COUNT)
                        throw new Error("Invalid panel geometry or selection");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        console.log("AI_LAYOUT_OK");
                        Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('COUNT', str(count)).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('AI_LAYOUT_OK', result.stdout + result.stderr)
                self.assertGreater(capture.stat().st_size, 1000)
                self.assertEqual(json.loads(preference.read_text())['providers'],
                                 ['Claude'] if count == 1 else ['Claude', 'Codex'])
                capture.unlink()
