"""Exercise the production bell and badge in both theme polarities."""
import json
from pathlib import Path
import tempfile
import unittest

from layout_render import capture_path, copy_runtime, render, render_environment


FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar
import "PanelStyle.js" as PanelStyle

FloatingWindow {
    id: fixture
    implicitWidth: 64
    implicitHeight: 40
    property int step: 0
    readonly property bool light: step >= 3
    readonly property int count: [0, 3, 120][step % 3]
    color: light ? "#f6f7fa" : "#191b22"

    QtObject {
        id: palette
        property int workspaceItemSize: 24
        property color workspaceMenuBg: fixture.color
        property color barFg: fixture.light ? "#20232d" : "#eef0fa"
        property color activeBg: fixture.light ? "#9e2c45" : "#fc9aa6"
        property color fg: barFg
    }
    Item {
        id: canvas
        anchors.fill: parent
        Rectangle { anchors.fill: parent; color: fixture.color }
        Bar.NotificationWidget {
            id: bell
            anchors.centerIn: parent
            host: palette
            notificationService: QtObject {
                property int count: fixture.count
                property bool doNotDisturb: false
            }
        }
    }
    Timer {
        interval: 80; running: true; repeat: true
        onTriggered: {
            const badge = bell.children[1];
            const pill = badge.children[0];
            const label = pill.children[0];
            const surface = PanelStyle.luminance(pill.color);
            const ink = PanelStyle.luminance(label.color);
            if (badge.visible !== (fixture.count > 0)
                || label.text !== (fixture.count > 99 ? "99+" : String(fixture.count))
                || (Math.max(surface, ink) + 0.05) / (Math.min(surface, ink) + 0.05) < 4.5
                || bell.width !== 24 || bell.height !== 24
                // The pill overlaps the glyph's top-right corner and may overhang the slot.
                || pill.x <= bell.width / 2 || pill.x >= bell.width || pill.y < 0)
                throw new Error("Bell badge visibility, label, contrast or slot geometry changed");
            const index = fixture.step;
            canvas.grabToImage(function(result) {
                if (!result.saveToFile(CAPTURES[index])) throw new Error("Bell capture failed");
                if (++fixture.step === 6) {
                    console.log("BELL_BADGE_OK");
                    Qt.quit();
                }
            });
        }
    }
}
'''


class CountBadgeRenderTests(unittest.TestCase):
    def test_bell_counts_keep_the_slot_fixed(self):
        with tempfile.TemporaryDirectory(prefix="eitr-bell-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            captures = [capture_path("BELL", directory, f"round3-bell-{count}-{theme}.png")
                        for theme in ("dark", "light") for count in (0, 3, 120)]
            fixture = folder / "fixture.qml"
            fixture.write_text(FIXTURE.replace("CAPTURES", json.dumps([str(path) for path in captures])))
            code, output = render(fixture, render_environment(folder), 12)
            self.assertEqual(code, 0, output)
            self.assertIn("BELL_BADGE_OK", output)
            for warning in ("ReferenceError", "TypeError", "Binding loop", "Unable to assign"):
                self.assertNotIn(warning, output)
            for capture in captures:
                self.assertGreater(capture.stat().st_size, 200)
