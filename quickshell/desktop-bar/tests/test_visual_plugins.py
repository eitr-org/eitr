"""Render the actual plugin host with trusted example and failed components."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class VisualPluginLayoutTests(unittest.TestCase):
    def test_example_and_load_failure_in_both_themes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            broken = folder / 'Broken.qml'
            broken.write_text('import QtQuick\nItem { invalid syntax }\n')
            entries = []
            for kind, key, title, source in (
                    ('tiles', 'hello', 'Hello', ROOT / 'distro/plugins/example/HelloTile.qml'),
                    ('panels', 'hello-panel', 'Hello status', ROOT / 'distro/plugins/example/HelloPanel.qml'),
                    ('tiles', 'broken', 'Broken example', broken)):
                entries.append(dict(plugin='example', commit='a' * 40, kind=kind, id=key,
                                    title=title, icon='☀' if key == 'hello' else '', qml=source.name, source=source.as_uri(), disabled=False))
            for theme, state in [(theme, state) for theme in ('dark', 'light') for state in ('tiles', 'panel', 'broken', 'disabled')]:
                captures = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                captures.mkdir(parents=True, exist_ok=True)
                capture = captures / ('plugins-' + theme + '-' + state + '.png')
                background, foreground = ('#18212b', '#e9eef1') if theme == 'dark' else ('#f5f0e7', '#252936')
                selected = [dict(entry, panel='hello-panel') if entry['id'] == 'hello' else entry for entry in entries]
                if state == 'disabled':
                    selected = [dict(entry, disabled=True) for entry in selected if entry['id'] != 'broken']
                elif state != 'broken':
                    selected = [entry for entry in selected if entry['id'] != 'broken']
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 480; implicitHeight: 400
        Rectangle {
            id: sample; anchors.fill: parent; color: "BACKGROUND"
            Bar.PluginArea {
                id: area; x: 24; y: 24; width: 432
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#7ee0b5"
                queryEnabled: false; entries: ENTRIES
                Component.onCompleted: { OPEN_PANEL }
            }
            Timer {
                interval: 1200; running: true
                onTriggered: {
                    if (!area.visible || area.tiles.length === 0)
                        throw new Error("Plugin area did not populate");
                    if (area.height > sample.height - 48) throw new Error("Plugin area clipped");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        if (area.selectedPanel) {
                            if (!area.back() || area.selectedPanel !== null || area.back())
                                throw new Error("Back did not return to tiles before closing");
                        }
                        const cachedEntries = area.entries;
                        const tilesHeight = area.height;
                        area.active = false;
                        area.active = true;
                        if (area.entries !== cachedEntries || area.height !== tilesHeight)
                            throw new Error("Opening rebuilt cached placements or changed row geometry");
                        console.log("PLUGIN_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                    .replace('OPEN_PANEL', 'openPanel("example", "hello-panel")' if state == 'panel' else '').replace('ENTRIES', json.dumps(selected)).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('PLUGIN_RENDER_OK', result.stdout + result.stderr)
                if state == 'broken':
                    self.assertIn('Could not load', result.stdout + result.stderr)
                self.assertNotIn('HelloTile.qml: Cannot', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())

    def test_round_two_review_surfaces(self):
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-placement-') as directory:
            folder = Path(directory)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            spec = json.loads((ROOT / 'distro/plugins/example/eitr-plugin.json').read_text())
            entries = [dict(entry, plugin='example', pluginName='Example plugin', kind=kind, commit='a' * 40, disabled=False,
                            source=(ROOT / 'distro/plugins/example' / entry['qml']).as_uri())
                       for kind, declarations in spec['ui'].items() for entry in declarations]
            (folder / 'eitr').mkdir()
            (folder / 'eitr/plugin-placements.json').write_text(json.dumps({
                'version': 1,
                'widgets': [dict(plugin='example', id='clock', monitor='missing-monitor',
                                 x=24, y=24, width=240, height=144)],
                'barItems': [dict(plugin='example', id='status-dot')],
            }))
            clock = next(entry for entry in entries if entry['kind'] == 'widgets')
            dot = next(entry for entry in entries if entry['kind'] == 'barItems')
            shell_source = (BAR / 'shell.qml').read_text()
            tabs = shell_source.split('                    Item {\n                        id: tabStrip\n                        visible: shell.notchLayout', 1)[1].split('                    HoverHandler {\n                        id: barHover', 1)[0]
            tabs = 'Item {\n visible: shell.notchLayout' + tabs
            for mode in ('widget-dark', 'widget-light', 'widget-edit', 'bar-full', 'bar-tabs', 'management', 'management-disabled'):
                capture_folder = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                capture_folder.mkdir(parents=True, exist_ok=True)
                capture = capture_folder / (mode + '.png')
                light = mode == 'widget-light'
                foreground, background = ('#252936', '#f5f0e7') if light else ('#e9eef1', '#18212b')
                fixture = '''import QtQuick
import QtQuick.Shapes
import Quickshell
import "." as Bar
ShellRoot {
    id: shell
    property bool notchLayout: TABS
    property bool verticalBar: false
    property string barEdge: "top"
    property real tabStripThickness: 7
    property real tabBendRound: 6
    function barBackground() { return "BACKGROUND"; }
    Component.onCompleted: {
        Bar.PluginRegistry.entries = ENTRIES;
        Bar.PluginRegistry.placements = {version: 1, widgets: [{plugin: "example", id: "clock", monitor: "missing-monitor", x: 24, y: 24, width: 240, height: 144}], barItems: [{plugin: "example", id: "status-dot"}]};
        if (Bar.PluginRegistry.placed("widgets", "connected-monitor").length !== 0 || Bar.PluginRegistry.placements.widgets.length !== 1)
            throw new Error("Missing monitor lost or displayed its placement");
        if (Bar.PluginRegistry.barItems.length !== 1)
            throw new Error("Explicit bar placement did not resolve");
    }
    FloatingWindow {
        id: bar
        visible: true; implicitWidth: 1280; implicitHeight: 800
        property real normalThickness: 30
        property real tabLeadingEnd: 220
        property real tabCenterStart: 552
        property real tabCenterEnd: 728
        property real tabTrailingStart: 1000
        Rectangle {
            id: sample; anchors.fill: parent; color: "WALLPAPER"
            Rectangle {
                x: -240; y: 400; width: 1100; height: 400; rotation: -22
                color: LIGHT ? "#b8c7bc" : "#20372f"; opacity: 0.7
            }
            Rectangle {
                x: 700; y: 240; width: 800; height: 200; rotation: 30
                color: LIGHT ? "#d4c6ae" : "#302b42"; opacity: 0.5
            }
            Bar.PluginWidget {
                visible: WIDGET
                x: 220; y: 220; width: 300; height: 180
                entry: CLOCK; editing: EDITING
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#70ba9a"
            }
            Item {
                id: barContents; width: parent.width; height: 30; visible: BAR
                Bar.BarSection { anchors.fill: parent; edge: "top"; background: shell.notchLayout ? "transparent" : "BACKGROUND" }
                TAB_SURFACES
                Text {
                    id: centre; anchors.centerIn: parent; anchors.alignWhenCentered: false
                    text: "Tue 27 Oct  12:34"; color: "FOREGROUND"; font.pixelSize: 13
                }
                Text { x: 12; anchors.verticalCenter: parent.verticalCenter; text: "ᛖ    ▦    1    2    3    4    5"; color: "FOREGROUND"; font.pixelSize: 13 }
                Row {
                    anchors.right: parent.right; anchors.rightMargin: 12; anchors.verticalCenter: parent.verticalCenter; spacing: 4
                    Bar.PluginBarItems {
                        id: items; entries: [DOT]
                        foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#70ba9a"
                    }
                    Text { text: "WiFi   BT   Audio   Updates   Bell"; color: "FOREGROUND"; font.pixelSize: 13 }
                }
            }
            Rectangle {
                visible: BAR; x: parent.width / 2; y: 30; width: 1; height: 50; color: "#70ba9a"
                Text { x: 8; y: 24; text: "screen centre"; color: "FOREGROUND"; font.pixelSize: 12 }
            }
            Rectangle {
                visible: MANAGEMENT
                x: 380; y: 50; width: 520; height: 700
                color: "BACKGROUND"; radius: 12
                Column {
                    x: 24; y: 20; width: parent.width - 48; spacing: 16
                    Text { text: "Control Center · General"; color: "FOREGROUND"; font.pixelSize: 16 }
                    Bar.PluginArea {
                        id: area; width: parent.width; queryEnabled: false; entries: ENTRIES
                        monitors: [{name: "missing-monitor", description: "Example display"}, {name: "DP-2", description: "Second display"}, {name: "DP-3", description: "Third display"}]
                        Component.onCompleted: managing = true
                        foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#70ba9a"
                    }
                }
            }
            Timer {
                interval: 1000; running: true
                onTriggered: {
                    if (Math.abs(centre.x + centre.width / 2 - sample.width / 2) > 0.01)
                        throw new Error("Clock moved off screen centre");
                    if (items.width !== 24) throw new Error("Plugin slot changed width");
                    if (MANAGEMENT) {
                        if (!area.managing || area.height > 640) throw new Error("Management missing or clipped");
                        if (Bar.PluginRegistry.placements.widgets.length !== 1 || Bar.PluginRegistry.placements.barItems.length !== 1) throw new Error("Management lost placements before capture");
                    }
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        if (MANAGEMENT && (!area.back() || area.managing || area.back())) throw new Error("Manage back failed");
                        console.log("ROUND_TWO_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''
                replacements = dict(TAB_SURFACES=tabs, BACKGROUND=background, FOREGROUND=foreground,
                                    WALLPAPER='#e2dfd5' if light else '#0e151e', LIGHT=str(light).lower(),
                                    CLOCK=json.dumps(clock), DOT=json.dumps(dot),
                                    ENTRIES=json.dumps([dict(entry, disabled=True) for entry in entries] if mode == 'management-disabled' else entries),
                                    WIDGET=str(mode.startswith('widget')).lower(), EDITING=str(mode == 'widget-edit').lower(),
                                    MANAGEMENT=str(mode.startswith('management')).lower(), BAR=str(mode.startswith('bar')).lower(),
                                    TABS=str(mode == 'bar-tabs').lower(), CAPTURE=str(capture))
                for key, value in replacements.items():
                    fixture = fixture.replace(key, value)
                path = folder / 'round-two.qml'
                path.write_text(fixture)
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(path)], env=environment, text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('ROUND_TWO_RENDER_OK', result.stdout + result.stderr)
                self.assertNotIn('ReferenceError', result.stdout + result.stderr)
                self.assertNotIn('TypeError', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())
