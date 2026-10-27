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
    def test_author_canvases_and_theme_api(self):
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-style-') as directory:
            folder = Path(directory)
            canvas = folder / 'Canvas.qml'
            canvas.write_text('''import QtQuick
Rectangle {
    required property var api
    implicitHeight: 120
    color: "#ed286b"
    Component.onCompleted: {
        if (api.palette.color15 !== "#fff123" || api.palette.foreground !== "#abcdef")
            throw new Error("Missing full palette");
        api.themeChanged.connect(function() { console.log("THEME_SIGNAL_OK"); });
    }
    Text { anchors.centerIn: parent; text: "MY CANVAS"; color: "#132750"; font.pixelSize: 22 }
}''')
            spec = json.loads((ROOT / 'distro/plugins/example/eitr-plugin.json').read_text())
            entries = [dict(entry, plugin='example', kind=kind, commit='a' * 40, disabled=False,
                            source=(ROOT / 'distro/plugins/example' / entry['qml']).as_uri())
                       for kind, declarations in spec['ui'].items() for entry in declarations]
            widget = dict(plugin='example', kind='widgets', id='canvas', title='Canvas', source=canvas.as_uri(), qml='Canvas.qml', disabled=False, commit='a' * 40)
            panel = dict(widget, kind='panels', id='canvas-panel', header=False)
            entries.append(panel)
            for mode in ('custom-tiles', 'widget-none', 'panel-no-header'):
                captures = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                captures.mkdir(parents=True, exist_ok=True)
                capture = captures / (mode + '.png')
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    Component.onCompleted: {
        Bar.PluginRegistry.palette = {color15: "#fff123", foreground: "#abcdef"};
        if (Bar.PluginRegistry.widgetSurface({}) !== "none"
            || Bar.PluginRegistry.widgetSurface({surface: "panel"}) !== "panel"
            || Bar.PluginRegistry.widgetSurface({surface: "panel", geometry: {surface: "none"}}) !== "none"
            || Bar.PluginRegistry.widgetSurface({surface: "none", geometry: {surface: "panel"}}) !== "panel")
            throw new Error("Surface precedence failed");
    }
    Bar.PluginComponent {
        id: defaultTile; active: false; visible: false
        entry: ({kind: "tiles", title: "Default"})
        foreground: "white"; background: "black"; accent: "cyan"
    }
    FloatingWindow {
        visible: true; implicitWidth: 480; implicitHeight: 240
        Rectangle {
            id: sample; anchors.fill: parent; color: "#162c36"
            Bar.PluginArea {
                id: area; x: 24; y: 24; width: 432; visible: !WIDGET
                foreground: "#e9eef1"; background: "#18212b"; accent: "#7ee0b5"
                queryEnabled: false; entries: ENTRIES
                Component.onCompleted: if (PANEL) openPanel("example", "canvas-panel")
            }
            Bar.PluginWidget {
                id: widget; visible: WIDGET; x: 24; y: 24; width: 432; height: 180
                entry: WIDGET_ENTRY
                foreground: "#e9eef1"; background: "#18212b"; accent: "#7ee0b5"
            }
            Timer {
                interval: 1200; running: true
                onTriggered: {
                    if (defaultTile.customTile || !defaultTile.surface || defaultTile.implicitHeight !== 36) throw new Error("Tile default changed");
                    if (WIDGET && widget.surface !== "none") throw new Error("Widget default changed");
                    if (!PANEL && !WIDGET && (area.tiles.length !== 2 || area.height !== 116)) throw new Error("Tile slot geometry changed");
                    if (PANEL && area.height !== 120) throw new Error("Hidden header reserves space");
                    Bar.PluginRegistry.palette = {color15: "#123fff", foreground: "#abcdef"};
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        if (PANEL && !area.back()) throw new Error("Headerless Back failed");
                        console.log("AUTHOR_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BAR', BAR.as_uri()).replace('WIDGET_ENTRY', json.dumps(widget))
                    .replace('WIDGET', str(mode == 'widget-none').lower())
                    .replace('PANEL', str(mode == 'panel-no-header').lower())
                    .replace('ENTRIES', json.dumps(entries)).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                output = result.stdout + result.stderr
                self.assertEqual(result.returncode, 0, output)
                self.assertIn('AUTHOR_RENDER_OK', output)
                self.assertNotIn('Error:', output)
                self.assertNotIn('Plugin QML', output)
                if mode != 'custom-tiles':
                    self.assertIn('THEME_SIGNAL_OK', output)
                self.assertTrue(capture.is_file())

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
                    Text { text: "Control Center · Plugins"; color: "FOREGROUND"; font.pixelSize: 16 }
                    Bar.PluginManagement {
                        id: area; width: parent.width; entries: ENTRIES
                        monitors: [{name: "missing-monitor", description: "Example display"}, {name: "DP-2", description: "Second display"}, {name: "DP-3", description: "Third display"}]
                        foreground: "FOREGROUND"; background: "BACKGROUND"
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
                        if (!area.rows.length || area.height > 640) throw new Error("Management missing or clipped");
                        if (Bar.PluginRegistry.placements.widgets.length !== 1 || Bar.PluginRegistry.placements.barItems.length !== 1) throw new Error("Management lost placements before capture");
                    }
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
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

    def test_spectrum_and_layer_toggle_offscreen(self):
        import sys
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-live-') as directory:
            folder = Path(directory)
            fake = folder / 'cava'
            fake.write_text(f'#!{sys.executable}\nimport time\nwhile True:\n print(";".join(str((index * 17) % 100) for index in range(128)) + ";", flush=True)\n time.sleep(.03)\n')
            fake.chmod(0o700)
            widget = folder / 'SpectrumWidget.qml'
            widget.write_text('''import QtQuick
Item {
    id: widget
    required property var api
    Component.onCompleted: { api.spectrumBars = 32; api.spectrumFrameRate = 30; }
    Row {
        anchors.centerIn: parent; spacing: 3; height: parent.height - 32
        Repeater {
            model: widget.api.spectrum
            Rectangle {
                required property real modelData
                width: 6; height: Math.max(2, modelData * parent.height)
                anchors.bottom: parent.bottom; radius: 2; color: widget.api.accent
            }
        }
    }
}''')
            entry = dict(plugin='fixture', pluginName='Spectrum example', kind='widgets', id='spectrum',
                         title='Audio spectrum', qml=widget.name, source=widget.as_uri(),
                         commit='a' * 40, disabled=False, capabilities=['audio-spectrum'])
            placement = dict(plugin='fixture', id='spectrum', monitor='test-display',
                             x=24, y=24, width=320, height=180, aboveWindows=True)
            (folder / 'eitr').mkdir()
            (folder / 'eitr/plugin-placements.json').write_text(json.dumps(dict(version=2, widgets=[placement], barItems=[])))
            for mode in ('spectrum-dark', 'spectrum-light', 'layer-toggle-dark', 'layer-toggle-light'):
                captures = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                captures.mkdir(parents=True, exist_ok=True)
                capture = captures / (mode + '.png')
                light = mode.endswith('light')
                foreground, background = ('#252936', '#f5f0e7') if light else ('#e9eef1', '#18212b')
                fixture = folder / 'shell.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 540; implicitHeight: 260
        Rectangle {
            id: sample; anchors.fill: parent; color: "BACKGROUND"
            Text { x: 24; y: 20; text: MANAGE ? "Plugins · Manage" : "Audio spectrum · simulated playback"; color: "FOREGROUND"; font.pixelSize: 16 }
            Bar.PluginWidget {
                id: widget; visible: !MANAGE
                x: 110; y: 60; width: 320; height: 170
                entry: ENTRY; foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#70ba9a"
            }
            Bar.PluginManagement {
                id: manage; visible: MANAGE; x: 24; y: 64; width: parent.width - 48
                entries: [ENTRY]; monitors: [{name: "test-display", description: "Example monitor"}]
                foreground: "FOREGROUND"; background: "BACKGROUND"
            }
            Timer {
                interval: 1200; running: true
                onTriggered: {
                    if (!MANAGE && !Bar.SpectrumProvider.hasFrame) throw new Error("No fake spectrum");
                    if (MANAGE && (!manage.rows[0].aboveWindows || manage.height !== 36)) throw new Error("Layer toggle row missing or resized");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        console.log("LIVE_PLUGIN_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BAR', BAR.as_uri()).replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                    .replace('MANAGE', str(mode.startswith('layer')).lower()).replace('ENTRY', json.dumps(entry)).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='',
                                   PATH=directory + os.pathsep + os.environ['PATH'])
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('LIVE_PLUGIN_RENDER_OK', result.stdout + result.stderr)
                self.assertNotIn('ReferenceError', result.stdout + result.stderr)
                self.assertNotIn('TypeError', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())

    def test_stream_visibility_and_repeated_line_signal(self):
        import sys
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-stream-') as directory:
            folder = Path(directory)
            helper = folder / 'walker/scripts/actions/install/plugins.py'
            helper.parent.mkdir(parents=True)
            helper.write_text('''import sys
from pathlib import Path
from eitr_plugin_stream import run_stream
if sys.argv[1] == 'ui-stream':
    run_stream([sys.executable, str(Path(__file__).parents[4] / 'source.py')], Path.cwd())
''')
            (folder / 'source.py').write_text('''import os, signal, time
from pathlib import Path
log = Path(os.environ['STREAM_TEST_LOG'])
with log.open('a') as output:
    output.write('start\\n')
while True:
    print('same', flush=True)
    time.sleep(.03)
''')
            widget = folder / 'Widget.qml'
            widget.write_text('''import QtQuick
Item {
    id: streamView
    required property var api
    property int received: 0
    Connections { target: streamView.api; function onStreamReceived(line) { streamView.received++; streamView.api.detail = String(streamView.received); } }
}''')
            entry = dict(plugin='fixture', kind='panels', id='stream', title='Stream', qml='Widget.qml',
                         source=widget.as_uri(), commit='a' * 40, dataStream={'run': 'source.py'}, disabled=False)
            fixture = folder / 'shell.qml'
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR"
ShellRoot {
    FloatingWindow {
        visible: true
        PluginComponent { id: host; anchors.fill: parent; entry: ENTRY; foreground: "white"; background: "black"; accent: "green" }
    }
    Timer {
        interval: 400; running: true; repeat: true
        property int stage: 0
        onTriggered: {
            if (stage === 0) {
                if (Number(host.detail) < 2) throw new Error("Repeated stream lines did not emit signals");
                host.visible = false;
            } else if (stage === 1) host.visible = true;
            else if (stage === 2) {
                if (Number(host.detail) < 2) throw new Error("Stream did not restart on show");
                host.active = false;
            } else { console.log("STREAM_VISIBILITY_OK"); Qt.quit(); }
            stage++;
        }
    }
}'''.replace('BAR', BAR.as_uri()).replace('ENTRY', json.dumps(entry)))
            log = folder / 'events'
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=directory,
                               PYTHONPATH=str(ROOT / 'distro/lib'), STREAM_TEST_LOG=str(log),
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                               XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                    text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('STREAM_VISIBILITY_OK', result.stdout + result.stderr)
            self.assertNotIn('TypeError', result.stdout + result.stderr)
            self.assertEqual(log.read_text().splitlines(), ['start', 'start'])


    def test_round_four_manager_widgets_and_menu(self):
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-round4-') as directory:
            folder = Path(directory)
            plugin = folder / 'Visualizer.qml'
            plugin.write_text("""import QtQuick
Item {
    id: view
    required property var api
    Component.onCompleted: api.setMenu([{id: "wave", text: "Wave", checked: true}, {id: "terminal", text: "Terminal", checked: false}])
    Connections {
        target: view.api
        function onMenuTriggered(id) {
            view.api.setMenu([{id: "wave", text: "Wave", checked: id === "wave"}, {id: "terminal", text: "Terminal", checked: id === "terminal"}]);
        }
    }
    Row {
        anchors.centerIn: parent; spacing: 5; height: parent.height - 64
        Repeater {
            model: 36
            Rectangle {
                required property int index
                width: 7; height: 8 + (Math.sin(index * .48) + 1) * 38
                anchors.bottom: parent.bottom; radius: 2; color: view.api.accent
            }
        }
    }
}""")
            entry = dict(plugin='visualizer', kind='widgets', id='spectrum', title='Audio visualizer',
                         qml=plugin.name, source=plugin.as_uri(), commit='a' * 40, disabled=False, surface='none')
            preview = folder / 'preview.png'
            installed = [dict(id='visualizer', name='Audio visualizer', author='Example author', version='2.1.0',
                              description='Playback spectrum with Wave and Terminal modes', enabled=True,
                              blocked='', visualsDisabled=False, icon=(ROOT / 'distro/plugins/example/icon.svg').as_uri(), preview=preview.as_uri()),
                         dict(id='clock', name='Desktop clock', author='Example contributor', version='1.0.0',
                              description='A clock for each display', enabled=False, blocked='disabled',
                              visualsDisabled=False, icon='', preview='')]
            for mode in ('manager-dark', 'manager-light', 'manager-list', 'transparent-widget', 'edit-widget', 'widget-menu'):
                captures = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                captures.mkdir(parents=True, exist_ok=True)
                capture = captures / (mode + '.png')
                light = mode.endswith('light')
                foreground, background = ('#252936', '#f5f0e7') if light else ('#e9eef1', '#18212b')
                fixture = folder / 'shell.qml'
                fixture.write_text("""import QtQuick
import Quickshell
import "BAR" as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 660; implicitHeight: 820
        Rectangle {
            id: sample; anchors.fill: parent; color: "BACKGROUND"
            Repeater {
                model: MANAGER ? 0 : 28
                Rectangle {
                    required property int index
                    x: index * 33 - 180; y: -100; width: 22; height: 1400
                    rotation: 32; color: index % 2 ? "#315362" : "#473956"
                }
            }
            Rectangle {
                visible: MANAGER; x: 12; y: 12; width: 42; height: parent.height - 24
                color: Qt.alpha("FOREGROUND", .05); radius: 6
                Column {
                    anchors.horizontalCenter: parent.horizontalCenter; y: 16; spacing: 14
                    Repeater {
                        model: ["󰕮", "󰏖", "󰏘", "󱁤", "󰒓"]
                        Bar.PanelButton {
                            required property string modelData
                            width: 32; height: 32; text: modelData; icon: true
                            foreground: "FOREGROUND"; selected: modelData === "󰏖"
                        }
                    }
                }
            }
            Text { x: MANAGER ? 74 : 24; y: 24; text: MANAGER ? "Plugins" : "Audio visualizer"; color: "FOREGROUND"; font.pixelSize: 16 }
            Bar.PluginManager {
                id: manager; x: 74; y: 62; width: 560; visible: MANAGER
                installed: []; entries: [ENTRY]; selectedPlugin: LIST ? "" : "visualizer"; expanded: "visualizer"
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#7ee0b5"
            }
            Bar.PluginWidget {
                id: widget; x: 96; y: 100; width: 460; height: 200; visible: !MANAGER
                entry: ENTRY; surface: "none"; editing: EDIT
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#7ee0b5"
            }
            Rectangle {
                visible: MENU; x: 294; y: 308; width: 300; height: options.implicitHeight + 20
                color: "BACKGROUND"; radius: 6
                border.width: 1; border.color: Qt.alpha("FOREGROUND", .15)
                Bar.PluginWidgetMenu {
                    id: options; x: 10; y: 10; width: parent.width - 20
                    foreground: "FOREGROUND"; background: "BACKGROUND"
                    surface: "none"; entries: widget.menuEntries
                    onSelected: id => widget.selectMenu(id)
                }
            }
            Timer {
                interval: 700; running: true; repeat: true
                property bool ready: false
                property bool listChecked: false
                onTriggered: {
                    if (MANAGER && !ready) {
                        widget.visible = true;
                        widget.grabToImage(function(result) {
                            result.saveToFile("PREVIEW");
                            widget.visible = false;
                            manager.installed = LIST ? Array.from({length: 20}, function(unusedValue, index) { return Object.assign({}, INSTALLED[0], {id: "plugin-" + index}); }) : INSTALLED;
                            manager.selectedPlugin = LIST ? "" : "visualizer";
                            ready = true;
                        });
                        return;
                    }
                    if (LIST && !listChecked) {
                        if (manager.height > 20 * 42 + 150) throw new Error("Plugin list is not compact");
                        manager.selectedPlugin = "plugin-0";
                        if (!manager.selected || manager.selected.id !== "plugin-0" || !manager.back() || manager.back()) throw new Error("Detail navigation failed");
                        manager.installed = INSTALLED;
                        listChecked = true;
                        return;
                    }
                    if (manager.height > sample.height - 90) throw new Error("Manager clipped");
                    if (!MANAGER) {
                        if (widget.menuEntries.length !== 2) throw new Error("Menu API missing");
                        widget.selectMenu("terminal");
                        if (!widget.menuEntries[1].checked || widget.menuEntries[0].checked) throw new Error("Menu API signal failed");
                    }
                    manager.visible = !MANAGER; manager.visible = MANAGER;
                    sample.grabToImage(function(result) {
                        if (!result.saveToFile("CAPTURE")) throw new Error("Capture failed");
                        console.log("ROUND_FOUR_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}""".replace('BAR', BAR.as_uri()).replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                    .replace('MANAGER', str(mode.startswith('manager')).lower()).replace('LIST', str(mode == 'manager-list').lower()).replace('EDIT', str(mode == 'edit-widget').lower())
                    .replace('MENU', str(mode == 'widget-menu').lower()).replace('INSTALLED', json.dumps(installed))
                    .replace('ENTRY', json.dumps(entry)).replace('CAPTURE', str(capture)).replace('PREVIEW', str(preview)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment, text=True, capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('ROUND_FOUR_RENDER_OK', result.stdout + result.stderr)
                self.assertNotIn('ReferenceError', result.stdout + result.stderr)
                self.assertNotIn('TypeError', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())


    def test_pointer_handles_reach_geometry_save(self):
        with tempfile.TemporaryDirectory(prefix='eitr-widget-input-') as directory:
            folder = Path(directory)
            helper = folder / 'walker/scripts/actions/install/plugins.py'
            helper.parent.mkdir(parents=True)
            helper.write_text("""import json, sys
from pathlib import Path
if sys.argv[1] == 'place':
    target = Path(__file__).parents[4] / 'saved.json'
    values = json.loads(target.read_text()) if target.exists() else []
    values.append(json.loads(sys.argv[sys.argv.index('--geometry') + 1]))
    target.write_text(json.dumps(values))
elif sys.argv[1] == 'placements':
    print('{"version":2,"widgets":[],"barItems":[]}')
else:
    print('[]')
""")
            fixture = folder / 'shell.qml'
            fixture.write_text("""import QtQuick
import QtTest
import Quickshell
import "BAR" as Bar
import "GEOMETRY" as Geometry
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 900; implicitHeight: 600
        Rectangle {
            anchors.fill: parent; color: "#18212b"
            property var gestureStart: null
            property var draft: ({x: 24, y: 30, width: 360, height: 180})
            readonly property var bounds: ({x: 0, y: 30, width: 900, height: 570})
            id: canvas
            TestEvent { id: pointer }
            Bar.PluginWidget {
                id: widget
                entry: ({plugin: "fixture", id: "widget", kind: "widgets", title: "Input fixture", disabled: true, source: "", qml: ""})
                x: canvas.draft.x; y: canvas.draft.y; width: canvas.draft.width; height: canvas.draft.height
                originX: x; originY: y; editing: true
                foreground: "white"; background: "#18212b"; accent: "#7ee0b5"
                onBegun: canvas.gestureStart = Object.assign({}, canvas.draft)
                onMoved: function(dx, dy) { canvas.draft = Geometry.fit(Geometry.delta(canvas.gestureStart, dx, dy, false), canvas.bounds, 96, 96, 1); }
                onResized: function(dx, dy) { canvas.draft = Geometry.fit(Geometry.delta(canvas.gestureStart, dx, dy, true), canvas.bounds, 96, 96, 1); }
                onFinished: {
                    canvas.draft = Geometry.fit(canvas.draft, canvas.bounds, 96, 96, 6);
                    Bar.PluginRegistry.change("place", entry, "test-monitor", canvas.draft);
                }
            }
            Timer {
                interval: 500; running: true; repeat: true
                property int stage: 0
                onTriggered: {
                    if (stage === 0) {
                        pointer.mouseClick(widget, 180, 80, Qt.RightButton, Qt.NoModifier, 1);
                        if (!widget.menuOpen) throw new Error("Right-click did not open menu");
                    } else if (stage === 1) {
                        if (!widget.menuOpen) throw new Error("Menu dismissed after right-click release");
                        widget.forceActiveFocus();
                        pointer.keyClick(Qt.Key_Escape, Qt.NoModifier, 1);
                        if (widget.menuOpen) throw new Error("Escape did not close menu");
                        pointer.mousePress(widget, 80, 12, Qt.LeftButton, Qt.NoModifier, 1);
                        for (let step = 0; step < 20; step++) pointer.mouseMove(widget, 81, 12, 1, Qt.LeftButton, Qt.NoModifier);
                        pointer.mouseRelease(widget, 80, 12, Qt.LeftButton, Qt.NoModifier, 1);
                        if (canvas.draft.x <= 24) throw new Error("Title drag did not move");
                    } else if (stage === 2) {
                        pointer.mousePress(widget, widget.width - 10, widget.height - 10, Qt.LeftButton, Qt.NoModifier, 1);
                        pointer.mouseMove(widget, widget.width + 20, widget.height + 20, 1, Qt.LeftButton, Qt.NoModifier);
                        pointer.mouseRelease(widget, widget.width - 10, widget.height - 10, Qt.LeftButton, Qt.NoModifier, 1);
                        if (canvas.draft.width <= 360 || canvas.draft.height <= 180) throw new Error("Grip did not resize");
                    } else { console.log("POINTER_SAVE_OK"); Qt.quit(); }
                    stage++;
                }
            }
        }
    }
}""".replace('BAR', BAR.as_uri()).replace('GEOMETRY', (BAR / 'PluginGeometry.js').as_uri()))
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=directory,
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                               XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment, text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('POINTER_SAVE_OK', result.stdout + result.stderr)
            saved = json.loads((folder / 'saved.json').read_text())
            self.assertEqual(len(saved), 2)
            self.assertGreater(saved[0]['x'], 24)
            self.assertGreater(saved[1]['width'], saved[0]['width'])
            self.assertGreater(saved[1]['height'], saved[0]['height'])
            self.assertTrue(all(value % 6 == 0 for geometry in saved for value in geometry.values()))
