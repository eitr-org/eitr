"""Exercise production Islands surfaces and their rounded input regions offscreen."""
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

from PIL import Image

BAR = Path(__file__).resolve().parents[1]


def qml_block(source, marker):
    start = source.index(marker)
    opening = source.index('{', start)
    depth = 1
    cursor = opening + 1
    while depth:
        depth += (source[cursor] == '{') - (source[cursor] == '}')
        cursor += 1
    return source[start:cursor]


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class IslandsLayoutTests(unittest.TestCase):
    def test_pills_edges_corners_players_and_input(self):
        source = (BAR / 'shell.qml').read_text()
        surfaces = qml_block(source, '                Item {\n                    id: islandSurfaces')
        targets = ('verticalControlCenterLogo', 'controlCenterLogo', 'verticalOverviewIcon', 'overviewIcon',
                   'verticalWorkspaces', 'verticalHardware', 'hardwareStatus',
                   'verticalCalendarIcon', 'centerInfo', 'verticalWeatherIcon', 'barWeather',
                   'verticalMedia', 'mediaStrip', 'verticalCapture', 'barCapture', 'verticalEnd',
                   'rightSide', 'notificationIcon')
        # The left group's items are reached through BarLeftGroup in the bar; the fixture names them directly.
        surfaces = surfaces.replace('leftGroup.', '')
        surfaces = re.sub(r'\b(?:bar\.)?(' + '|'.join(targets) + r')\b', lambda match: 'barContents.' + match[1], surfaces)
        component = qml_block(source, '                component IslandSurface: Rectangle')
        geometry = source.split('                    id: barContents\n', 1)[1].split('                    Item {', 1)[0]
        self.assertIn('shell.centeredLayout || shell.islandsLayout ? null : barContents', source)
        self.assertIn('IslandMask { surfaces: islandSurfaces.children }', source)
        self.assertIn('!!hostWindow.islandsLayout', (BAR / 'DockPanel.qml').read_text())
        with tempfile.TemporaryDirectory(prefix='eitr-islands-') as directory:
            folder = Path(directory)
            for filename in BAR.iterdir():
                if filename.suffix in ('.qml', '.js') or filename.name in ('qmldir', 'corner-styles.json'):
                    shutil.copy(filename, folder / filename.name)
            for edge in ('top', 'bottom', 'left', 'right'):
                for corners in ('square', 'rounded', 'extra-rounded'):
                    capture_folder = Path(os.environ.get('EITR_ISLANDS_RENDERS', directory))
                    capture_folder.mkdir(parents=True, exist_ok=True)
                    capture = capture_folder / f'{edge}-{corners}.png'
                    fixture = '''import QtQuick
import Quickshell
import "PanelStyle.js" as PanelStyle
ShellRoot {
    id: shell
    property string barEdge: EDGE
    property bool verticalBar: barEdge === "left" || barEdge === "right"
    property bool islandsLayout: true
    property bool barVisible: true
    property bool barAutoHide: false
    property bool barPointerHeld: false
    property string dragCandidate: ""
    property real surfaceAlpha: 1
    function barBackground() { return Qt.rgba(1, 1, 1, surfaceAlpha); }
    function barDoubleClick(button) {}
    function updateBarSetting(key, value) {}
    FloatingWindow {
        id: bar
        visible: true; implicitWidth: shell.verticalBar ? 300 : 1920; implicitHeight: shell.verticalBar ? 1920 : 300
        color: "black"
        property bool islandsLayout: true
        property bool centeredLayout: false
        property real normalThickness: shell.verticalBar ? 60 : 30
        property real reservedThickness: normalThickness + (islandsLayout ? islandGap : 0)
        property real exclusiveZone: EXCLUSION
        property real thinThickness: normalThickness
        property real islandGap: 6
        property real islandSpacing: islandGap * 2 + 8
        property Item stripItem: barContents
        property real panelGap: 12
        property var outerGaps: [12, 12, 12, 12]
        property real centerExtent: 100
        property real leadingReveal: 0
        property real trailingReveal: 0
        QtObject { id: autoHide; property real progress: 1 }
        Item {
            id: sample
            anchors.fill: parent
        Item {
            id: barContents
            GEOMETRY
            property bool playing: false
            property bool captureShown: false
            property bool mediaFits: true
            property real clockLength: 100
            property real weatherLength: 54
            property Item controlCenterLogo: logo
            property Item verticalControlCenterLogo: logo
            property Item overviewIcon: workspaces
            property Item verticalOverviewIcon: workspaces
            property Item verticalWorkspaces: workspaces
            property Item hardwareStatus: hardware
            property Item verticalHardware: hardware
            property Item centerInfo: clock
            property Item verticalCalendarIcon: clock
            property Item barWeather: weather
            property Item verticalWeatherIcon: weather
            property Item mediaStrip: media
            property Item verticalMedia: media
            property Item barCapture: capture
            property Item verticalCapture: capture
            property Item rightSide: status
            property Item verticalEnd: status
            property Item notificationIcon: status
            component Slot: Item {
                property real along: 0
                property real extent: 24
                x: shell.verticalBar ? (bar.normalThickness - width) / 2 : along
                y: shell.verticalBar ? along : (bar.normalThickness - height) / 2
                width: shell.verticalBar ? 24 : extent
                height: shell.verticalBar ? extent : 24
            }
            Slot { id: logo; along: 16 }
            Slot { id: workspaces; along: logo.along + logo.extent + bar.islandSpacing; extent: 164 }
            Slot { id: hardware; along: workspaces.along + workspaces.extent + bar.islandSpacing; extent: 80 }
            Slot { id: clock; along: ((shell.verticalBar ? barContents.height : barContents.width) - extent) / 2; extent: barContents.clockLength }
            Slot { id: weather; along: clock.along + clock.extent + bar.islandSpacing; extent: barContents.weatherLength }
            Slot { id: capture; property bool shown: barContents.captureShown; extent: shown ? 24 : 0; along: clock.along - extent - (shown ? bar.islandSpacing : 0) }
            Slot { id: media; property var player: barContents.playing ? ({}) : null; visible: player !== null && barContents.mediaFits; along: capture.along - extent - bar.islandSpacing; extent: 100 }
            Slot { id: status; extent: 52; along: (shell.verticalBar ? barContents.height : barContents.width) - extent - 16 }
            SURFACES
            COMPONENT
        }
        }
        DockPanel {
            id: panel
            attachmentTarget: clock
            attachmentEdge: shell.barEdge
            implicitWidth: 4000; implicitHeight: 4000
            opened: true
        }
        IslandMask { id: input; surfaces: islandSurfaces.children }
        function contains(horizontal, vertical) {
            for (var region of input.regions) {
                if (!region.item) continue;
                const origin = region.item.mapToItem(bar.contentItem, 0, 0);
                const localX = horizontal - origin.x;
                const localY = vertical - origin.y;
                if (localX < 0 || localY < 0 || localX >= region.item.width || localY >= region.item.height) continue;
                const across = Math.max(0, region.radius - Math.min(localX, region.item.width - localX));
                const inward = Math.max(0, region.radius - Math.min(localY, region.item.height - localY));
                if (across * across + inward * inward <= region.radius * region.radius) return true;
            }
            return false;
        }
        function verify() {
            if (bar.exclusiveZone !== bar.normalThickness + bar.islandGap) throw new Error("Wrong reserved window space");
            if (!panel.detached || panel.centeredPlacement || panel.transitionDuration !== DesktopStyle.motionDuration(320)) throw new Error("Wrong detached panel mode");
            if (panel.x < 12 || panel.y < 12 || panel.x + panel.width > bar.width - 12 || panel.y + panel.height > bar.height - 12) throw new Error("Panel crossed outer gap");
            const pills = islandSurfaces.children;
            if (pills.length !== 8) throw new Error("Wrong pill grouping");
            for (var index = 0; index < pills.length; index++) {
                const pill = pills[index];
                const expected = index === 5 ? barContents.playing && barContents.mediaFits : index === 6 ? barContents.captureShown : true;
                if (pill.visible !== expected) throw new Error("Conditional pill leaked " + index);
                if (input.regions[index].item !== (expected ? pill : null)) throw new Error("Hidden pill captured input " + index);
                if (!expected) continue;
                if (Math.abs(pill.color.a - shell.surfaceAlpha) > .01) throw new Error("Appearance ignored");
                if (pill.radius !== DesktopStyle.radius(PanelStyle.cornerRadius)) throw new Error("Corner preference ignored");
                const point = pill.mapToItem(bar.contentItem, 0, 0);
                if (!contains(point.x + pill.width / 2, point.y + pill.height / 2)) throw new Error("Pill missing input");
                if (contains(point.x - 2, point.y - 2)) throw new Error("Gap captured input");
                const distance = shell.barEdge === "top" ? point.y : shell.barEdge === "bottom" ? bar.height - point.y - pill.height : shell.barEdge === "left" ? point.x : bar.width - point.x - pill.width;
                if (Math.abs(distance - bar.islandGap) > .001) throw new Error("Wrong outer gap " + distance);
                if (pill.radius > 0 && contains(point.x, point.y)) throw new Error("Rounded corner captured input");
            }
            const clock = pills[3];
            const weather = pills[4];
            const center = shell.verticalBar ? clock.y + clock.height / 2 : clock.x + clock.width / 2;
            const length = shell.verticalBar ? bar.height : bar.width;
            if (Math.abs(center - length / 2) > .001) throw new Error("Clock shifted");
            const gap = shell.verticalBar ? weather.y - clock.y - clock.height : weather.x - clock.x - clock.width;
            if (Math.abs(gap - 2 * bar.islandGap) > .001) throw new Error("Weather shares clock pill");
        }
        Timer {
            interval: 120; running: true; repeat: true
            property int stage: 0
            onTriggered: {
                try {
                    if (stage === 0) {
                        DesktopStyle.styles = STYLES;
                        DesktopStyle.corners = CORNERS;
                    } else if (stage === 1) {
                        bar.verify(); barContents.playing = true; barContents.captureShown = true;
                        barContents.clockLength = 120; barContents.weatherLength = 70;
                        shell.surfaceAlpha = .38; DesktopStyle.reduceMotion = true;
                    } else if (stage === 2) {
                        bar.verify(); barContents.mediaFits = false; barContents.captureShown = false;
                        bar.islandGap = 20;
                    } else if (stage === 3) {
                        bar.verify(); panel.opened = false; autoHide.progress = 0; shell.barAutoHide = true;
                        if (bar.exclusiveZone !== 0) throw new Error("Auto-hide reserved window space");
                    } else if (stage === 4) {
                        for (var pill of islandSurfaces.children) {
                            if (!pill.visible) continue;
                            const point = pill.mapToItem(bar.contentItem, 0, 0);
                            if (!(point.x + pill.width <= 0 || point.y + pill.height <= 0 || point.x >= bar.width || point.y >= bar.height)) throw new Error("Auto-hidden pill still on screen");
                        }
                        autoHide.progress = 1; shell.barAutoHide = false; bar.islandGap = 6; shell.surfaceAlpha = 1; DesktopStyle.reduceMotion = false;
                    } else if (stage === 5) {
                        bar.verify();
                        if (!sample.grabToImage(function(result) {
                            result.saveToFile(CAPTURE);
                            console.log("ISLANDS_OK"); Qt.quit();
                        })) throw new Error("Cannot capture Islands fixture");
                    }
                    stage++;
                } catch (error) { console.error(error); Qt.exit(1); }
            }
        }
    }
}'''
                    for key, value in {'EDGE': json.dumps(edge), 'CORNERS': json.dumps(corners),
                                       'STYLES': json.dumps(json.loads((BAR / 'corner-styles.json').read_text())['styles']),
                                       'GEOMETRY': geometry, 'SURFACES': surfaces, 'COMPONENT': component,
                                       'EXCLUSION': source.split('                exclusiveZone: ', 1)[1].split('\n', 1)[0],
                                       'CAPTURE': json.dumps(str(capture))}.items():
                        fixture = fixture.replace(key, value)
                    path = folder / f'{edge}-{corners}.qml'
                    path.write_text(fixture)
                    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                       QML_IMPORT_PATH=str(BAR.parent), EITR_CODE_ROOT=str(BAR.parents[1]),
                                       XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory,
                                       XDG_CACHE_HOME=directory, XDG_DATA_HOME=directory, XDG_RUNTIME_DIR=directory,
                                       DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                    try:
                        result = subprocess.run(['quickshell', '-p', str(path)], env=environment,
                                                capture_output=True, text=True, timeout=10)
                    except subprocess.TimeoutExpired as error:
                        self.fail(f'{edge}/{corners}: {error.stdout!r} {error.stderr!r}')
                    with self.subTest(edge=edge, corners=corners):
                        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                        self.assertIn('ISLANDS_OK', result.stdout + result.stderr)
                        self.assertNotIn('Error:', result.stdout + result.stderr)
                        image = Image.open(capture).convert('RGB')
                        transverse = 300 - 12 - (60 if edge in ('left', 'right') else 30) // 2 if edge in ('bottom', 'right') else 12 + (60 if edge in ('left', 'right') else 30) // 2
                        point = (transverse, 960) if edge in ('left', 'right') else (960, transverse)
                        self.assertGreater(image.getpixel(point)[0], 240)
