"""Offscreen Cleaning mode overlay rendering, input blocking, and transient popup suppression."""
import json
from pathlib import Path
import tempfile
import unittest

from layout_render import BAR, capture_path, copy_runtime, render, render_environment

DARK = {"foreground": "#cdd6f4", "background": "#181824", "accent": "#89b4fa"}
LIGHT = {"foreground": "#203b30", "background": "#f3f8f1", "accent": "#32644c"}

RENDER_FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    id: root
    property int step: 0
    readonly property var states: [
        {name: "dark-idle", fg: "#cdd6f4", bg: "#181824", accent: "#89b4fa", progress: 0.0, holding: false},
        {name: "dark-holding", fg: "#cdd6f4", bg: "#181824", accent: "#89b4fa", progress: 0.65, holding: true},
        {name: "light-idle", fg: "#203b30", bg: "#f3f8f1", accent: "#32644c", progress: 0.0, holding: false},
        {name: "light-holding", fg: "#203b30", bg: "#f3f8f1", accent: "#32644c", progress: 0.65, holding: true}
    ]
    readonly property var current: states[step]
    FloatingWindow {
        visible: true
        implicitWidth: 960; implicitHeight: 600
        Rectangle {
            id: stage
            anchors.fill: parent
            // Simulate underlying desktop wallpaper/windows so translucent backdrop tint shows.
            gradient: Gradient {
                GradientStop { position: 0.0; color: root.current.bg }
                GradientStop { position: 1.0; color: Qt.tint(root.current.bg, Qt.alpha(root.current.accent, 0.35)) }
            }
            Rectangle {
                x: 40; y: 40; width: 280; height: 180; radius: 10
                color: Qt.alpha(root.current.accent, 0.25)
                border.width: 1; border.color: Qt.alpha(root.current.foreground, 0.3)
            }
            Bar.CleanOverlayContent {
                anchors.fill: parent
                foreground: root.current.fg
                background: root.current.bg
                accent: root.current.accent
                holdProgress: root.current.progress
                holdingEsc: root.current.holding
            }
        }
    }
    Timer {
        interval: 250; running: true; repeat: true
        onTriggered: stage.grabToImage(function(result) {
            if (!result.saveToFile("OUTPUT/clean-overlay-" + root.current.name + ".png")) {
                console.error("SAVE_FAILED");
                Qt.exit(1);
                return;
            }
            if (root.step + 1 >= root.states.length) {
                console.log("CLEAN_RENDER_OK");
                Qt.quit();
                return;
            }
            root.step += 1;
        })
    }
}
'''

INTERACTION_FIXTURE = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
    id: root
    property int escPressCount: 0
    property int escReleaseCount: 0
    property int leakedKeys: 0
    property int leakedClicks: 0
    property int leakedWheels: 0
    FloatingWindow {
        id: window
        visible: true
        implicitWidth: 640; implicitHeight: 420
        Item {
            id: under
            anchors.fill: parent
            Keys.onPressed: event => { root.leakedKeys += 1; event.accepted = true; }
            MouseArea {
                anchors.fill: parent
                acceptedButtons: Qt.AllButtons
                onPressed: root.leakedClicks += 1
                onWheel: root.leakedWheels += 1
            }
            Bar.CleanOverlayContent {
                id: overlay
                anchors.fill: parent
                focus: true
                foreground: "#cdd6f4"
                background: "#181824"
                accent: "#89b4fa"
                onEscPressed: root.escPressCount += 1
                onEscReleased: root.escReleaseCount += 1
            }
        }
    }
    TestCase {
        name: "CleanOverlayInteraction"
        when: window.visible
        function find(item, name) {
            if (item.objectName === name) return item;
            for (const child of item.children || []) {
                const hit = find(child, name);
                if (hit) return hit;
            }
            return null;
        }
        function test_eats_input_and_tracks_escape() {
            wait(100);
            overlay.forceActiveFocus();
            const blocker = find(overlay, "cleanOverlayMouseBlocker");
            verify(blocker !== null);
            compare(blocker.cursorShape, Qt.BlankCursor);
            compare(blocker.acceptedButtons, Qt.AllButtons);
            mouseClick(blocker, 100, 100, Qt.LeftButton);
            mouseClick(blocker, 100, 100, Qt.RightButton);
            mouseWheel(blocker, 100, 100, 0, 120);
            compare(root.leakedClicks, 0);
            compare(root.leakedWheels, 0);
            keyClick(Qt.Key_A);
            keyClick(Qt.Key_Space);
            keyClick(Qt.Key_Return);
            compare(root.leakedKeys, 0);
            compare(root.escPressCount, 0);
            keyPress(Qt.Key_Escape);
            compare(root.escPressCount, 1);
            keyRelease(Qt.Key_Escape);
            compare(root.escReleaseCount, 1);
            compare(root.leakedKeys, 0);
            console.log("CLEAN_INTERACTION_OK");
            Qt.quit();
        }
    }
}
'''


