"""Production Dynamic parenting, motion, independent anchors and rounded input regions."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from layout_render import copy_runtime, render_environment, render, capture_path, EDGES

BAR = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class DynamicLayoutTests(unittest.TestCase):
    def test_islands_are_full_pills_whatever_the_corner_preference(self):
        island = (BAR / 'bar/DynamicIsland.qml').read_text()
        self.assertIn('radius: Math.min(width, height, depth > thickness + 0.5 ? 40 : Infinity) / 2', island)
        self.assertNotIn('DesktopStyle.radius', island)

    def test_open_island_follows_panel_resizes_without_its_own_easing(self):
        # Easing behind the panel's own resize left the panel's content outside the card.
        island = (BAR / 'bar/DynamicIsland.qml').read_text()
        self.assertIn('readonly property bool followsPanel: morphed && panel.opened && panel.revealProgress >= 1', island)
        self.assertIn('Behavior on depth { enabled: island.eased && !island.followsPanel;', island)
        self.assertIn('Behavior on extent { enabled: island.eased && !island.followsPanel;', island)

    def test_edges_appearances_motion_and_panel_holds(self):
        with tempfile.TemporaryDirectory(prefix='eitr-dynamic-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            shutil.copytree(BAR / "assets", folder / "assets", dirs_exist_ok=True)
            for edge in EDGES:
                for light in (False, True):
                    marker = folder / 'theme/current/light.mode'
                    marker.parent.mkdir(parents=True, exist_ok=True)
                    if light:
                        marker.touch()
                    else:
                        marker.unlink(missing_ok=True)
                    for website in (False, True):
                        capture = capture_path('DYNAMIC', directory, f'{edge}-{light}-{website}')
                        fixture = (BAR / 'tests/fixtures/layout/dynamic.qml.in').read_text()
                        source = (BAR / 'bar/BarWindow.qml').read_text()
                        geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
                        geometry = 'width: host.verticalBar ? bar.thinThickness' + geometry
                        geometry = geometry.replace('host.', 'shell.')
                        reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
                        fixture = fixture.replace('GEOMETRY', geometry).replace('RESERVED', reserved)
                        fixture = fixture.replace('EDGE', json.dumps(edge)).replace('LIGHT', str(light).lower()).replace('WEBSITE', str(website).lower()).replace('CAPTURE', json.dumps(str(capture)))
                        (folder / 'fixture.qml').write_text(fixture)
                        code, output = render(folder / 'fixture.qml', render_environment(directory), 20)
                        with self.subTest(edge=edge, light=light, website=website):
                            self.assertEqual(code, 0, output)
                            self.assertIn('DYNAMIC_OK', output)
                            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                                self.assertNotIn(error, output)
                            for state in range(4):
                                self.assertTrue(Path(f'{capture}-{state}.png').is_file())

    def test_animation_delay_holds_and_reduce_motion(self):
        with tempfile.TemporaryDirectory(prefix='eitr-dynamic-motion-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            fixture = '''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    id: shell
    property string barEdge: "top"
    property bool verticalBar: barEdge === "left" || barEdge === "right"
    property bool barPointerHeld: false
    property string dragCandidate: ""
    function barBackground() { return "black"; }
    function barDoubleClick(button) {}
    function updateBarSetting(key, value) {}
    FloatingWindow {
        id: window; visible: true; implicitWidth: 400; implicitHeight: 400
        property real normalThickness: 30
        Bar.DynamicIsland {
            id: island; host: shell; barHost: window
            x: 20; y: 20; restingExtent: 32; fullExtent: 200
        }
        property int edgeIndex: 0
        property int stage: 0
        Timer {
            id: steps; interval: 50; running: true
            onTriggered: {
                try {
                    if (window.stage === 0) {
                        Bar.DesktopStyle.reduceMotion = false;
                        island.hovered = true;
                    } else if (window.stage === 1) {
                        if (!(island.extent > 32 && island.extent < 200)) throw new Error("Motion did not interpolate");
                        interval = 400;
                    } else if (window.stage === 2) {
                        if (island.extent !== 200) throw new Error("Reveal did not settle");
                        island.hovered = false; interval = 100;
                    } else if (window.stage === 3) {
                        if (!island.expanded) throw new Error("Collapse delay missing");
                        interval = 700;
                    } else if (window.stage === 4) {
                        if (island.extent !== 32) throw new Error("Collapse did not settle");
                        Bar.DesktopStyle.reduceMotion = true;
                        island.hovered = true;
                        Qt.callLater(function() {
                            if (island.extent !== 200) { console.error("Reduced motion was animated"); Qt.exit(1); }
                        });
                        island.held = true; island.hovered = false; interval = 400;
                        island.contentExtent = 400;
                        const viewport = island.children.find(child => child.contentX !== undefined);
                        if (shell.verticalBar) viewport.contentY = 50;
                        else viewport.contentX = 50;
                    } else if (window.stage === 5) {
                        if (island.extent !== 200) throw new Error("Panel hold failed after hover delay");
                        island.held = false;
                        if (island.extent !== 32) throw new Error("Reduced collapse was animated");
                        const viewport = island.children.find(child => child.contentX !== undefined);
                        if (viewport.contentX !== 0 || viewport.contentY !== 0) throw new Error("Collapsed island retained scroll offset");
                        shell.barPointerHeld = true;
                        if (island.extent !== 200) throw new Error("Drag hold failed");
                        shell.barPointerHeld = false;
                        if (++window.edgeIndex === 4) { console.log("DYNAMIC_MOTION_OK"); Qt.quit(); return; }
                        shell.barEdge = ["top", "bottom", "left", "right"][window.edgeIndex];
                        window.stage = -1; interval = 50;
                    }
                    window.stage++;
                    restart();
                } catch (error) { console.error(error); Qt.exit(1); }
            }
        }
    }
}'''
            path = folder / 'fixture.qml'
            path.write_text(fixture)
            code, output = render(path, render_environment(directory), 15)
            self.assertEqual(code, 0, output)
            self.assertIn('DYNAMIC_MOTION_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign', 'Error:'):
                self.assertNotIn(error, output)


class LiveRegressionTests(unittest.TestCase):
    """Issues found while iterating on the bar layouts with the owner (2026-11-03/04)."""

    def source(self, relative):
        return (BAR / relative).read_text()

    def test_centered_and_tabs_slopes_start_at_the_content(self):
        window = self.source('bar/BarWindow.qml')
        self.assertIn('readonly property real centerExtent: host.verticalBar ? 56 : centerInfo.width\n', window)
        self.assertIn('readonly property real tabsPadding: 0\n', window)
        self.assertIn('readonly property real endPadding: host.verticalBar ? 8 : 4\n', window)

    def test_left_group_has_no_filler_to_land_behind(self):
        placement = self.source('bar/BarHorizontalPlacement.qml')
        self.assertIn('Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter', placement)
        self.assertNotIn('Layout.fillWidth: true', placement)

    def test_dynamic_moves_groups_without_freezing_their_geometry(self):
        dynamic = self.source('bar/BarDynamic.qml')
        states = dynamic[dynamic.index('states: ['):]
        self.assertNotIn('ParentChange', states)
        self.assertIn('PropertyChanges { target: barHost.leftGroup; width: barHost.leftGroup.implicitWidth }', states)

    def test_cards_grow_from_their_own_icon(self):
        center = self.source('bar/BarHorizontalCenter.qml')
        self.assertIn('morphAnchor: centerSection.host.verticalBar ? verticalWeatherIconRef : barWeather', center)
        dock = self.source('components/DockPanel.qml')
        self.assertIn('pillFor(morphAnchor || attachmentTarget)', dock)
        self.assertIn('const iconOf = panel => panel.morphAnchor || panel.attachmentTarget;', self.source('bar/BarDynamic.qml'))

    def test_islands_cards_open_from_the_logo_push_neighbours_and_hide_their_pill(self):
        islands = self.source('bar/BarIslands.qml')
        self.assertIn('if (item === barHost.stripItem) return logoPill;', islands)
        self.assertIn('visible: barHost.islandsLayout && shown && !carded', islands)
        # Hiding the carded pill must not detach its panel from it.
        self.assertIn('if (pill.itemPosition === undefined || !pill.shown) continue;', islands)
        self.assertNotIn('!pill.visible', islands)
        # The pill stays hidden until its card has finished shrinking.
        self.assertIn('(candidate.visible || candidate === barHost.pendingPanel) && candidate.morphPill', islands)
        self.assertIn('Binding { target: first; property: "opacity"; value: 0; when: carded }', islands)
        for pill, grow in (('clockPill', 'center'), ('mediaStrip', 'end'), ('barCapture', 'end'), ('notificationIcon', 'end')):
            line = next(line for line in islands.splitlines() if pill in line and 'IslandSurface {' in line)
            self.assertIn(f'grow: "{grow}"', line)
        self.assertIn('barWindow.islandSurfaces.afterLogo', self.source('bar/BarLeftGroup.qml'))
        self.assertIn('barWindow.islandSurfaces.afterWorkspaces', self.source('bar/BarLeftGroup.qml'))
        self.assertEqual(self.source('bar/BarHorizontalCenter.qml').count('barHost.islandSurfaces.aroundClock'), 3)
        vertical = self.source('bar/BarVerticalPlacement.qml')
        self.assertIn('barHost.islandSurfaces.afterLogo', vertical)
        self.assertIn('barHost.islandSurfaces.afterWorkspaces', vertical)
        self.assertEqual(self.source('bar/BarVerticalCenter.qml').count('barHost.islandSurfaces.aroundClock'), 3)

    def test_twelve_hour_clocks_never_show_the_24_hour_number(self):
        clock = self.source('bar/ClockButton.qml')
        self.assertNotIn('"h:mm"', clock)
        self.assertNotIn('"hh\\nmm"', clock)
        self.assertEqual(clock.count('(clock.now.getHours() + 11) % 12 + 1'), 2)

    def test_auto_hide_stays_revealed_while_moving_along_the_bar(self):
        # Revealed from a screen corner, the pointer crosses click-through gaps on its way
        # to an island; the trigger must cover the bar's depth while revealed.
        window = self.source('bar/BarWindow.qml')
        sensor = window[window.index('id: edgeSensor'):window.index('HoverHandler { id: edgeHover }')]
        self.assertIn('readonly property real depth: autoHide.progress > 0 ? bar.reservedThickness : 1', sensor)
        self.assertIn('width: host.verticalBar ? depth : bar.width', sensor)
        self.assertIn('height: host.verticalBar ? bar.height : depth', sensor)
