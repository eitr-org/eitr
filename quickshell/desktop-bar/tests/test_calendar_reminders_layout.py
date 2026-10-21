import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class CalendarReminderLayoutTests(unittest.TestCase):
    def test_reminder_list_is_bounded_and_fixed_in_both_themes(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            folder = Path(directory)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            (folder/'ThemedPopup.qml').write_text('''import QtQuick
Item {
    property bool opened: true
    property var keyTarget
    property color foreground
    property color background
    property color accent
    property var contentGaps: [4,4,4,4]
    property bool detached: true
    property string barEdge: "top"
    property real verticalContentInset: 0
    width: implicitWidth; height: implicitHeight
}
''')
            for theme in ('dark', 'light'):
                capture = folder/(theme+'.png')
                fixture = folder/'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true
        implicitWidth: 560; implicitHeight: 700
        Rectangle {
            id: sample
            anchors.fill: parent; color: "BACKGROUND"
            Bar.CalendarMenu {
                id: panel
                x: 12; y: 12
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#509475"
            }
            property real emptyHeight: 0
            Timer {
                interval: 250; running: true
                onTriggered: {
                    const day = new Date(2026, 9, 30, 15);
                    panel.selectedDay = day; panel.viewYear = 2026; panel.viewMonth = 9;
                    sample.emptyHeight = panel.height;
                    panel.reminders = Array.from({length: 20}, function(unused, index) {
                        return {id: String(index), text: "Dentist appointment with a deliberately long title for wrapping", due: day.getTime()/1000};
                    });
                    finish.start();
                }
            }
            Timer {
                id: finish; interval: 250
                onTriggered: {
                    if (panel.height > sample.height - 24 || panel.selectedReminders.length !== 20)
                        throw new Error("Calendar overflow or missing reminders: " + panel.height + "/" + panel.selectedReminders.length);
                    // The calendar keeps one height whether a day has reminders or not.
                    if (panel.height !== sample.emptyHeight)
                        throw new Error("Calendar height changed: " + sample.emptyHeight + " -> " + panel.height);
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE"); console.log("CALENDAR_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', '#18212b' if theme=='dark' else '#f5f0e7')
                    .replace('FOREGROUND', '#e9eef1' if theme=='dark' else '#252936')
                    .replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT/'quickshell'), XDG_CONFIG_HOME=directory,
                                   XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                try:
                    result = subprocess.run(['quickshell','-p',str(fixture)], env=environment,
                                            capture_output=True, text=True, timeout=15)
                except subprocess.TimeoutExpired as error:
                    self.fail(str(error.stdout) + str(error.stderr))
                self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
                self.assertIn('CALENDAR_OK', result.stdout+result.stderr)
                self.assertTrue(capture.exists())
                if os.environ.get('EITR_CALENDAR_REVIEW_RENDERS'):
                    destination = Path(os.environ['EITR_CALENDAR_REVIEW_RENDERS'])
                    destination.mkdir(parents=True, exist_ok=True)
                    shutil.copy(capture, destination/capture.name)
