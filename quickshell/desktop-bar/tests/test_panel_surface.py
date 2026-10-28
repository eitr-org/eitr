from pathlib import Path
import unittest
import os
import shutil
import subprocess
import tempfile
import json


class PanelSurfaceTests(unittest.TestCase):
    def test_background_uses_reactive_geometry_not_cached_canvas(self):
        source = (Path(__file__).resolve().parents[1] / "PanelSurface.qml").read_text()
        self.assertIn("import QtQuick.Shapes", source)
        self.assertIn("fillColor: surface.color", source)
        self.assertIn("data: [Item {", source)
        self.assertNotIn("Canvas {", source)
        self.assertNotIn("requestPaint()", source)


class PanelMotionTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_plugin_reload_and_review_release_panel_grab(self):
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            fixture = folder / 'shell.qml'
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        id: window
        visible: true; implicitWidth: 500; implicitHeight: 400
        property Item stripItem: strip
        Item { id: strip; width: 500; height: 30 }
        Bar.ThemedPopup {
            id: panel; target: strip
            foreground: "white"; background: "black"; accent: "cyan"
            implicitWidth: 300; implicitHeight: 200
        }
        Timer {
            interval: 200; running: true; repeat: true
            property int stage: 0
            onTriggered: {
                if (stage === 0) panel.opened = true;
                else if (stage === 1) {
                    if (!panel.grabReady) throw new Error("Opening did not arm grab");
                    panel.target = null;
                    if (panel.opened) throw new Error("Lost anchor left panel open");
                    panel.target = strip;
                    panel.opened = true;
                } else if (stage === 2) {
                    Bar.PluginRegistry.reviewStarted();
                    if (panel.opened) throw new Error("Review left panel open");
                    if (panel.grabReady) throw new Error("Review left grab armed");
                    console.log("PLUGIN_GRAB_RELEASE_OK"); Qt.quit();
                }
                stage++;
            }
        }
    }
}'''.replace('BAR', bar.as_uri()))
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=temporary,
                XDG_CONFIG_HOME=temporary, XDG_STATE_HOME=temporary, XDG_DATA_HOME=temporary,
                XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                text=True, capture_output=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('PLUGIN_GRAB_RELEASE_OK', output)

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_single_motion_with_retargeted_size(self):
        bar = Path(__file__).resolve().parents[1]
        for reduced, first_result in ((False, 20), (False, 180), (True, 20)):
            with self.subTest(reduced=reduced, first_result=first_result), tempfile.TemporaryDirectory() as temporary:
                folder = Path(temporary)
                for source in bar.iterdir():
                    if source.suffix in ('.qml', '.js', '.json') or source.name == 'qmldir':
                        shutil.copy(source, folder / source.name)
                captures = Path(os.environ.get('EITR_PANEL_REVIEW_RENDERS', temporary))
                captures.mkdir(parents=True, exist_ok=True)
                stem = 'motion-reduced' if reduced else ('motion-cap' if first_result > 100 else 'motion-full')
                capture = captures / (stem + '.png')
                fixture = folder / 'fixture.qml'
                fixture.write_text(FIXTURE.replace('REDUCED', json.dumps(reduced)).replace('CAPTURE', str(capture)).replace('FIRST_RESULT', str(first_result)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                    QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=temporary,
                    XDG_CONFIG_HOME=temporary, XDG_STATE_HOME=temporary, XDG_DATA_HOME=temporary,
                    XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                    DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                    text=True, capture_output=True, timeout=10)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn('PANEL_MOTION_OK', output, output)
                self.assertTrue(capture.is_file())
                if os.environ.get('EITR_PANEL_REVIEW_RENDERS'):
                    (captures / (stem + '.log')).write_text(output)

FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        id: window
        visible: true; implicitWidth: 620; implicitHeight: 540
        property bool centeredLayout: false
        property bool notchLayout: false
        property var outerGaps: [12, 12, 12, 12]
        property Item stripItem: strip
        property real panelGap: 12
        property var panelFocusWindows: [window]
        Rectangle {
            id: sample
            anchors.fill: parent; color: "#18212b"
            Rectangle { id: strip; width: parent.width; height: 30; color: "#293743" }
        }
        Bar.ThemedPopup {
            id: panel
            parent: sample
            target: strip; foreground: "#e9eef1"; background: "#18212b"; accent: "#7ee0b5"
            waitForFreshData: true
            implicitWidth: 500
            implicitHeight: snapshot.length ? snapshot[0].height : 300
            property var snapshot: []
            property int resetsDuringReveal: 0
            property int resets: 0
            onSnapshotChanged: {
                resets++;
                if (revealProgress > 0 && revealProgress < 1) resetsDuringReveal++;
            }
            Column {
                width: parent.width; spacing: 18
                Bar.PanelHeading { text: "Panel motion fixture"; foreground: panel.foreground; accent: panel.accent }
                Text { text: "Stable content during reveal"; color: panel.foreground }
                Bar.PanelSwitch { checked: Bar.DesktopStyle.reduceMotion; foreground: panel.foreground; accent: panel.accent }
            }
        }
        property double started: 0
        property double stableAt: 0
        property int samples: 0
        property int resetsBefore: 0
        property real settledHeight: 0
        property bool revealFinished: false
        property string failure: ""
        property int motions: 0
        property bool moving: false
        property real previousExtent: 0
        property double revealAt: 0
        property double revealEnd: 0
        Timer { interval: 100; running: true; onTriggered: {
            Bar.DesktopStyle.reduceMotion = REDUCED;
            window.resetsBefore = panel.resets;
            window.started = Date.now(); panel.opened = true;
            updates.start(); frames.start(); finish.start();
        } }
        Timer { id: updates; interval: 20; repeat: true; onTriggered: {
            const elapsed = Date.now() - window.started;
            if (elapsed < FIRST_RESULT) return;
            const revealing = panel.transitioning;
            const previousHeight = panel.height;
            panel.applySnapshot("snapshot", [{name: "fixture", height: elapsed > FIRST_RESULT + 130 ? 400 : 350}]);
            if (revealing && panel.height !== previousHeight) window.failure = "Size jumped during reveal";
            if (Date.now() - window.started > FIRST_RESULT + 160) stop();
        } }
        Timer { id: frames; interval: 16; repeat: true; onTriggered: {
            window.samples++;
            if (panel.revealProgress === 1 && panel.height === 400 && window.stableAt === 0) window.stableAt = Date.now() - window.started;
            if (panel.revealProgress > 0 && window.revealAt === 0) window.revealAt = Date.now();
            const extent = panel.height * panel.revealProgress;
            const moving = Math.abs(extent - window.previousExtent) > 0.001;
            if (moving && !window.moving) window.motions++;
            window.moving = moving;
            window.previousExtent = extent;
            if (!REDUCED && window.revealFinished && panel.height !== window.settledHeight) window.failure = "Second size motion after reveal";
            if (panel.revealProgress === 1 && !window.revealFinished) {
                window.revealFinished = true;
                window.settledHeight = panel.height;
                window.revealEnd = Date.now();
                if (!REDUCED && panel.height !== 400) window.failure = "Reveal ended before final size";
            }
        } }
        Timer { id: finish; interval: 850; onTriggered: {
            frames.stop(); updates.stop();
            if (!REDUCED && window.stableAt > Math.min(FIRST_RESULT, 100) + 360) window.failure = "Opening missed shared deadline";
            if (window.revealAt - window.started > 135) window.failure = "Preparation exceeded cap";
            if (window.failure) { console.error(window.failure); Qt.exit(1); return; }
            if (window.motions !== (REDUCED ? 2 : 1)) throw new Error("Expected one continuous opening motion: " + window.motions);
            if (panel.resets - window.resetsBefore !== 2) throw new Error("Equal model rebuilt");
            if (REDUCED && window.stableAt > 220) throw new Error("Reduced motion was animated");
            console.log("PANEL_MEASURE " + JSON.stringify({reduced: REDUCED, firstStableFrameMs: window.stableAt, frames: window.samples, motions: window.motions, revealMs: window.revealEnd - window.revealAt, resetsDuringReveal: panel.resetsDuringReveal}));
            sample.grabToImage(function(result) {
                result.saveToFile("CAPTURE");
                console.log("PANEL_MOTION_OK"); Qt.quit();
            });
        } }
    }
}
'''
