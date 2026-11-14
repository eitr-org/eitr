"""Production centre sections and slot grid with an inert clock-slot plugin."""
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from layout_render import BAR, layout_fixture, render_environment, render, capture_path, EDGES, copy_runtime


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class ClockSlotRenderTests(unittest.TestCase):
    def test_layouts_edges_and_palettes_keep_the_clock_centred(self):
        with tempfile.TemporaryDirectory(prefix='eitr-clock-slot-') as directory:
            folder = Path(directory)
            kinds = set()
            for name in ('BarHorizontalCenter', 'BarVerticalCenter'):
                text = (BAR / 'bar' / (name + '.qml')).read_text().replace('import ".."\n', '')
                (folder / (name + '.qml')).write_text(text)
                kinds.update(re.findall(r'^\s*([A-Z]\w+)\s*\{', text, re.M))
            kinds.add('BarTooltip')
            (folder / 'Stub.qml').write_text(layout_fixture('stub'))
            for kind in kinds - {'Item', 'Row', 'Column', 'Behavior', 'NumberAnimation', 'PluginBarItems', 'ClockButton'}:
                (folder / (kind + '.qml')).write_text('import QtQuick\nStub {}\n')
            for name, source in [('ClockButton', 'bar/ClockButton.qml'), ('PluginBarItems', 'plugins/PluginBarItems.qml')]:
                (folder / (name + '.qml')).write_text((BAR / source).read_text().replace('import ".."\n', ''))
            (folder / 'DesktopStyle.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function radius(value) { return value; } function motionDuration(value) { return 0; } }')
            (folder / 'DesktopFonts.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property string family: "DejaVu Sans Mono" }')
            (folder / 'PluginRegistry.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property var clockBarItems: [{title:"World clock"}]; property var barItems: []; function slotItems(slot) { return slot === "clock" ? clockBarItems : []; } }')
            (folder / 'PluginComponent.qml').write_text('''import QtQuick
Item {
    required property var entry
    property bool observing: true
    property string clockFormat: "24h"
    property bool verticalContent: false
    property bool verticalBar: false
    property bool iconSlot: false
    property color foreground
    property color background
    property color accent
    readonly property int barContentHeight: 24
    implicitWidth: entry.slot === "clockEnd" ? 64 : 120
    signal panelRequested(string plugin, string panel)
    Text { anchors.centerIn: parent; rotation: parent.verticalContent ? 90 : 0; text: ({clock:"LIS 14:05", clockEnd:"E", start:"S", status:"R"})[parent.entry.title] || parent.entry.title; color: parent.foreground; font.family: "DejaVu Sans Mono"; font.pixelSize: 12 }
}''')
            (folder / 'BarTooltip.qml').write_text('import QtQuick\nItem { property color background; property color foreground; property Item target; property bool hovered; property string text }')
            registry = []
            for component in folder.glob('*.qml'):
                prefix = 'singleton ' if component.stem in ('DesktopStyle', 'DesktopFonts', 'PluginRegistry') else ''
                registry.append(prefix + component.stem + ' ' + component.name)
            (folder / 'qmldir').write_text('\n'.join(registry) + '\n')
            for layout in ('Full', 'Centered', 'Tabs', 'Islands', 'Dynamic', 'Drop'):
                for edge in EDGES:
                    for light in (False, True):
                        for scenario in ('weather', 'removed', 'slots'):
                            entries = [] if scenario == 'removed' else [{'title': '☁ 21°C', 'slot': 'clockEnd'}]
                            if scenario == 'slots':
                                entries = [{'title': slot, 'slot': slot} for slot in ('start', 'clock', 'clockEnd', 'status')]
                            (folder / 'PluginRegistry.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property var entries: '
                                + json.dumps(entries) + '; function slotItems(slot) { return entries.filter(entry => entry.slot === slot); } }')
                            capture = capture_path('CLOCK_SLOT', directory, f'{scenario}-{layout.lower()}-{edge}-{"light" if light else "dark"}.png')
                            fixture = FIXTURE.replace('EXPECT_CLOCK', str(scenario == 'slots').lower()).replace('LAYOUT', json.dumps(layout)).replace('EDGE', json.dumps(edge)).replace('LIGHT', str(light).lower()).replace('CAPTURE', json.dumps(str(capture)))
                            (folder / 'fixture.qml').write_text(fixture)
                            code, output = render(folder / 'fixture.qml', render_environment(directory), 10)
                            with self.subTest(layout=layout, edge=edge, light=light):
                                self.assertEqual(code, 0, output)
                                self.assertIn('CLOCK_CENTRE_OK', output)
                                for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                                    self.assertNotIn(error, output)
                                self.assertTrue(capture.is_file())


    def test_production_tabs_include_the_clock_slot(self):
        from bar_frame_source import frame_source
        source = (BAR / "shell.qml").read_text() + frame_source(BAR)
        tab = source.split('                    Item {\n                        id: tabStrip\n                        visible: shell.notchLayout', 1)[1].split('                    HoverHandler {\n                        id: barHover', 1)[0]
        tab = 'Item {\n visible: shell.notchLayout' + tab
        geometry = 'readonly property real tabsPadding:' + source.split('                readonly property real tabsPadding:', 1)[1].split('                readonly property var outerGaps:', 1)[0]
        reveal = 'readonly property real weatherExtent:' + source.split('                readonly property real weatherExtent:', 1)[1].split('                readonly property real centerExtent:', 1)[0]
        icon_visibility = source.split('readonly property bool iconsOpen: ', 1)[1].split('\n', 1)[0]
        status_source = (BAR / "bar/BarHorizontalStatus.qml").read_text()
        toggle = status_source.split("id: statusToggle", 1)[1].split("visible: ", 1)[1].split("\n", 1)[0]
        toggle = toggle.replace("barHost.", "bar.").replace("rightSide.host.", "shell.")
        styles = json.loads((BAR / "corner-styles.json").read_text())["styles"]
        with tempfile.TemporaryDirectory(prefix="eitr-clock-tabs-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            for edge in ("top", "left"):
                for light in (False, True):
                    capture = capture_path("CLOCK_SLOT", directory, f"tabs-production-{edge}-{'light' if light else 'dark'}.png")
                    fixture = layout_fixture("notch_layout").replace("Item { id: emptyClockPlugin; width: 0; height: 0 }", '''Item {
                        id: emptyClockPlugin; parent: barContents
                        width: shell.verticalBar ? 24 : 120; height: shell.verticalBar ? 120 : 24
                        x: shell.verticalBar ? centerInfo.x : centerInfo.x - width - 6
                        y: shell.verticalBar ? centerInfo.y - height - 3 : centerInfo.y
                        Text { anchors.centerIn: parent; rotation: shell.verticalBar ? 90 : 0; text:"LIS 14:05"; color:centerInfo.color; font.pixelSize:12 }
                    }''')
                    fixture = fixture.replace(": verticalCalendarIcon.y)", ": emptyClockPlugin.y)").replace(": centerInfo.x);", ": emptyClockPlugin.x);")
                    values = {"EDGE": json.dumps(edge), "LIGHT": str(light).lower(), "CORNERS": "rounded",
                              "CORNER_STYLES": json.dumps(styles), "WORKSPACES": "5", "CENTERED": "false",
                              "PANEL_WIDTH": "330", "PANEL_HEIGHT": "300", "ALIGNMENT": "center", "CALENDAR": "true",
                              "HOVERED": "false", "MEDIA": "false", "TAB": tab, "ICON_VISIBILITY": icon_visibility,
                              "TOGGLE_VISIBILITY": toggle, "GEOMETRY": geometry, "REVEAL": reveal, "CAPTURE": str(capture)}
                    for key, value in values.items():
                        fixture = fixture.replace(key, value)
                    (folder / "fixture.qml").write_text(fixture)
                    code, output = render(folder / "fixture.qml", render_environment(directory), 10)
                    with self.subTest(edge=edge, light=light):
                        self.assertEqual(code, 0, output)
                        self.assertIn("NOTCH_OK", output)
                        for error in ("ReferenceError", "TypeError", "Binding loop", "Cannot anchor", "Unable to assign", "Error:"):
                            self.assertNotIn(error, output)
                        self.assertTrue(capture.is_file())

    def test_real_plugin_loader_natural_size_rotation_and_panel_request(self):
        with tempfile.TemporaryDirectory(prefix="eitr-clock-loader-") as directory:
            folder = Path(directory)
            copy_runtime(folder)
            (folder / "ClockStub.qml").write_text('''import QtQuick
Item {
    required property var api
    implicitWidth: 170
    implicitHeight: 24
    Text { anchors.centerIn: parent; text: "LIS " + (parent.api.clockFormat === "24h" ? "14:05" : "2:05 PM"); color: parent.api.foreground; font.pixelSize: 12 }
}''')
            entry = dict(plugin="clock-fixture", id="clock", kind="barItems", slot="clock", title="Clock",
                         disabled=False, commit="a" * 40, qml="ClockStub.qml", source=(folder / "ClockStub.qml").as_uri(), panel="panel")
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 400; implicitHeight: 300
        Bar.PluginBarItems {
            id: horizontal; x:20; y:20; clockSlot:true
            clockFormat:"24h"; foreground:"white"; background:"black"; accent:"gold"
            entries:[ENTRY]
            property bool opened: false
            onPanelRequested: function(plugin, panel, target) {
                if (plugin !== "clock-fixture" || panel !== "panel" || !target) throw new Error("Wrong panel target");
                opened = true;
            }
        }
        Bar.PluginBarItems {
            id: vertical; x:20; y:70; clockSlot:true; vertical:true
            clockFormat:"24h"; foreground:"white"; background:"black"; accent:"gold"
            entries:[ENTRY]
        }
        Timer {
            interval:500; running:true
            onTriggered: {
                if (horizontal.width !== 170 || horizontal.height !== 24 || vertical.width !== 24 || vertical.height !== 170) {
                    console.error("Natural dimensions lost", horizontal.width, horizontal.height, vertical.width, vertical.height); Qt.exit(1); return;
                }
                const item = horizontal.children.find(child => typeof child.activate === "function");
                if (!item) { console.error("Missing plugin component"); Qt.exit(1); return; }
                item.activate();
                if (!horizontal.opened) { console.error("Panel did not open"); Qt.exit(1); return; }
                console.log("CLOCK_LOADER_OK"); Qt.quit();
            }
        }
    }
}'''.replace("ENTRY", json.dumps(entry))
            (folder / "fixture.qml").write_text(fixture)
            code, output = render(folder / "fixture.qml", render_environment(directory), 10)
            self.assertEqual(code, 0, output)
            self.assertIn("CLOCK_LOADER_OK", output)
            for error in ("ReferenceError", "TypeError", "Binding loop", "Cannot anchor", "Unable to assign", "Error:"):
                self.assertNotIn(error, output.split("CLOCK_LOADER_OK")[0])

FIXTURE = r"""
import QtQuick
import Quickshell
ShellRoot {
    id: shell
    property string layout: LAYOUT
    property string barEdge: EDGE
    property bool verticalBar: barEdge === "left" || barEdge === "right"
    property string barClock: "24h"
    property int barHeight: 40
    property bool barVisible: true
    property bool barPinned: true
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: []
    property string barMediaStyle: "bars"
    property real workspaceItemSize: 24
    property color fg: LIGHT ? "#252936" : "#e9eef1"
    property color activeBg: "#70ba9a"
    property color workspaceMenuBg: LIGHT ? "#f5f0e7" : "#18212b"
    function barBackground() { return workspaceMenuBg; }
    function updateBarSetting(key, value) {}
    FloatingWindow {
        id: window
        visible: true
        implicitWidth: shell.verticalBar ? 160 : 1920
        implicitHeight: shell.verticalBar ? 1080 : 160
        color: LIGHT ? "#e2ddcf" : "#0c1119"
        Item {
            id: bar
            anchors.fill: parent
            property bool centeredLayout: shell.layout === "Centered"
            property bool islandsLayout: shell.layout === "Islands"
            property bool dynamicLayout: shell.layout === "Dynamic"
            property bool dropLayout: shell.layout === "Drop"
            property bool notchLayout: shell.layout === "Tabs"
            property bool expanded: true
            property real leadingReveal: 400
            property real trailingReveal: 260
            property real itemGap: 4
            property real endPadding: 4
            property real islandSpacing: 20
            property real weatherReveal: 50
            property real clockPluginExtent: 166
            property var islandSurfaces: ({aroundClock: 0, afterLogo:0, afterWorkspaces:0})
            property var dynamicSurfaces: ({middleIsland: {expanded: true}, weatherReveal: 50})
            property var dropSurfaces: ({timeOffset: 0})
            property var clockActivity: ({flash:0, bellAngle:0, flashText:"", flashColor:"white"})
            function togglePanel(panel) {}
            function openPluginPanel(plugin, panel, target) {}
            function showPanel(panel) {}
            function showControlCenter(page) {}
            property var notificationCenter: null
            Item { id: hardware; width: 0; height: 0 }
            Stub { id: obs }
            Stub { id: media }
            Stub { id: recording }
            Item {
                id: strip
                width: shell.verticalBar ? 40 : bar.centeredLayout ? 960 : bar.dynamicLayout ? 700 : bar.width
                height: shell.verticalBar ? (bar.centeredLayout ? 960 : bar.dynamicLayout ? 800 : bar.height) : 40
                x: shell.verticalBar ? (shell.barEdge === "right" ? bar.width - width : 0) : (bar.width - width) / 2 - (bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0)
                y: shell.verticalBar ? (bar.height - height) / 2 - (bar.centeredLayout ? (bar.leadingReveal - bar.trailingReveal) / 2 : 0) : shell.barEdge === "bottom" ? bar.height - height : 0
                Rectangle {
                    anchors.fill: parent
                    radius: bar.islandsLayout || bar.dynamicLayout || bar.dropLayout ? 20 : 0
                    color: shell.barBackground()
                }
                PluginBarItems {
                    id: startSlot
                    placementSlot: "start"; vertical: shell.verticalBar
                    foreground:shell.fg; background:shell.workspaceMenuBg; accent:shell.activeBg
                    open: !bar.dropLayout
                    x:shell.verticalBar ? 8 : 350; y:shell.verticalBar ? 280 : 8
                    slotSize:24
                }
                PluginBarItems {
                    id: statusSlot
                    placementSlot: "status"; vertical: shell.verticalBar
                    foreground:shell.fg; background:shell.workspaceMenuBg; accent:shell.activeBg
                    open: !bar.dropLayout
                    x:shell.verticalBar ? 8 : strip.width - 180; y:shell.verticalBar ? strip.height - 100 : 8
                    slotSize:24
                }
                Text {
                    visible:!shell.verticalBar && !bar.dropLayout
                    x:12; y:12; text:"ᛖ   ▦   1  2  3  4  5   ▥   ◉   ♙"
                    color:shell.fg; font.pixelSize:13
                }
                Text {
                    visible:!shell.verticalBar && !bar.dropLayout
                    x:strip.width - 130; y:12; text:"WiFi  ♪  ♧"
                    color:shell.fg; font.pixelSize:13
                }
                BarHorizontalCenter {
                    id: horizontal
                    visible: !shell.verticalBar
                    host: shell; barHost: bar
                    hardwareStatusRef: hardware; workspacesRef: hardware
                    mediaMenuRef: media; obsMenuRef: obs; recordingMenuRef: recording
                    verticalCalendarIconRef: vertical.verticalCalendarIconItem
                    verticalWeatherIconRef: vertical.verticalWeatherIconItem
                }
                BarVerticalCenter {
                    id: vertical
                    visible: shell.verticalBar
                    host: shell; barHost: bar
                    barWeatherRef: horizontal.barWeatherItem
                    calendarMenuRef: horizontal.calendarMenuItem
                    weatherMenuRef: horizontal.weatherMenuItem
                    mediaMenuRef: media; mediaStripRef: horizontal.mediaStripItem
                    obsMenuRef: obs; recordingMenuRef: recording
                }
            }
            Timer {
                interval: 200; running: true
                onTriggered: {
                    const clock = shell.verticalBar ? vertical.verticalCalendarIconItem : horizontal.centerInfoItem;
                    const slot = shell.verticalBar ? vertical.clockPluginsItem : horizontal.clockPluginsItem;
                    const point = clock.mapToItem(bar, clock.width / 2, clock.height / 2);
                    const actual = shell.verticalBar ? point.y : point.x;
                    const expected = (shell.verticalBar ? bar.height : bar.width) / 2;
                    if (Math.abs(actual - expected) > 0.01) { console.error("Clock displaced", actual, expected); Qt.exit(1); return; }
                    if (!bar.dropLayout && EXPECT_CLOCK) {
                        const start = slot.mapToItem(bar, 0, 0);
                        const end = shell.verticalBar ? start.y + slot.height : start.x + slot.width;
                        const beforeClock = shell.verticalBar ? point.y - clock.height / 2 : point.x - clock.width / 2;
                        if (end > beforeClock || slot.width <= 0 || slot.height <= 0) { console.error("Clock slot misplaced"); Qt.exit(1); return; }
                    } else if (slot.width > 0 && slot.height > 0) { console.error("Drop slot visible"); Qt.exit(1); return; }
                    for (const item of [startSlot, statusSlot]) {
                        if (EXPECT_CLOCK && !bar.dropLayout && (item.width !== 24 || item.height !== 24)) {
                            console.error("Outer slot geometry"); Qt.exit(1); return;
                        }
                        if (bar.dropLayout && item.visible) { console.error("Drop outer slot leaked"); Qt.exit(1); return; }
                    }
                    console.log("CLOCK_CENTRE_OK", shell.layout, shell.barEdge, actual, expected);
                    bar.grabToImage(result => { result.saveToFile(CAPTURE); Qt.quit(); });
                }
            }
        }
    }
}
"""
