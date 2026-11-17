"""A volume or brightness step updates the shown moment in place, without a cross-fade."""
from pathlib import Path
import tempfile
import unittest

from layout_render import copy_runtime, render, render_environment

FIXTURE = '''import QtQuick
import Quickshell
ShellRoot {
    FloatingWindow {
        width: 240; height: 32; color: "black"
        BarMoment {
            id: moment
            anchors.fill: parent
            host: QtObject { property bool verticalBar: false; property color fg: "white" }
        }
        Timer { interval: 100; running: true; onTriggered: moment.payload = {kind: "volume", level: 40, icon: "", text: "Volume"} }
        // After the first moment has faded in, a step must not start another fade.
        Timer {
            interval: 600; running: true
            onTriggered: {
                moment.payload = {kind: "volume", level: 45, icon: "", text: "Volume"};
                const step = [moment.mix, moment.previous === null, moment.shown.level];
                moment.payload = {kind: "notification", text: "Hello", icon: ""};
                const other = [moment.mix < 1, moment.previous && moment.previous.kind];
                console.log("LEVELS " + JSON.stringify({step: step, other: other}));
                Qt.quit();
            }
        }
    }
}
'''


class BarMomentLevelTests(unittest.TestCase):
    def test_level_steps_update_in_place_and_other_kinds_still_cross_fade(self):
        with tempfile.TemporaryDirectory(prefix='eitr-moment-levels-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'fixture.qml').write_text(FIXTURE)
            code, output = render(folder / 'fixture.qml', render_environment(folder), 15)
            self.assertEqual(code, 0, output)
            line = next((row for row in output.splitlines() if 'LEVELS ' in row), '')
            self.assertIn('"step":[1,true,45]', line, output)
            self.assertIn('"other":[true,"volume"]', line, output)
