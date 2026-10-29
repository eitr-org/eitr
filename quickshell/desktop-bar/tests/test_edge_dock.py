"""Exercise the production dock, using mock clients instead of a compositor."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

BAR = Path(__file__).resolve().parents[1]
ROOT = BAR.parents[1]


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class EdgeDockTests(unittest.TestCase):
    def test_model_geometry_and_reveal(self):
        clients = [
            dict(address='0x1', **{'class': 'Browser'}, workspace={'id': 1}, focusHistoryID=4),
            dict(address='0x2', **{'class': 'Editor'}, workspace={'id': 2}, focusHistoryID=1),
            dict(address='0x3', **{'class': 'browser'}, workspace={'id': 2}, focusHistoryID=0),
            dict(address='0x4', **{'class': 'Hidden'}, mapped=False, workspace={'id': 1}),
        ]
        source = (BAR / 'EdgeDock.qml').read_text()
        self.assertIn('exclusiveZone: 0', source)
        self.assertIn('exclusionMode: ExclusionMode.Ignore', source)
        self.assertIn('WlrLayershell.layer: WlrLayer.Overlay', source)
        self.assertIn('DockModel.windowCommand("focus"', source)
        self.assertIn('DockModel.windowCommand("close"', source)
        self.assertNotIn('focuswindow', source)
        # The mask uses the resting rectangle: a Region ignores the slide-in transform.
        self.assertIn('Region { item: dock.available && reveal.progress > 0 ? surfaceArea : null', source)
        self.assertNotIn('? surface : null', source)
        self.assertIn('dockEnabled && !fullscreen', source)
        # Only the platform window and compositor lookup are replaced; render and
        # exercise the production content, geometry, mask and auto-hide controller.
        source = source.replace('PanelWindow {', 'FloatingWindow {', 1)
        source = '\n'.join(line for line in source.splitlines() if not any(token in line for token in (
            '    anchors {', '    exclusionMode:', '    exclusiveZone:', '    WlrLayershell.')))
        source = source.replace('readonly property var monitor: Hyprland.monitorFor(screen)',
                                'property var monitor: ({activeWorkspace: {id: 2, hasFullscreen: false}})')
        source = source.replace('Quickshell.execDetached(command)', 'dock.actions.push(command.join(" "))')
        source = source.replace('    id: dock', '    id: dock\n    property var actions: []\n    implicitWidth: 800; implicitHeight: 600', 1)
        with tempfile.TemporaryDirectory(prefix='eitr-dock-') as directory:
            folder = Path(directory)
            for path in BAR.iterdir():
                if path.suffix in ('.qml', '.js') or path.name == 'qmldir':
                    shutil.copy(path, folder / path.name)
            for edge in ('top', 'bottom', 'left', 'right'):
                for light in (False, True):
                    capture_folder = Path(os.environ.get('EITR_DOCK_RENDERS', directory))
                    capture_folder.mkdir(parents=True, exist_ok=True)
                    capture = capture_folder / f'{edge}-{light}.png'
                    checks = '''
    property int phase: 0
    Timer {
        interval: 450; running: true; repeat: true
        onTriggered: {
            if (dock.phase === 0) {
                if (reveal.progress !== 0) throw new Error("Dock starts revealed");
                if (dock.apps.length !== 2 || dock.apps[0].appClass !== "Browser" || dock.apps[1].appClass !== "Editor") throw new Error("Grouping/order");
                if (dock.apps[0].windows.length !== 2 || dock.apps[0].recent.address !== "0x3") throw new Error("Recent window");
                if (!dock.apps[0].onCurrentWorkspace || !dock.apps[1].onCurrentWorkspace) throw new Error("Workspace dots");
                var other = DockModel.groups(dock.clients, 1, []);
                if (!other[0].onCurrentWorkspace || other[1].onCurrentWorkspace) throw new Error("Workspace dot did not follow workspace");
                var pinned = DockModel.groups(dock.clients, 2, [{appClass: "Other"}, {appClass: "browser"}]);
                if (pinned.length !== 3 || pinned[0].windows.length || !pinned[1].pinned || pinned[1].windows.length !== 2) throw new Error("Pinned entry extension");
                var expected = {top: "bottom", bottom: "top", left: "right", right: "left"}[dock.barEdge];
                if (dock.edge !== expected || surface.width !== (dock.vertical ? 52 : 94) || surface.height !== (dock.vertical ? 94 : 52) || surface.detached) throw new Error("Dock geometry");
                var center = dock.vertical ? surface.y + surface.height / 2 : surface.x + surface.width / 2;
                if (center !== (dock.vertical ? dock.height : dock.width) / 2) throw new Error("Dock not centered");
                if ((dock.vertical ? sensor.width : sensor.height) !== 1) throw new Error("Trigger thickness");
                // Browser's recent window 0x3 already has focus, so a click moves on to 0x1.
                surface.activated(dock.apps[0]); surface.activated(dock.apps[1]); surface.closeRequested(dock.apps[0]);
                if (dock.actions.join("|") !== 'hyprctl dispatch hl.dsp.focus({ window = "address:0x1" })|hyprctl dispatch hl.dsp.focus({ window = "address:0x2" })|hyprctl dispatch hl.dsp.window.close({ window = "address:0x3" })') throw new Error("App actions: " + dock.actions.join("|"));
                reveal.pointerInside = true;
            } else if (dock.phase === 1) {
                if (reveal.progress !== 1) throw new Error("Dock did not reveal");
                surface.grabToImage(function(result) {
                    if (!result.saveToFile(CAPTURE)) throw new Error("Dock capture");
                });
                reveal.pointerInside = false;
            } else if (dock.phase === 3) {
                if (reveal.progress !== 0) throw new Error("Leave delay did not hide dock");
                DesktopStyle.reduceMotion = true;
                reveal.pointerInside = true;
            } else if (dock.phase === 4) {
                if (reveal.progress !== 1) throw new Error("Reduce motion reveal");
                dock.monitor = {activeWorkspace: {id: 2, hasFullscreen: true}};
                reveal.pointerInside = false;
            } else if (dock.phase === 5) {
                if (dock.available || dock.visible || reveal.progress !== 0) throw new Error("Fullscreen did not suppress dock");
                dock.monitor = {activeWorkspace: {id: 2, hasFullscreen: false}};
                dock.dockEnabled = false;
            } else if (dock.phase === 6) {
                if (dock.visible) throw new Error("Disabled dock visible");
                console.log("DOCK_OK"); Qt.quit();
            }
            dock.phase++;
        }
    }
'''.replace('CAPTURE', json.dumps(str(capture)))
                    fixture = source.replace('required property string barEdge', 'property string barEdge: '+json.dumps(edge)).replace('required property var clients', 'property var clients: '+json.dumps(clients)).replace('required property color foreground', 'property color foreground: '+json.dumps('#202430' if light else '#eee9df')).replace('required property color background', 'property color background: '+json.dumps('#eee9df' if light else '#202430'))
                    fixture = fixture.rstrip()[:-1] + checks + '\n}'
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                       QML_IMPORT_PATH=str(ROOT / 'quickshell'), HOME=directory,
                                       XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
                                       XDG_RUNTIME_DIR=directory, HYPRLAND_INSTANCE_SIGNATURE='',
                                       DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
                    result = subprocess.run(['quickshell', '-p', str(path)], env=environment,
                                            capture_output=True, text=True, timeout=15)
                    output = result.stdout + result.stderr
                    with self.subTest(edge=edge, light=light):
                        self.assertEqual(result.returncode, 0, output)
                        self.assertIn('DOCK_OK', output)
                        self.assertNotIn('ReferenceError', output)
                        self.assertNotIn('TypeError', output)
                        self.assertTrue(capture.is_file(), output)
