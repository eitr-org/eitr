"""The recording dot stays round when the layout switches between beside-the-clock and centred."""
from pathlib import Path
import tempfile
import unittest

from layout_render import copy_runtime, render, render_environment

FIXTURE = '''import Quickshell
import QtQuick
import "."
FloatingWindow {
  implicitWidth: 120; implicitHeight: 40
  QtObject { id: hostObj; property color fg: "white"; property color workspaceMenuBg: "black" }
  CaptureIndicator { id: capture; host: hostObj; recording: true }
  Timer { interval: 50; running: true; onTriggered: {
    const dot = capture.children[0].children[0].children[0];
    const sizes = [];
    for (const centered of [false, true, false, true, false]) {
      capture.centered = centered;
      sizes.push(dot.width + "x" + dot.height);
    }
    console.log("DOT_SIZES " + sizes.join(","));
    Qt.quit();
  } }
}
'''


class CaptureIndicatorRenderTests(unittest.TestCase):
    def test_dot_stays_round_across_layout_switches(self):
        with tempfile.TemporaryDirectory(prefix='eitr-capture-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / 'fixture.qml').write_text(FIXTURE)
            code, output = render(folder / 'fixture.qml', render_environment(folder), 15)
            self.assertEqual(code, 0, output)
            line = next((entry for entry in str(output).split('\n') if 'DOT_SIZES' in entry), '')
            self.assertIn('DOT_SIZES 6x6,6x6,6x6,6x6,6x6', line, output)


if __name__ == '__main__':
    unittest.main()
