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


class DockClientRefreshTests(unittest.TestCase):
    def test_title_changes_refresh_only_title_consumers(self):
        source = (BAR / 'services/DockClients.qml').read_text()
        immediate = source[source.index('["openwindow"'):source.index('].indexOf')]
        self.assertNotIn('windowtitlev2', immediate)
        self.assertNotIn('activewindowv2', immediate)
        self.assertIn('event.data === model.activeAddress', source)
        self.assertIn('event.name === "windowtitlev2" && model.followTitles', source)
        self.assertIn('followTitles: true', (BAR / 'services/FocusMode.qml').read_text())
        self.assertNotIn('followTitles', (BAR / 'shell.qml').read_text())


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class EdgeDockTests(unittest.TestCase):
    def test_model_geometry_and_reveal(self):
        clients = [
            dict(address='0x1', **{'class': 'Browser'}, workspace={'id': 1}, focusHistoryID=4),
            dict(address='0x2', **{'class': 'Editor'}, workspace={'id': 2}, focusHistoryID=1),
            dict(address='0x3', **{'class': 'browser'}, workspace={'id': 2}, focusHistoryID=0),
            dict(address='0x4', **{'class': 'Hidden'}, mapped=False, workspace={'id': 1}),
        ]
        source = (BAR / 'dock/EdgeDock.qml').read_text()
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
        source = source.replace('import ".."\n', '').replace('"../', '"')
        source = source.replace('PanelWindow {', 'FloatingWindow {', 1)
        source = '\n'.join(line for line in source.splitlines() if not any(token in line for token in (
            '    anchors {', '    exclusionMode:', '    exclusiveZone:', '    WlrLayershell.')))
        source = source.replace('readonly property var monitor: Hyprland.monitorFor(screen)',
                                'property var monitor: ({activeWorkspace: {id: 2, hasFullscreen: false}})')
        source = source.replace('Quickshell.execDetached(command)', 'dock.actions.push(command.join(" "))')
        source = source.replace('    id: dock', '    id: dock\n    property var actions: []\n    implicitWidth: 800; implicitHeight: 600', 1)
        with tempfile.TemporaryDirectory(prefix='eitr-dock-') as directory:
            folder = Path(directory)
            for path in BAR.rglob("*"):
                if path.suffix in ('.qml', '.js') or path.name == 'qmldir':
                    destination = folder / path.relative_to(BAR)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(path, destination)
            for name, color in [('browser', '#d98a38'), ('editor', '#508db8'), ('files', '#72a470')]:
                (folder / f'{name}.svg').write_text(
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32">'
                    f'<rect x="2" y="2" width="28" height="28" rx="6" fill="{color}"/>'
                    '<path d="M9 10h14v3H9zm0 6h14v3H9zm0 6h9v3H9z" fill="white"/></svg>')
            for edge in ('top', 'bottom', 'left', 'right'):
                for light in (False, True):
                    capture_folder = Path(os.environ.get('EITR_DOCK_RENDERS', directory))
                    capture_folder.mkdir(parents=True, exist_ok=True)
                    capture = capture_folder / f'{edge}-{light}.png'
                    checks = '''
    function findAction(item, name) {
        if (item.objectName === name) return item;
        for (var child of item.children) { var found = findAction(child, name); if (found) return found; }
        return null;
    }
    property int phase: 0
    Timer {
        interval: 450; running: true; repeat: true
        onTriggered: {
            try {
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
                surface.desktopEntries = [{id: "Browser", name: "Browser", icon: "firefox", startupClass: "Browser"}, {id: "Editor", name: "Editor", icon: "text-editor", startupClass: "Editor"}, {id: "Other", name: "Files", icon: "system-file-manager", startupClass: "Other"}];
                dock.savePins(["Other", "Browser"]);
                if (dock.apps.length !== 3 || dock.apps[0].windows.length !== 0 || !surface.dividerVisible) throw new Error("Closed pin/divider");
                surface.activated(dock.apps[0]);
                if (dock.actions[dock.actions.length - 1].indexOf("app-launch --desktop Other.desktop") < 0) throw new Error("Pinned launch");
                dock.menuEntry = dock.apps[2];
                if (!reveal.held) throw new Error("Menu reveal hold");
                findAction(dock.contentItem, "dockPinAction").clicked();
                if (dock.pinnedEntries.join(",") !== "Other,Browser,Editor" || dock.menuOpen || surface.dividerVisible) throw new Error("Menu pin");
                dock.menuEntry = dock.apps[2];
                findAction(dock.contentItem, "dockPinAction").clicked();
                if (dock.pinnedEntries.join(",") !== "Other,Browser" || dock.menuOpen || !surface.dividerVisible) throw new Error("Menu unpin");
                surface.dragTo(dock.apps[2], 0);
                if (!reveal.held || surface.previewPins.join(",") !== "Editor,Other,Browser") throw new Error("Drag pin preview");
                surface.finishDrag();
                surface.dragTo(dock.apps[0], 500);
                surface.finishDrag();
                if (dock.pinnedEntries.join(",") !== "Other,Browser" || reveal.held) throw new Error("Drag unpin/hold release");
                var original = dock.pinnedEntries;
                dock.savePins([]);
                if (surface.dividerVisible) throw new Error("Divider without pins");
                dock.savePins(["Browser", "Editor"]);
                if (surface.dividerVisible) throw new Error("Divider without unpinned apps");
                dock.savePins(original);
            } else if (dock.phase === 2) {
                var closedSlot = findAction(surface, "dockSlot-other");
                var browserSlot = findAction(surface, "dockSlot-browser");
                var editorSlot = findAction(surface, "dockSlot-editor");
                if (!closedSlot || !browserSlot || !editorSlot) throw new Error("Missing icon slots");
                if ((dock.vertical ? browserSlot.y : browserSlot.x) !== 42 || (dock.vertical ? editorSlot.y : editorSlot.x) !== 96) throw new Error("Icon/divider placement");
                if (findAction(surface, "dockDots-other").count !== 0 || findAction(surface, "dockDots-browser").count !== 2) throw new Error("Window dots");
                if (findAction(surface, "dockIcon-other").opacity !== 1) throw new Error("Closed pin opacity");
                surface.grabToImage(function(result) {
                    if (!result.saveToFile(CAPTURE)) throw new Error("Dock capture");
                }, Qt.size(surface.width * 3, surface.height * 3));
                reveal.pointerInside = false;
            } else if (dock.phase === 4) {
                if (reveal.progress !== 0) throw new Error("Leave delay did not hide dock");
                DesktopStyle.reduceMotion = true;
                reveal.pointerInside = true;
            } else if (dock.phase === 5) {
                if (reveal.progress !== 1) throw new Error("Reduce motion reveal");
                dock.monitor = {activeWorkspace: {id: 2, hasFullscreen: true}};
                reveal.pointerInside = false;
            } else if (dock.phase === 6) {
                if (dock.available || dock.visible || reveal.progress !== 0) throw new Error("Fullscreen did not suppress dock");
                dock.monitor = {activeWorkspace: {id: 2, hasFullscreen: false}};
                dock.dockEnabled = false;
            } else if (dock.phase === 7) {
                if (dock.visible) throw new Error("Disabled dock visible");
                console.log("DOCK_OK"); Qt.quit();
            }
            dock.phase++;
            } catch (error) { console.error(error); Qt.exit(1); }
        }
    }
'''.replace('CAPTURE', json.dumps(str(capture))).replace('icon: "firefox"', 'icon: ' + json.dumps(str(folder / 'browser.svg'))).replace('icon: "text-editor"', 'icon: ' + json.dumps(str(folder / 'editor.svg'))).replace('icon: "system-file-manager"', 'icon: ' + json.dumps(str(folder / 'files.svg')))
                    fixture = source.replace('required property string barEdge', 'property string barEdge: '+json.dumps(edge)).replace('required property var clients', 'property var clients: '+json.dumps(clients)).replace('required property color foreground', 'property color foreground: '+json.dumps('#202430' if light else '#eee9df')).replace('required property color background', 'property color background: '+json.dumps('#eee9df' if light else '#202430'))
                    fixture = fixture.rstrip()[:-1] + checks + '\n}'
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    config_folder = folder / f'config-{edge}-{light}'
                    config_folder.mkdir()
                    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                       QML_IMPORT_PATH=str(ROOT / 'quickshell'), HOME=directory,
                                       XDG_CONFIG_HOME=str(config_folder), XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
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


