"""Load the extracted per-screen sections offscreen with inert data and panel controls."""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

from test_islands_layout import qml_block

BAR = Path(__file__).resolve().parents[1]
SECTIONS = ('BarHorizontalCenter', 'BarHorizontalStatus', 'BarVerticalCenter', 'BarVerticalStatus')


class BarSectionTests(unittest.TestCase):
    def test_dependencies_cannot_shadow_the_outside_ids(self):
        shell = (BAR / 'shell.qml').read_text()
        for name in SECTIONS:
            source = (BAR / (name + '.qml')).read_text()
            instance = qml_block(shell, name + ' {')
            self.assertIn('host: shell', instance)
            self.assertIn('barHost: bar', instance)
            for property_name in re.findall(r'required property var (\w+)', source):
                self.assertNotRegex(instance, rf'\b{property_name}:\s*{property_name}\b')
            self.assertNotIn('host: host', source)
            self.assertIn(name + ' ' + name + '.qml', (BAR / 'qmldir').read_text())

    @unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
    def test_sections_bind_and_keep_the_clock_centred_on_each_screen(self):
        shell = (BAR / 'shell.qml').read_text()
        aliases = shell.split('                // Centre and status items remain available', 1)[1]
        aliases = aliases.split('                NotificationPopups {', 1)[0]
        aliases = '\n'.join(line for line in aliases.splitlines() if 'property alias' in line)
        with tempfile.TemporaryDirectory(prefix='eitr-bar-sections-') as directory:
            folder = Path(directory)
            for name in SECTIONS:
                shutil.copy(BAR / (name + '.qml'), folder)
            # All dependencies are inert; this test never loads the desktop or starts a data service.
            (folder / 'qmldir').write_text('singleton DesktopStyle DesktopStyle.qml\n'
                                          'singleton DisplayService DisplayService.qml\n')
            (folder / 'DesktopStyle.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function motionDuration(value) { return 0; } }\n')
            (folder / 'DisplayService.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { function refresh() {} }\n')
            (folder / 'Stub.qml').write_text('''import QtQuick
Item {
    property var host
    property bool compact: false
    property bool open: true
    property bool opened: false
    property bool shown: recording || dictating
    property bool recording: false
    property bool recordingPaused: false
    property bool streaming: false
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: []
    property string icon: ""
    property string tooltip: ""
    property string text: "WiFi"
    property string hoverLabel: ""
    property string title: ""
    property string activeCode: "US"
    property string activeLabel: "English"
    property var layouts: ["us", "br"]
    property var obsState: ({recording: false, paused: false, streaming: false})
    property int iconSize: 16
    property int fontSize: 16
    property int glyphOffsetY: 0
    property real slotWidth: 24
    property real fixedWidth: 24
    property real slotSize: 24
    property real slotSpacing: 4
    property bool clickable: false
    property bool rightClickable: false
    property bool spinning: false
    property bool vertical: false
    property bool autoRefresh: false
    property real temp: 21
    property var player: null
    property bool playing: false
    property bool active: false
    property bool audioEnabled: false
    property string mediaStyle: "wave"
    property string style: "wave"
    property real itemSpacing: 4
    property real indicatorSpacing: 4
    property real availableWidth: 100
    property var networkService
    property var service
    property var controller
    property Item target
    property string barEdge: "top"
    property string kind: ""
    property bool centered: false
    property real maximumHeight: 1000
    property color surfaceColor: "black"
    property color foreground: "white"
    property color background: "black"
    property color accent: "cyan"
    width: open ? (compact ? 30 : slotWidth) : 0
    height: 24
    signal clicked(int button)
    signal recordingClicked()
    signal detailsRequested()
    signal panelRequested(var plugin, var panel, var target)
    signal primarySelected()
    signal observationChanged(bool observing)
    signal captureStarting()
}
''')
            kinds = set()
            for name in SECTIONS:
                kinds.update(re.findall(r'^\s*([A-Z]\w+)\s*\{', (BAR / (name + '.qml')).read_text(), re.M))
            for kind in kinds - {'Item', 'Row', 'Column', 'Behavior', 'NumberAnimation'}:
                (folder / (kind + '.qml')).write_text('import QtQuick\nStub {}\n')
            with (folder / 'qmldir').open('a') as registry:
                for component in folder.glob('*.qml'):
                    if component.stem not in ('DesktopStyle', 'DisplayService'):
                        registry.write(f'{component.stem} {component.name}\n')
            horizontal = '\n'.join(qml_block(shell, name + ' {') for name in SECTIONS[:2])
            vertical = '\n'.join(qml_block(shell, name + ' {') for name in SECTIONS[2:])
            fixture = '''import QtQuick
import Quickshell
ShellRoot {
    id: shell
    property bool verticalBar: false
    property string barEdge: "top"
    property bool notchLayout: false
    property bool centeredLayout: false
    property bool islandsLayout: false
    property bool iconsOpen: true
    property bool statusOpen: true
    property bool barVisible: true
    property bool barPinned: false
    property bool dictating: false
    property bool transcribing: false
    property var dictationLevels: []
    property string barMediaStyle: "wave"
    property string wifiGlyph: "WiFi"
    property real workspaceItemSize: 24
    property real workspaceItemSpacing: 4
    property var screenGaps: [8, 8, 8, 8]
    property color fg: "white"
    property color activeBg: "cyan"
    property color workspaceMenuBg: "black"
    property string updatesIcon: "U"
    property string updatesTooltip: "Updates"
    property var updates: ({checking: false})
    property var battery: ({available: true, percent: 80, status: "Discharging"})
    property string batteryIcon: "B"
    property int remoteObservers: 0
    function barBackground() { return "black"; }
    function updateBarSetting(key, value) {}
    function checkUpdates() {}
    function openSystemUpdate() {}
    QtObject { id: networkOwner }
    QtObject { id: remoteAccessService; property bool allowed: true }
    QtObject { id: notificationCenter; property bool opened: false }
    QtObject { id: batteryMenu; property bool opened: false }
    QtObject { id: mediaMenu; property bool opened: false }
    FloatingWindow {
        visible: true; implicitWidth: 1920; implicitHeight: 1080
        Item {
            id: bar; anchors.fill: parent
            property bool centeredLayout: shell.centeredLayout
            property bool islandsLayout: shell.islandsLayout
            property bool notchLayout: shell.notchLayout
            property bool expanded: true
            property real leadingReveal: 320
            property real trailingReveal: 240
            property real endPadding: shell.verticalBar ? 8 : 12
            property real itemGap: 4
            property real islandSpacing: 16
            property real weatherReveal: 27
            property bool weatherExpanded: true
            property var screen: ({height: 1080})
            function togglePanel(panel) { panel.opened = !panel.opened; }
            function openPluginPanel(plugin, panel, target) {}
ALIASES
            Item {
                id: strip
                width: shell.verticalBar ? 56 : (bar.centeredLayout ? 800 : bar.width)
                height: shell.verticalBar ? (bar.centeredLayout ? 700 : bar.height) : 32
                x: shell.verticalBar ? (shell.barEdge === "right" ? bar.width - width : 0) : (bar.width - width) / 2 - (bar.centeredLayout ? 40 : 0)
                y: shell.verticalBar ? (bar.height - height) / 2 - (bar.centeredLayout ? 40 : 0) : (shell.barEdge === "bottom" ? bar.height - height : 0)
                Item { id: mockWorkspaces; width: 180; height: 24 }
                Item { id: mockStatus; x: 200; width: 80; height: 24 }
                // The bar exposes its left items through BarLeftGroup; the fixture mirrors that.
                QtObject { id: leftGroup; readonly property Item workspaces: mockWorkspaces; readonly property Item hardwareStatus: mockStatus }
                Item {
                    anchors.fill: parent; visible: !shell.verticalBar
                    Stub { id: notificationIcon; anchors.right: parent.right; text: "N" }
HORIZONTAL
                }
                Item { anchors.fill: parent; visible: shell.verticalBar
VERTICAL
                }
            }
            property int step: 0
            Timer {
                interval: 30; running: true; repeat: true
                onTriggered: {
                    const edges = ["top", "bottom", "left", "right"];
                    const mode = Math.floor(bar.step / 8) % 4;
                    shell.barEdge = edges[bar.step % 4];
                    shell.verticalBar = shell.barEdge === "left" || shell.barEdge === "right";
                    shell.centeredLayout = mode === 1;
                    shell.notchLayout = mode === 2;
                    shell.islandsLayout = mode === 3;
                    shell.iconsOpen = bar.step % 8 < 4;
                    bar.width = bar.step < 32 ? 1920 : 1366;
                    bar.height = bar.step < 32 ? 1080 : 768;
                    Qt.callLater(function() {
                        try {
                        const clock = shell.verticalBar ? bar.verticalCalendarIcon : bar.centerInfo;
                        const position = clock.mapToItem(bar, clock.width / 2, clock.height / 2);
                        const actual = shell.verticalBar ? position.y : position.x;
                        const expected = (shell.verticalBar ? bar.height : bar.width) / 2;
                        if (Math.abs(actual - expected) > 0.01) throw new Error("Clock displaced: " + actual + " / " + expected);
                        for (const item of [bar.centerInfo, bar.barCapture, bar.barPin, bar.barWeather,
                                bar.verticalCalendarIcon, bar.verticalCapture, bar.verticalWeatherIcon,
                                bar.wifiIcon, bar.bluetoothIcon, bar.obsIcon, bar.keyboardIcon,
                                bar.verticalWifiIcon, bar.verticalBluetoothIcon, bar.verticalObsIcon]) {
                            if (item.host !== shell) throw new Error("Missing host: " + item);
                        }
                        const calendarTarget = shell.verticalBar ? bar.verticalCalendarIcon : bar.centerInfo;
                        if (bar.calendarMenu.target !== calendarTarget || bar.weatherMenu.target !== (shell.verticalBar ? bar.verticalWeatherIcon : bar.centerInfo))
                            throw new Error("Centre panel target changed");
                        const statusTargets = [[bar.wifiMenu, bar.verticalWifiIcon, bar.wifiIcon],
                            [bar.bluetoothMenu, bar.verticalBluetoothIcon, bar.bluetoothIcon],
                            [bar.brightnessMenu, bar.verticalDisplayIcon, bar.brightnessIcon],
                            [bar.volumeMenu, bar.verticalVolumeIcon, bar.volumeIcon],
                            [bar.keyboardMenu, bar.verticalKeyboardIcon, bar.keyboardIcon]];
                        for (const entry of statusTargets) {
                            const expectedTarget = shell.verticalBar ? entry[1] : shell.iconsOpen ? entry[2] : notificationIcon;
                            if (entry[0].target !== expectedTarget) throw new Error("Status panel target changed");
                        }
                        if (bar.recordingMenu.target !== (shell.verticalBar ? bar.verticalCapture : bar.barCapture)
                                || bar.recordingMenu.controller !== bar.obsMenu)
                            throw new Error("Recording panel wiring changed");
                        if (++bar.step === 64) { console.log("BAR_SECTIONS_OK"); Qt.quit(); }
                        } catch (error) { console.error(error); Qt.exit(1); }
                    });
                }
            }
        }
    }
}
'''.replace('ALIASES', aliases).replace('HORIZONTAL', horizontal).replace('VERTICAL', vertical)
            (folder / 'shell.qml').write_text(fixture)
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(BAR.parent), HOME=directory,
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
                               XDG_DATA_HOME=directory, XDG_RUNTIME_DIR=directory,
                               HYPRLAND_INSTANCE_SIGNATURE='', DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
            result = subprocess.run(['quickshell', '--no-color', '-p', str(folder / 'shell.qml')],
                                    env=environment, text=True, capture_output=True, timeout=15)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('BAR_SECTIONS_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                self.assertNotIn(error, output)
