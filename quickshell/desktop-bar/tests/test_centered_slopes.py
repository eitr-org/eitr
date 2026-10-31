"""Render the production Centered silhouette on every edge and expansion state."""
from bar_frame_source import frame_source
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

BAR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class CenteredSlopesTests(unittest.TestCase):
    def test_edges_collapsed_and_expanded(self):
        source = frame_source(BAR)
        outline = 'Shape {' + source.split('                Shape {\n                    id: centeredOutline', 1)[1].split('                Item {\n                    id: barContents', 1)[0]
        outline = outline.replace('\n                    visible:', '\n                    id: centeredOutline\n                    visible:', 1)
        self.assertNotIn('DesktopStyle.radius', outline)
        with tempfile.TemporaryDirectory(prefix='eitr-centered-slopes-') as directory:
            folder = Path(directory)
            shutil.copy(BAR / 'EdgeSlopes.js', folder)
            shutil.copy(BAR / 'CenteredBarMask.qml', folder)
            shutil.copy(BAR / 'BarGestureArea.qml', folder)
            shutil.copy(BAR / 'BarGeometry.js', folder)
            for edge in ('top', 'bottom', 'left', 'right'):
                for expanded in (False, True):
                    vertical = edge in ('left', 'right')
                    length = 300 if expanded else 100
                    depth = 60 if vertical else 30
                    captures = Path(os.environ.get('EITR_CENTERED_RENDERS', directory))
                    captures.mkdir(parents=True, exist_ok=True)
                    capture = captures / f'{edge}-{expanded}.png'
                    fixture = '''import QtQuick
import QtQuick.Shapes
import Quickshell
import "EdgeSlopes.js" as EdgeSlopes
ShellRoot {
    id: shell
    property bool centeredLayout: true
    property bool verticalBar: VERTICAL
    property string barEdge: EDGE
    property real tabBendRound: 6
    function barBackground() { return "#ffffff"; }
    FloatingWindow {
        visible: true; implicitWidth: 500; implicitHeight: 500; color: "#000000"
        Item {
            id: bar; anchors.fill: parent
            property real normalThickness: DEPTH
            Item { id: autoHide; property real progress: 1 }
            Item {
                id: barContents
                width: shell.verticalBar ? DEPTH : LENGTH
                height: shell.verticalBar ? LENGTH : DEPTH
                x: shell.verticalBar ? (shell.barEdge === "right" ? 500 - DEPTH : 0) : (500 - width) / 2
                y: shell.verticalBar ? (500 - height) / 2 : (shell.barEdge === "bottom" ? 500 - DEPTH : 0)
            }
            OUTLINE
            CenteredBarMask { id: input; surface: centeredOutline; edge: shell.barEdge; depth: DEPTH; bendRound: 6 }
            Timer {
                interval: 80; running: true
                onTriggered: {
                    if (input.regions.length !== DEPTH) throw new Error("missing slope input slices");
                    bar.grabToImage(function(result) {
                    if (!result.saveToFile(CAPTURE)) throw new Error("capture failed");
                    centeredOutline.visible = false;
                    Qt.callLater(function() {
                        if (input.regions.length !== 0) throw new Error("stale hidden slope input");
                        centeredOutline.visible = true;
                        Qt.callLater(function() {
                            if (input.regions.length !== DEPTH) throw new Error("slope input did not return");
                            console.log("CENTERED_OK"); Qt.quit();
                        });
                    });
                }); }
            }
        }
    }
}'''.replace('OUTLINE', outline).replace('VERTICAL', str(vertical).lower()).replace('EDGE', json.dumps(edge)).replace('LENGTH', str(length)).replace('DEPTH', str(depth)).replace('CAPTURE', json.dumps(str(capture)))
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                       HOME=directory, XDG_CONFIG_HOME=directory, XDG_RUNTIME_DIR=directory,
                                       DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
                    try:
                        result = subprocess.run(['quickshell', '-p', str(path)], env=environment,
                                                capture_output=True, text=True, timeout=15)
                    except subprocess.TimeoutExpired as error:
                        self.fail(f'{edge}/{expanded}: {error.stdout!r} {error.stderr!r}')
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    self.assertIn('CENTERED_OK', result.stdout + result.stderr)
                    image = Image.open(capture).convert('RGB')
                    start = (500 - length) // 2

                    def pixel(axis, inward):
                        x, y = (axis, inward) if edge == 'top' else (axis, 499-inward) if edge == 'bottom' else (inward, axis) if edge == 'left' else (499-inward, axis)
                        return image.getpixel((x, y))[0]

                    with self.subTest(edge=edge, expanded=expanded):
                        self.assertGreater(pixel(250, depth-1), 240)
                        self.assertGreater(pixel(start-15, 3), 240)
                        self.assertLess(pixel(start-15, depth-6), 15)
                        self.assertLess(pixel(start-depth-6, 1), 15)
                        self.assertGreater(pixel(start+10, 0), 240)