class CleanOverlayTests(unittest.TestCase):
    def test_overlay_and_notification_suppression_wiring(self):
        overlay = (BAR / "panels/CleanOverlay.qml").read_text()
        self.assertIn("WlrLayershell.layer: WlrLayer.Overlay", overlay)
        self.assertIn("WlrLayershell.keyboardFocus: overlay.active ? WlrKeyboardFocus.Exclusive : WlrKeyboardFocus.None", overlay)
        self.assertIn('WlrLayershell.namespace: "desktop-clean"', overlay)
        self.assertIn("Variants {", overlay)
        self.assertIn("IdleInhibitor {", overlay)
        self.assertIn('target: "clean"', overlay)

        shell = (BAR / "shell.qml").read_text()
        self.assertIn("transientSuppress: cleanOverlay.active", shell)
        self.assertIn("CleanOverlay {", shell)

        service = (BAR / "notifications/NotificationService.qml").read_text()
        self.assertIn("property bool transientSuppress: false", service)
        self.assertIn("readonly property bool popupsSuppressed: doNotDisturb || transientSuppress", service)
        self.assertIn("onPopupsSuppressedChanged: if (popupsSuppressed) popupIds = []", service)
        # Saved DND binding stays untouched so transient suppression never persists as DND.
        self.assertIn('Binding { target: EventSounds; property: "doNotDisturb"; value: service.doNotDisturb }', service)

        registry = (BAR / "qmldir").read_text()
        self.assertIn("CleanOverlay panels/CleanOverlay.qml", registry)
        self.assertIn("CleanOverlayContent panels/CleanOverlayContent.qml", registry)

    def test_transient_suppression_preserves_saved_dnd(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            settings_dir = folder / "quickshell/desktop-bar"
            settings_dir.mkdir(parents=True, exist_ok=True)
            settings_file = settings_dir / "notification-settings.json"
            settings_file.write_text('{"version":1,"doNotDisturb":false}\n')
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    Bar.NotificationService {
        id: service
    }
    Timer {
        interval: 200; running: true
        onTriggered: {
            if (service.doNotDisturb !== false || service.popupsSuppressed !== false) {
                console.error("INITIAL_STATE_BAD"); Qt.exit(1); return;
            }
            service.popupIds = [42];
            service.transientSuppress = true;
            if (service.popupsSuppressed !== true || service.popupIds.length !== 0 || service.doNotDisturb !== false) {
                console.error("SUPPRESS_FAILED"); Qt.exit(1); return;
            }
            service.transientSuppress = false;
            if (service.popupsSuppressed !== false || service.doNotDisturb !== false) {
                console.error("RESTORE_FAILED"); Qt.exit(1); return;
            }
            console.log("TRANSIENT_DND_OK");
            Qt.quit();
        }
    }
}
'''
            (folder / "transient.qml").write_text(fixture)
            code, output = render(folder / "transient.qml", render_environment(folder), 15)
            self.assertEqual(code, 0, output)
            self.assertIn("TRANSIENT_DND_OK", output)
            self.assertEqual(json.loads(settings_file.read_text())["doNotDisturb"], False)

    def test_offscreen_render_light_and_dark_themes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            output = capture_path("CLEAN_OVERLAY", directory, "probe").parent
            (folder / "render.qml").write_text(RENDER_FIXTURE.replace("OUTPUT", str(output)))
            code, log = render(folder / "render.qml", render_environment(folder, (960, 600)), 30)
            self.assertEqual(code, 0, log)
            self.assertIn("CLEAN_RENDER_OK", log)
            for diagnostic in ("FAIL!", "TypeError:", "ReferenceError:", "Binding loop", "QML error"):
                self.assertNotIn(diagnostic, log)
            for name in ("dark-idle", "dark-holding", "light-idle", "light-holding"):
                png = output / f"clean-overlay-{name}.png"
                self.assertTrue(png.is_file(), f"Missing {png}")
                self.assertGreater(png.stat().st_size, 5000)

    def test_offscreen_interaction_eats_events_and_tracks_esc(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / "interact.qml").write_text(INTERACTION_FIXTURE)
            code, log = render(folder / "interact.qml", render_environment(folder, (640, 420)), 20)
            self.assertEqual(code, 0, log)
            self.assertIn("CLEAN_INTERACTION_OK", log)
            self.assertNotIn("FAIL!", log)


if __name__ == "__main__":
    unittest.main()
