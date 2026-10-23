"""Exercise the clock offscreen without contacting the desktop session."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class TimePickerTests(unittest.TestCase):
    def test_render_and_keyboard_response_in_both_themes(self):
        for background, foreground in (('#202024', '#ffffff'), ('#eeeeee', '#202024')):
            with self.subTest(background=background), tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                for source in BAR.iterdir():
                    if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                        shutil.copy(source, folder / source.name)
                source = (folder / 'TimePicker.qml').read_text()
                # FloatingWindow supplies the offscreen surface in place of a Wayland layer.
                source = source.replace('id: picker', 'id: picker\n    property alias keyTarget: content', 1)
                source = source.replace('PanelWindow {', 'FloatingWindow {\n        implicitWidth: 800; implicitHeight: 600')
                source = '\n'.join(line for line in source.splitlines() if not any(
                    token in line for token in ('anchors { top:', 'exclusionMode:', 'WlrLayershell.')))
                (folder / 'TimePicker.qml').write_text(source)
                fixture = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
    Bar.TimePicker { id: picker; background: "BACKGROUND"; foreground: "FOREGROUND" }
    TestCase { id: keyboard; name: "ClockKeyboard"; when: false }
    Timer {
        interval: 300; running: true
        onTriggered: {
            for (const request of ["../invalid", "bad\\n", "", "a".repeat(65)]) {
                picker.open(request, "Question", "", "09:00");
                if (picker.opened) { Qt.exit(1); return; }
            }
            picker.open("typed", "At what time?", "Dentist appointment", "12:00");
            render.start();
        }
    }
    Timer {
        id: render; interval: 300
        onTriggered: {
            picker.keyTarget.grabToImage(function(result) {
                result.saveToFile("CAPTURE");
                picker.keyTarget.forceActiveFocus();
                // A full field can be typed again: 21:00, then 09:30.
                for (const key of [Qt.Key_2, Qt.Key_1, Qt.Key_0, Qt.Key_0, Qt.Key_0, Qt.Key_9, Qt.Key_3, Qt.Key_0])
                    keyboard.keyClick(key);
                keyboard.keyClick(Qt.Key_Return);
                finish.start();
            });
        }
    }
    Timer {
        id: finish; interval: 400
        onTriggered: {
            if (picker.opened) { Qt.exit(1); return; }
            picker.open("invalid", "At what time?", "", "12:00");
            picker.keyTarget.forceActiveFocus();
            keyboard.keyClick(Qt.Key_2);
            keyboard.keyClick(Qt.Key_5);
            keyboard.keyClick(Qt.Key_9);
            keyboard.keyClick(Qt.Key_9);
            if (picker.valid || picker.value !== "25:99") { Qt.exit(1); return; }
            keyboard.keyClick(Qt.Key_Return);
            if (!picker.opened) { Qt.exit(1); return; }
            keyboard.keyClick(Qt.Key_Escape);
            cancelled.start();
        }
    }
    Timer {
        id: cancelled; interval: 400
        onTriggered: { if (picker.opened) Qt.exit(1); else { console.log("CLOCK_OK"); Qt.quit(); } }
    }
}'''.replace('BACKGROUND', background).replace('FOREGROUND', foreground).replace('CAPTURE', str(folder / 'clock.png'))
                (folder / 'fixture.qml').write_text(fixture)
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), XDG_CONFIG_HOME=directory,
                                   XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(folder / 'fixture.qml')],
                                        env=environment, capture_output=True, text=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('CLOCK_OK', result.stdout + result.stderr)
                self.assertTrue((folder / 'clock.png').is_file())
                self.assertEqual((folder / 'eitr-time-picker/typed').read_text(), '09:30\n')
                self.assertEqual((folder / 'eitr-time-picker/invalid').read_text(), '')
