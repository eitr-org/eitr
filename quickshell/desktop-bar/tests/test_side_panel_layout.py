"""Render real shared surfaces and menus with inert Control Center geometry."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest

from layout_render import BAR, EDGES, copy_runtime, render, render_environment


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class SidePanelLayoutTests(unittest.TestCase):
    def test_attachment_and_content_on_every_edge(self):
        with tempfile.TemporaryDirectory(prefix='eitr-side-panels-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            source = (BAR / 'panels/ControlCenter.qml').read_text()
            # Keep the production size/placement bindings, without starting settings queries.
            bindings = '\n'.join(re.findall(
                r'^    (?:readonly property real edgeClearance:|implicitWidth:|implicitHeight:|leadingOffset:|barEdge:|leftAligned:).*$',
                source, re.MULTILINE))
            # Inert capture state: render the real RecordingMenu without a broker.
            (folder / 'services/ObsStatus.qml').write_text("""pragma Singleton
import QtQuick
QtObject {
    property int detailObservers: 0
    property var details: null
    signal detailsReceived(var snapshot)
    function refresh() {}
}
""")
            failures = []
            for edge in EDGES:
                for kind in ('center', 'workspace', 'small', 'small-center', 'small-right', 'recording'):
                    capture_dir = Path(os.environ.get('EITR_SIDE_RENDERS', directory))
                    capture_dir.mkdir(parents=True, exist_ok=True)
                    capture = capture_dir / f'{kind}-{edge}.png'
                    panel = {
                        'center': '''Bar.ThemedPopup {
                            property string barPosition: window.edge
                            property var screenMargins: window.outerGaps
                            BINDINGS
                            Rectangle { anchors.fill: parent; color: "#39434b"
                                Text { anchors.centerIn: parent; text: "Control Center content"; color: "white" }
                            }
                        }'''.replace('BINDINGS', bindings),
                        'workspace': '''Bar.WorkspaceStyleMenu {
                            barEdge: window.edge
                            currentStyle: "Runes"; selectedForeground: "black"
                        }''',
                        # All other content-sized menus use this same shared inset contract.
                        'small': '''Bar.ThemedPopup {
                            barEdge: window.edge; leftAligned: true
                            implicitWidth: 300
                            implicitHeight: rows.implicitHeight + verticalContentInset
                            Column { id: rows; width: parent.width; spacing: 6
                                Repeater { model: 4
                                    Rectangle { width: parent.width; height: 36; color: "#39434b"
                                        required property int index
                                        Text { anchors.centerIn: parent; text: "Option " + (parent.index + 1); color: "white" }
                                    }
                                }
                            }
                        }''',
                    }.get(kind, '''Bar.RecordingMenu {
                        barEdge: window.edge
                        controller: QtObject {
                            property var obsState: ({ready: false, recording: true, streaming: false, paused: false})
                            property bool busy: false
                        }
                    }''')
                    if kind.startswith('small-'):
                        panel = '''Bar.ThemedPopup {
                            barEdge: window.edge
                            alignment: ALIGNMENT
                            implicitWidth: 300
                            implicitHeight: rows.implicitHeight + verticalContentInset
                            Column { id: rows; width: parent.width; spacing: 6
                                Repeater { model: 4
                                    Rectangle { width: parent.width; height: 36; color: "#39434b" }
                                }
                            }
                        }'''.replace('ALIGNMENT', json.dumps(kind.split('-')[1]))
                    panel = panel.replace('{', '''{
                        id: panel; parent: sample; target: strip
                        foreground: "#f3e6df"; background: "#2b2020"; accent: "#ee8855"
                        opened: true
''', 1)
                    fixture = FIXTURE.replace('PANEL', panel).replace('EDGE', json.dumps(edge)).replace(
                        'KIND', json.dumps(kind)).replace('CAPTURE', json.dumps(str(capture)))
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    code, output = render(path, render_environment(directory), 10)
                    self.assertEqual(code, 0, output)
                    self.assertIn('SIDE_MEASURE', output)
                    self.assertTrue(capture.is_file(), output)
                    self.assertNotIn('Binding loop', output)
                    self.assertNotIn('ReferenceError', output)
                    self.assertNotIn('TypeError', output)
                    if 'SIDE_FAILURE' in output:
                        failures.append(output[output.index('SIDE_FAILURE'):])
            self.assertFalse(failures, '\n'.join(failures))


FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        id: window
        visible: true; implicitWidth: 800; implicitHeight: 600
        color: "#111820"
        property string edge: EDGE
        property bool vertical: edge === "left" || edge === "right"
        property bool centeredLayout: false
        property bool notchLayout: false
        property bool islandsLayout: false
        property real panelGap: 12
        property var outerGaps: [10, 11, 12, 13]
        property var panelFocusWindows: []
        property Item stripItem: strip
        Item {
        id: sample; anchors.fill: parent
        Rectangle {
            id: strip; color: "#2b2020"
            width: window.vertical ? 30 : window.width
            height: window.vertical ? window.height : 30
            x: window.edge === "right" ? window.width - width : 0
            y: window.edge === "bottom" ? window.height - height : 0
        }
        PANEL
        }
        Bar.ThemedPopup {
            id: reference; parent: sample; target: strip; barEdge: window.edge; leftAligned: true
            foreground: "white"; background: "black"; accent: "cyan"
            implicitWidth: 200; implicitHeight: 200
        }
        Component.onCompleted: Bar.DesktopStyle.reduceMotion = true
        Timer {
            interval: 350; running: true
            onTriggered: {
                let failures = [];
                function check(condition, message) { if (!condition) failures.push(message); }
                const surface = panel.children.find(child => child.toString().startsWith("PanelSurface"));
                const frame = surface.children[0].children.find(child => child.objectName === "panelContentFrame");
                if (KIND === "center") {
                    if (window.vertical) {
                        check(panel.y === reference.y && panel.x === (window.edge === "left" ? reference.x : strip.x - panel.width),
                            "Control Center must share Full-panel attachment");
                        check(panel.y === 0, "Control Center must start at screen top");
                        check(panel.height === window.height, "Control Center must use screen height");
                        check(surface.flushLeading && surface.flushTrailing, "Control Center must meet both screen ends");
                        check(frame.y === 20, "Control Center content must use shared top padding");
                    } else {
                        check(panel.height === 570 - (window.edge === "top" ? 12 : 10), "horizontal height changed");
                    }
                } else {
                    const body = frame.children[0];
                    const column = body.children.find(child => child.toString().startsWith("QQuickColumn"));
                    check(column !== undefined, "missing content column");
                    if (column) {
                        check(column.implicitHeight <= body.height, "rows clipped: " + column.implicitHeight + " > " + body.height);
                        for (const row of column.children) {
                            if (row.height > 0) check(row.y + row.height <= body.height, "last row extends beyond clip");
                        }
                    }
                }
                check(panel.x >= 0 && panel.y >= 0 && panel.x + panel.width <= window.width
                    && panel.y + panel.height <= window.height, "panel outside screen");
                console.log("SIDE_MEASURE", KIND, window.edge, JSON.stringify({x:panel.x, y:panel.y,
                    width:panel.width, height:panel.height, frameHeight:frame.height}));
                sample.grabToImage(function(result) {
                    result.saveToFile(CAPTURE);
                    if (failures.length) console.log("SIDE_FAILURE", KIND, window.edge, failures.join("; "));
                    Qt.quit();
                });
            }
        }
    }
}
'''
