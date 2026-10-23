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
    def test_one_two_and_four_providers_in_both_themes(self):
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
            # Renders stay in the temporary folder unless a reviewer asks to keep them.
            renders = Path(os.environ.get('EITR_REVIEW_RENDERS') or folder)
            renders.mkdir(parents=True, exist_ok=True)
            for count, theme in ((count, theme) for count in (1, 2, 4) for theme in ('dark', 'light')):
                capture = renders / f'ai-{count}-{theme}.png'
                preference.write_text(json.dumps({"version": 1, "providers": ["Codex"]}))

                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 468; implicitHeight: 768
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.AiUsageMenu {
                id: panel
                x: 24; y: 24
                width: 420
                target: sample
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#c4914f"
                maximumHeight: 720
            }
            Timer {
                interval: 300; running: true
                onTriggered: {
                    if (panel.foldedProviders.length !== 0) throw new Error("Legacy selection was not dropped");
                    panel.usage = {providers: [
                        {name: "Claude", accounts: [{id: "default", label: "Default", plan: "Max", windows: [{label: "5h window", used: 42}, {label: "Weekly", used: 68}]}, {id: "example", label: "Example account", error: "No data", windows: []}]},
                        {name: "Codex", accounts: [{label: "Default", plan: "Plus", error: "Example offline error", windows: [{label: "Session", used: 23}]}]},
                        {name: "Grok", accounts: [{label: "Default", plan: "Pro", windows: [{label: "Credits", used: 12}]}]},
                        {name: "Example AI", accounts: [{label: "Default", plan: "Pro", windows: [{label: "Session", used: 23}]}]}
                    ].slice(0, COUNT)};
                    if (COUNT === 4) panel.toggleProvider("Grok");
                    panel.status = "Last checked 12:00";
                    captureDelay.start();
                }
            }
            Timer {
                id: captureDelay
                interval: 300
                onTriggered: {
                    if (panel.height > panel.maximumHeight || panel.availableProviders.length !== COUNT)
                        throw new Error("Invalid panel geometry or providers");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        console.log("AI_LAYOUT_OK");
                        Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('COUNT', str(count)).replace('CAPTURE', str(capture))
                    .replace('BACKGROUND', '#f5f0e7' if theme == 'light' else '#18212b')
                    .replace('FOREGROUND', '#252936' if theme == 'light' else '#e9eef1'))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('AI_LAYOUT_OK', result.stdout + result.stderr)
                self.assertGreater(capture.stat().st_size, 1000)
                self.assertEqual(json.loads(preference.read_text()),
                                 {'version': 2, 'foldedProviders': ['Grok'] if count == 4 else []})
