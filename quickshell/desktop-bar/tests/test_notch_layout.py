"""Render the production notch geometry and surfaces without a desktop connection."""
from bar_frame_source import frame_source
import itertools
from concurrent.futures import ThreadPoolExecutor
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
class NotchLayoutTests(unittest.TestCase):
    def test_notch_edges_and_themes(self):
        shell_source = ((BAR / 'shell.qml').read_text() + frame_source(BAR))
        tab = shell_source.split('                    Item {\n                        id: tabStrip\n                        visible: shell.notchLayout', 1)[1].split('                    HoverHandler {\n                        id: barHover', 1)[0]
        outline = tab.split('id: tabsOutline', 1)[1]
        self.assertNotIn('DesktopStyle', outline)
        # The centre-tab hover comes from the bar's own handler, which also sees the clock and weather.
        self.assertIn('readonly property bool overCenterTab', shell_source)
        self.assertEqual(outline.count('ShapePath {'), 1)
        self.assertIn('EdgeSlopes.outline', outline)
        self.assertNotIn('PanelSurface {', tab)
        icon_visibility = shell_source.split('readonly property bool iconsOpen: ', 1)[1].split('\n', 1)[0]
        status_source = (BAR / 'BarHorizontalStatus.qml').read_text()
        toggle_visibility = status_source.split('id: statusToggle', 1)[1].split('visible: ', 1)[1].split('\n', 1)[0]
        toggle_visibility = toggle_visibility.replace('barHost.', 'bar.').replace('rightSide.host.', 'shell.')
        corner_styles = json.loads((BAR / 'corner-styles.json').read_text())['styles']
        geometry = 'readonly property real tabsPadding:' + shell_source.split(
            '                readonly property real tabsPadding:', 1)[1].split(
            '                readonly property var outerGaps:', 1)[0]
        reveal = shell_source.split('                property bool weatherHovered:', 1)[1].split('                readonly property real centerExtent:', 1)[0]
        reveal = 'property bool weatherHovered:' + reveal
        self.assertIn('duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic', reveal)
        self.assertIn('interval: collapseDelay.interval', reveal)
        self.assertIn('weatherMenu.visible || pendingPanel === weatherMenu', reveal)
        tab = 'Item {\n visible: shell.notchLayout' + tab
        with tempfile.TemporaryDirectory(prefix="eitr-notch-fixture-") as directory:
            folder = Path(directory)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            cases = [(*case, False) for case in itertools.product(
                ('top', 'bottom', 'left', 'right'), (False, True),
                ('left', 'center', 'right'), ('square', 'rounded', 'extra-rounded'), (5, 10))]
            cases.extend((edge, False, alignment, 'rounded', 5, True)
                         for edge in ('top', 'bottom', 'left', 'right')
                         for alignment in ('left', 'right'))
            cases = [(*case, media, False) for case in cases for media in (False, True)]
            cases.extend((edge, False, 'center', 'rounded', 5, False, False, True) for edge in ('top', 'left'))
            jobs = []
            for index, (edge, light, alignment, corners, workspace_count, centered_layout, media, hovered) in enumerate(cases):
                center_panel = alignment == "center"
                capture_folder = Path(os.environ.get('EITR_NOTCH_RENDERS', directory))
                capture_folder.mkdir(parents=True, exist_ok=True)
                capture = capture_folder / f'{edge}-{light}-{alignment}-{corners}-{workspace_count}-{centered_layout}-{media}.png'
                fixture = '''import QtQuick
import QtQuick.Shapes
import Quickshell
import "PanelStyle.js" as PanelStyle
import "BarGeometry.js" as BarGeometry
import "EdgeSlopes.js" as EdgeSlopes
ShellRoot {
id: shell
property bool verticalBar: EDGE === "left" || EDGE === "right"
property real tabStripThickness: 7
property string barEdge: EDGE
property bool notchLayout: true
property bool centeredLayout: CENTERED
property bool statusOpen: false
readonly property bool iconsOpen: ICON_VISIBILITY
        property real workspaceItemSpacing: 4
function barBackground() { return LIGHT ? "#eee9df" : "#202430"; }
FloatingWindow {
    id: bar
    visible: true; implicitWidth: 1600; implicitHeight: 1200
    color: LIGHT ? "#cdc8c0" : "#10131a"
    property bool centeredLayout: CENTERED
    property bool notchLayout: true
    property real panelGap: 24
    property var outerGaps: [9, 15, 21, 27]
    property var panelFocusWindows: []
    property Item stripItem: barContents
    property real normalThickness: shell.verticalBar ? 60 : 30
    property real thinThickness: normalThickness
    property var pendingPanel: null
    Item { id: weatherMenu; visible: false }
    Timer { id: collapseDelay; interval: 350 }
    REVEAL
    Component.onCompleted: weatherHovered = HOVERED
    GEOMETRY
    Item {
        id: sample; anchors.fill: parent
        Rectangle { anchors.fill: parent; color: bar.color }
        Item {
            id: barContents
            width: shell.verticalBar ? bar.thinThickness : parent.width
            height: shell.verticalBar ? parent.height : bar.thinThickness
            x: EDGE === "right" ? parent.width - width : 0
            y: EDGE === "bottom" ? parent.height - height : 0

            TAB
            Text {
                id: centerInfo
                text: shell.verticalBar ? "12:34\\n23 Oct" : "Fri 23 Oct  12:34"
                color: LIGHT ? "#202430" : "#eee9df"; font.pixelSize: 13
                anchors.centerIn: parent
                anchors.alignWhenCentered: false
                anchors.verticalCenterOffset: shell.verticalBar ? 0 : 0
                anchors.horizontalCenterOffset: shell.verticalBar ? 0 : 0
            }
            Text {
                id: barWeather; visible: bar.weatherExpanded; text: "☀ 21°"; color: centerInfo.color; font.pixelSize: 13
                x: shell.verticalBar ? (parent.width - width) / 2 + 0 : centerInfo.x + centerInfo.width + 6
                y: shell.verticalBar ? centerInfo.y + centerInfo.height + 3 : centerInfo.y
            }
            Item { id: verticalMiddle; y: 560 }
            Item { id: verticalMedia; parent: verticalMiddle; y: -110; height: 102; visible: shell.verticalBar && MEDIA
                Text { text: "⏮\\n▶\\n⏭\\n♫"; color: centerInfo.color; font.pixelSize: 16 }
            }
            Item { id: verticalCapture; parent: verticalMiddle; y: -5; property bool shown: false }
            Item { id: verticalCalendarIcon; y: centerInfo.y; height: centerInfo.height }
            Item { id: verticalWeatherIcon; y: barWeather.y; height: barWeather.height }
            Item { id: mediaStrip; x: centerInfo.x - width - 18; y: 3; width: visible ? 69 : 0; height: 24; visible: !shell.verticalBar && MEDIA
                Text { text: "⏮ ▶ ⏭ ♫"; color: centerInfo.color; font.pixelSize: 13 }
            }
            Item { id: barCapture; x: centerInfo.x; property bool shown: false }
            Item { id: verticalEnd; y: barContents.height - 200; visible: shell.verticalBar
                Text { text: "WiFi\\nBT\\nAudio\\nUpdates\\nBell"; color: centerInfo.color; font.pixelSize: 13 }
            }
            Item { id: statusToggle; visible: TOGGLE_VISIBILITY }
            Text { id: rightSide; text: "WiFi  BT  Audio  Updates  Bell"; color: centerInfo.color; font.pixelSize: 13
                visible: !shell.verticalBar; x: parent.width - width - 13; y: (parent.height - height) / 2
            }
                Grid {
                    id: verticalStart
                    columns: shell.verticalBar ? 1 : 2
                    x: shell.verticalBar ? (parent.width - width) / 2 : 12
                    y: shell.verticalBar ? 8 : 3
                    spacing: shell.workspaceItemSpacing
                    Grid {
                        columns: shell.verticalBar ? 1 : WORKSPACES + 2
                        id: mockWorkspaces; spacing: shell.workspaceItemSpacing
                        Repeater { model: WORKSPACES + 2
                            Text { required property int index; text: index === 0 ? "ᛖ" : index === 1 ? "▦" : String(index - 1)
                                width: 24; height: 24; color: centerInfo.color; horizontalAlignment: Text.AlignHCenter }
                        }
                    }
                    Grid {
                        columns: shell.verticalBar ? 1 : 3
                        id: mockStatus; spacing: shell.workspaceItemSpacing
                        Repeater { model: ["◉", "AI", "▣"]
                            Text { required property string modelData; text: modelData; width: 24; height: 24; color: centerInfo.color }
                        }
                    }
                }
                // The bar exposes its left items through BarLeftGroup; the fixture mirrors that.
                QtObject { id: leftGroup; readonly property Item workspaces: mockWorkspaces; readonly property Item hardwareStatus: mockStatus }

        }
    }
    CalendarMenu {
        id: calendar; parent: sample; target: centerInfo; barEdge: EDGE; centered: true
        foreground: centerInfo.color; background: shell.barBackground(); accent: "#83b6a3"
        surfaceColor: shell.barBackground()
        opened: CALENDAR
    }
    DockPanel {
    id: statusPanel; parent: sample; attachmentTarget: statusToggle; attachmentEdge: EDGE
    alignment: "ALIGNMENT"; leadingOffset: 17
    implicitWidth: PANEL_WIDTH; implicitHeight: PANEL_HEIGHT; opened: !CALENDAR
    property string barEdge: EDGE
    property color background: shell.barBackground()
    PanelSurface {
        id: statusSurface
        anchors.fill: parent; hostWindow: statusPanel
        Text { text: "Status panel"; color: centerInfo.color; font.pixelSize: 16 }
    }
}
Timer {
        interval: 400; running: true
        onTriggered: {
            DesktopStyle.styles = CORNER_STYLES;
            DesktopStyle.corners = "CORNERS";
            if (!shell.iconsOpen || statusToggle.visible) throw new Error("Tabs status controls are collapsed or toggle is visible");
            var leadingEnd = shell.verticalBar ? verticalStart.mapToItem(barContents, 0, verticalStart.height).y
                : leftGroup.hardwareStatus.mapToItem(barContents, leftGroup.hardwareStatus.width, 0).x;
            var centerStart = shell.verticalBar ? (MEDIA ? verticalMedia.mapToItem(barContents, 0, 0).y : verticalCalendarIcon.y)
                : (MEDIA ? mediaStrip.x : centerInfo.x);
            var clockEnd = shell.verticalBar ? verticalCalendarIcon.y + verticalCalendarIcon.height : centerInfo.x + centerInfo.width;
            var centerEnd = clockEnd + bar.weatherReveal;
            if (barWeather.visible !== HOVERED) throw new Error("Weather visibility differs from hover");
            if (!MEDIA && !HOVERED && Math.abs(bar.tabCenterStart + bar.tabCenterEnd - (shell.verticalBar ? sample.height : sample.width)) > 0.01)
                throw new Error("Collapsed centre tab is not symmetric");
            if (Math.abs(bar.tabCenterEnd - clockEnd - bar.tabsPadding - (HOVERED ? (shell.verticalBar ? 3 + verticalWeatherIcon.height : 6 + barWeather.width) : 0)) > 0.01)
                throw new Error("Weather reveal did not extend the trailing side");
            var trailingStart = shell.verticalBar ? verticalEnd.y : rightSide.x;
            var paddings = [bar.tabLeadingEnd - leadingEnd, centerStart - bar.tabCenterStart,
                bar.tabCenterEnd - centerEnd, trailingStart - bar.tabTrailingStart];
            if (bar.tabsPadding !== 4 || paddings.some(padding => Math.abs(padding - bar.tabsPadding) > 0.01))
                throw new Error("Unequal Tabs padding: " + JSON.stringify(paddings));
            var point = centerInfo.mapToItem(sample, centerInfo.width / 2, centerInfo.height / 2);
            if (Math.abs((shell.verticalBar ? point.y : point.x) - (shell.verticalBar ? sample.height : sample.width) / 2) > 0.01)
                throw new Error("Clock moved off the screen axis");
            var panel = CALENDAR ? calendar : statusPanel;
            if (!panel.detached || panel.strip !== barContents || panel.transitionDuration !== 320)
                throw new Error("Tabs must reuse detached panel geometry and reveal");
            var gap = EDGE === "top" ? panel.y - bar.normalThickness
                : EDGE === "bottom" ? sample.height - bar.normalThickness - panel.y - panel.height
                : EDGE === "left" ? panel.x - bar.normalThickness
                : sample.width - bar.normalThickness - panel.x - panel.width;
            if (Math.abs(gap - bar.panelGap) > 0.01) throw new Error("Detached panel gap missing");
            var axisCenter = shell.verticalBar ? panel.y + panel.height / 2 : panel.x + panel.width / 2;
            var axisSize = shell.verticalBar ? sample.height : sample.width;
            var panelSize = shell.verticalBar ? panel.height : panel.width;
            var fullPosition = CALENDAR ? (axisSize - panelSize) / 2
                : statusPanel.alignment === "left" ? (shell.verticalBar ? statusPanel.leadingOffset : 0)
                : axisSize - panelSize;
            var leadingInset = shell.verticalBar ? bar.outerGaps[0] : bar.outerGaps[3];
            var trailingInset = shell.verticalBar ? bar.outerGaps[2] : bar.outerGaps[1];
            var expectedPosition = CENTERED ? (axisSize - panelSize) / 2
                : Math.max(leadingInset, Math.min(axisSize - panelSize - trailingInset, fullPosition));
            var position = shell.verticalBar ? panel.y : panel.x;
            if (Math.abs(position - expectedPosition) > 0.01)
                throw new Error("Tabs panel differs from Full alignment with outer insets: " + position + " vs " + expectedPosition);
            if (panel.x < 0 || panel.y < 0 || panel.x + panel.width > sample.width || panel.y + panel.height > sample.height)
                throw new Error("Detached panel clipped");
            if (!CENTERED && (panel.x < bar.outerGaps[3] || panel.y < bar.outerGaps[0]
                || panel.x + panel.width > sample.width - bar.outerGaps[1]
                || panel.y + panel.height > sample.height - bar.outerGaps[2]))
                throw new Error("Tabs panel crossed the screen outer gap");
            var surface = CALENDAR ? calendar.children.find(child => child.toString().startsWith("PanelSurface")) : statusSurface;
            if (!surface || !surface.detached || surface.leadingBodyInset !== 0 || surface.trailingBodyInset !== 0)
                throw new Error("Detached rounded surface missing");
            var frame = surface.children[0].children.find(child => child.objectName === "panelContentFrame");
            if (!frame || frame.width <= 0 || frame.height <= 0 || frame.x < 0 || frame.y < 0
                || frame.x + frame.width > panel.width || frame.y + frame.height > panel.height)
                throw new Error("Panel content clipped");
            sample.grabToImage(function(result) {
                if (!result.saveToFile("CAPTURE")) throw new Error("Capture failed");
                console.log("NOTCH_OK"); Qt.quit();
            });
        }
    }
}
    }'''.replace('HOVERED', str(hovered).lower()).replace('MEDIA', str(media).lower()).replace('TAB', tab).replace('ICON_VISIBILITY', icon_visibility).replace('TOGGLE_VISIBILITY', toggle_visibility).replace('GEOMETRY', geometry).replace('REVEAL', reveal).replace('WORKSPACES', str(workspace_count)).replace('CORNERS', corners).replace('CORNER_STYLES', json.dumps(corner_styles)).replace('EDGE', '"' + edge + '"').replace('LIGHT', str(light).lower()).replace('CENTERED', str(centered_layout).lower()).replace('PANEL_WIDTH', '1800' if alignment == 'right' and corners == 'square' and workspace_count == 10 else '330').replace('PANEL_HEIGHT', '1400' if alignment == 'right' and corners == 'square' and workspace_count == 10 else '300').replace('ALIGNMENT', alignment).replace('CALENDAR', str(center_panel).lower()).replace('CAPTURE', str(capture))
                # Each case renders in its own Quickshell process; they run in parallel below.
                fixture_path = folder / f'fixture-{index}.qml'
                fixture_path.write_text(fixture)
                subtest = dict(edge=edge, light=light, alignment=alignment, centered=centered_layout,
                               corners=corners, workspaces=workspace_count, media=media)
                jobs.append((subtest, fixture_path, capture))
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(ROOT / 'quickshell'), HOME=directory,
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory,
                               XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')

            def render(job):
                try:
                    result = subprocess.run(['quickshell', '-p', str(job[1])], env=environment,
                                            text=True, capture_output=True, timeout=60)
                    return result.returncode, result.stdout + result.stderr
                except subprocess.TimeoutExpired as error:
                    return None, str(error.stdout) + str(error.stderr)

            with ThreadPoolExecutor(max_workers=max(2, (os.cpu_count() or 4) // 4)) as pool:
                results = list(pool.map(render, jobs))
            for (subtest, _, capture), (returncode, output) in zip(jobs, results):
                with self.subTest(**subtest):
                    self.assertIsNotNone(returncode, output)
                    self.assertEqual(returncode, 0, output)
                    self.assertIn('NOTCH_OK', output)
                    self.assertNotIn('ReferenceError', output)
                    self.assertNotIn('TypeError', output)
                    self.assertTrue(capture.is_file())