class DockPinLogicTests(unittest.TestCase):
    def test_ordering_and_desktop_matching(self):
        script = (BAR / 'DockModel.js').read_text().replace('.pragma library', '')
        script += """
const assert = require('node:assert/strict');
assert.deepEqual(movePin(['a', 'b', 'c'], 'a', 2, true), ['b', 'c', 'a']);
assert.deepEqual(movePin(['a', 'b'], 'c', 1, true), ['a', 'c', 'b']);
assert.deepEqual(movePin(['a', 'b'], 'a', 9, false), ['b']);
assert.deepEqual(movePin([], 'a', 0, true), ['a']);
assert.deepEqual(dragPins(['a', 'b'], {desktopId: 'c', pinned: false}, 42), ['a', 'c', 'b']);
assert.deepEqual(dragPins(['a', 'b'], {desktopId: 'a', pinned: true}, 120), ['b']);
assert.deepEqual(dragPins(['a', 'b'], {desktopId: 'c', pinned: false}, 114), ['a', 'b']);
assert.deepEqual(dragPins(['a', 'b'], {desktopId: 'c', pinned: false}, 85), ['a', 'b', 'c']);
const ordered = [{id: 'a', desktopId: 'a'}, {id: 'b', desktopId: 'b'}, {id: 'c', desktopId: 'c'}];
assert.deepEqual(orderWithPins(ordered, ['c', 'a']).map(entry => entry.id), ['c', 'a', 'b']);
assert.deepEqual(orderWithPins(ordered, []).map(entry => entry.id), ['a', 'b', 'c']);
assert.deepEqual(movePin(['a.desktop'], 'A', 0, true), ['A']);
const lookup = value => ['org.browser', 'BrowserClass', 'org.browser.desktop'].includes(value) ? {id: 'org.browser'} : null;
const clients = [{address: '0x1', class: 'BrowserClass', workspace: {id: 1}}, {address: '0x2', class: 'Other'}];
const entries = groups(clients, 1, ['org.browser.desktop', 'Closed'], lookup);
assert.equal(entries.length, 3);
assert.equal(entries[0].windows.length, 1);
assert.equal(entries[0].desktopId, 'org.browser');
assert.equal(entries[1].windows.length, 0);
assert.equal(entries[2].appClass, 'Other');
assert.deepEqual(groups(clients, 1, [], lookup).map(entry => entry.appClass), ['BrowserClass', 'Other']);
assert.ok(eitrTerminal('eitr-menu-terminal') && eitrTerminal('fifs-terminal') && eitrTerminal('system-cleanup') && eitrTerminal('system-mirrors'));
assert.ok(!eitrTerminal('kitty') && !eitrTerminal('eitr'));
const terminals = groups([{address: '0x3', class: 'eitr-menu-terminal'}, {address: '0x4', class: 'cloud-terminal'}], 1, [], lookup);
assert.equal(terminals.length, 1);
assert.equal(terminals[0].windows.length, 2);
"""
        result = subprocess.run(['node', '-e', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_persistence_round_trip(self):
        with tempfile.TemporaryDirectory(prefix='eitr-dock-pins-') as directory:
            environment = dict(os.environ, HOME=directory, XDG_CONFIG_HOME=directory)
            helper = BAR / 'scripts/dock-pins.py'
            def run(*arguments):
                result = subprocess.run(['python3', str(helper), *arguments], env=environment,
                                        capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)['pins']
            self.assertEqual(run('status'), [])
            self.assertEqual(run('set', '["browser.desktop", "editor", "BROWSER"]'), ['browser.desktop', 'editor'])
            self.assertEqual(run('status'), ['browser.desktop', 'editor'])
            self.assertEqual(run('set', '["editor", "browser.desktop"]'), ['editor', 'browser.desktop'])
            self.assertEqual(run('status'), ['editor', 'browser.desktop'])
            self.assertEqual(run('set', '[]'), [])
            path = Path(directory) / 'quickshell/desktop-bar/dock-pins.json'
            self.assertEqual(json.loads(path.read_text())['version'], 1)
            self.assertEqual(list(path.parent.glob('.dock-pins.json-*')), [])
            result = subprocess.run(['python3', str(helper), 'set', '["/tmp/app"]'],
                                    env=environment, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(run('status'), [])
