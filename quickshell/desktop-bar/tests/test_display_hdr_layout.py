import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required for offscreen rendering')
class DisplayHdrLayoutTests(unittest.TestCase):
    def test_hdr_controls_in_both_themes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as temporary:
            folder = Path(temporary)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            for theme in ('dark', 'light'):
                renders = Path(os.environ.get('EITR_REVIEW_RENDERS') or folder)
                renders.mkdir(parents=True, exist_ok=True)
                capture = renders / (theme + '.png')
                background, foreground = ('#18212b', '#e9eef1') if theme == 'dark' else ('#f5f0e7', '#252936')
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 420; implicitHeight: 420
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.DisplaySettingsEditor {
                id: panel
                x: 24; y: 24; width: 372
                monitor: ({hdr_capable: true, hdr: true, hdr_peak: 302, sdr_brightness: 1.4,
                    mode: "2560x1440@144", scale: "1", position: "0x0",
                    modes: ["2560x1440@144Hz"]})
                others: []; isMain: true
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#4c9b7d"
                onTryChange: function(key, value) {
                    if (key !== "hdr" || value !== "off") throw new Error("Wrong HDR toggle payload");
                }
            }
            function child(item, name) {
                if (item.objectName === name) return item;
                for (const candidate of item.children || []) {
                    const found = child(candidate, name);
                    if (found) return found;
                }
                return null;
            }
            Timer {
                interval: 700; running: true
                onTriggered: {
                    if (panel.height > sample.height - 48) throw new Error("Display editor clipped");
                    const toggle = sample.child(panel, "hdrSwitch");
                    const brightness = sample.child(panel, "sdrBrightness");
                    if (!toggle || !brightness || !toggle.visible || !brightness.visible)
                        throw new Error("HDR controls missing");
                    if (brightness.from !== 1 || brightness.to !== 2 || brightness.stepSize !== 0.1)
                        throw new Error("Wrong brightness range");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        panel.monitor = {hdr_capable: true, hdr: false};
                        if (brightness.visible) throw new Error("SDR slider visible with HDR off");
                        panel.monitor = {hdr_capable: false, hdr: false};
                        if (toggle.visible) throw new Error("HDR toggle visible on SDR hardware");
                        console.log("DISPLAY_HDR_LAYOUT_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', background).replace('FOREGROUND', foreground).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=temporary,
                                   XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='',
                                   LC_ALL='de_DE.UTF-8')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('DISPLAY_HDR_LAYOUT_OK', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())
