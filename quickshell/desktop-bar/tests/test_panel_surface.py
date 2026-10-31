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

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_updates_wait_for_the_unfold_and_revealed_fires_once(self):
        """Data arriving mid-unfold is applied after it, so the panel never re-lays out while moving."""
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'shell.qml'
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
            property string value: "old"
            property int revealCount: 0
            property bool checked: false
            onRevealed: revealCount++
            onRevealProgressChanged: {
                if (checked || revealProgress <= 0.2 || revealProgress >= 1) return;
                checked = true;
                updateContent(function() { value = "new"; });
                if (value !== "old") throw new Error("Update applied during the unfold");
            }
        }
        Timer {
            interval: 500; running: true; repeat: true
            property int stage: 0
            onTriggered: {
                if (stage === 0) panel.opened = true;
                else {
                    if (!panel.checked) throw new Error("Unfold was never observed");
                    if (panel.value !== "new") throw new Error("Deferred update was lost");
                    if (panel.revealCount !== 1) throw new Error("revealed fired " + panel.revealCount + " times");
                    console.log("DEFERRED_UPDATES_OK"); Qt.quit();
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
            self.assertIn('DEFERRED_UPDATES_OK', output)

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


class PanelPlacementTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_real_popup_edge_contact_has_no_binding_loops(self):
        bar = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary) / 'shell.qml'
            fixture.write_text(PLACEMENT_FIXTURE.replace('BAR', bar.as_uri()))
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                QML_IMPORT_PATH=str(bar.parent), EITR_CODE_ROOT=temporary,
                HOME=temporary, XDG_CONFIG_HOME=temporary, XDG_STATE_HOME=temporary,
                XDG_DATA_HOME=temporary, XDG_CACHE_HOME=temporary, XDG_RUNTIME_DIR=temporary,
                DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                text=True, capture_output=True, timeout=30)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('PLACEMENT_OK 294', output)
            self.assertNotIn('Binding loop detected', output)
            self.assertNotIn('ReferenceError', output)
            self.assertNotIn('TypeError', output)


PLACEMENT_FIXTURE = '''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        id: window
        visible: true; implicitWidth: 600; implicitHeight: 600
        property string layout: "full"
        property bool centeredLayout: layout === "centered"
        property bool notchLayout: layout === "tabs"
        property bool islandsLayout: layout === "islands"
        property real islandGap: 6
        property real panelGap: 24
        property var outerGaps: [12, 12, 12, 12]
        property Item stripItem: strip
        property string edge: "top"
        property bool vertical: edge === "left" || edge === "right"
        Item {
            id: strip
            width: window.vertical ? 30 : 600
            height: window.vertical ? 600 : 30
            x: window.edge === "right" ? 570 : 0
            y: window.edge === "bottom" ? 570 : 0
        }
        Bar.WorkspaceStyleMenu {
            id: workspaceMenu
            target: window.stripItem
            currentStyle: "Numbers"; selectedForeground: "black"
            foreground: "white"; background: "black"; accent: "cyan"
        }
        Component {
            id: popupComponent
            Bar.ThemedPopup {
                id: popup
                parent: window.contentItem
                target: window.stripItem; barEdge: window.edge
                foreground: "white"; background: "black"; accent: "cyan"
                property real baseExtent: 260
                property real offset: 0
                leadingOffset: offset
                // The same size feedback as a content-sized menu, on either axis.
                edgeContactWidth: window.vertical ? 200 : baseExtent
                edgeContactHeight: window.vertical ? baseExtent : 200
                implicitWidth: window.vertical ? 200 : baseExtent + horizontalContentInset - 48
                implicitHeight: window.vertical ? baseExtent + surface.leadingBodyInset + surface.trailingBodyInset : 200
                property var surface: children.find(child => child.toString().startsWith("PanelSurface"))
            }
        }
        property var cases: []
        property var panel: null
        property int current: 0
        Component.onCompleted: {
            Bar.DesktopStyle.reduceMotion = true;
            for (var edge of ["top", "bottom", "left", "right"])
                for (var layout of ["full", "centered", "tabs", "islands"])
                    for (var alignment of ["left", "center", "right"])
                        for (var extent of [260, 600, 640])
                            for (var light of [false, true])
                                cases.push({edge: edge, layout: layout, alignment: alignment, extent: extent, light: light, offset: 0});
            // A vertical leading offset must survive until the screen clamp wins.
            for (var edge of ["left", "right"])
                for (var extent of [260, 600, 640])
                    cases.push({edge: edge, layout: "full", alignment: "left", extent: extent, light: false, offset: 17});
            tick.start();
        }
        Timer {
            id: tick; interval: 5; repeat: true
            onTriggered: {
                if (window.panel) {
                    var panel = window.panel;
                    var surface = panel.surface;
                    var position = window.vertical ? panel.y : panel.x;
                    var extent = window.vertical ? panel.height : panel.width;
                    var leading = position <= 0;
                    var trailing = position + extent >= 600;
                    function check(condition, message) {
                        if (!condition) { console.error(JSON.stringify(window.cases[window.current - 1]) + ": " + message); Qt.exit(1); }
                    }
                    check(surface.flushLeading === leading, "leading contact");
                    check(surface.flushTrailing === trailing, "trailing contact " + [panel.placementExtent, panel.availableExtent, panel.placementStart, panel.touchesTrailingEdge, surface.flushTrailing]);
                    check(surface.leadingBodyInset === (panel.detached || leading ? 0 : 14), "leading inset");
                    check(surface.trailingBodyInset === (panel.detached || trailing ? 0 : 14), "trailing inset");
                    var expectedExtent = panel.detached ? Math.min(panel.baseExtent, 576)
                        : panel.baseExtent + (leading ? 0 : 14) + (trailing ? 0 : 14);
                    check(extent === expectedExtent, "size " + extent + " vs " + expectedExtent);
                    var desired = panel.centeredPlacement || panel.alignment === "center" ? (600 - extent) / 2
                        : panel.alignment === "left" ? (window.vertical ? panel.offset : 0) : 600 - extent;
                    var inset = panel.detached ? 12 : 0;
                    check(position === Math.max(inset, Math.min(600 - extent - inset, desired)), "position " + [position, desired, panel.hostWindow, panel.strip, panel.attachmentTarget]);
                    var frame = surface.children[0].children.find(child => child.objectName === "panelContentFrame");
                    check((window.vertical ? frame.y : frame.x) === 24 + surface.leadingBodyInset, "content start");
                    check((window.vertical ? frame.height : frame.width) === extent - 48
                        - surface.leadingBodyInset - surface.trailingBodyInset, "content extent");
                    var crossPosition = window.vertical ? panel.x : panel.y;
                    var expectedCross = window.edge === "top" || window.edge === "left"
                        ? 30 + panel.attachmentGap : 570 - 200 - panel.attachmentGap;
                    check(crossPosition === expectedCross, "attachment position");
                    check(workspaceMenu.width > 0 && workspaceMenu.horizontalContentInset >= 48, "workspace menu size");
                    panel.destroy(); window.panel = null;
                }
                if (window.current === window.cases.length) {
                    console.log("PLACEMENT_OK " + window.cases.length); Qt.quit(); return;
                }
                var data = window.cases[window.current++];
                window.edge = data.edge; window.layout = data.layout;
                window.panel = popupComponent.createObject(window.contentItem, {
                    parent: window.contentItem, alignment: data.alignment, baseExtent: data.extent, offset: data.offset,
                    background: data.light ? "#eeeeee" : "#202020"
                });
            }
        }
    }
}
'''
