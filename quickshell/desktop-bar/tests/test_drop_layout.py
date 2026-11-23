"""Drop: the resting time pill on every edge, and the drop it falls from with auto-hide."""
from bar_frame_source import eager_projection
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from layout_render import copy_runtime, render_environment, render, capture_path, layout_fixture, EDGES

BAR = Path(__file__).resolve().parents[1]


class DropSourceTests(unittest.TestCase):
    def source(self, relative):
        return (BAR / relative).read_text()

    def test_drop_is_the_sixth_layout_after_dynamic(self):
        choices = json.loads((BAR.parents[1] / 'tools/choice-lists.json').read_text())
        layouts = [row['id'] for row in choices['bar_layouts']]
        self.assertEqual(layouts[-2:], ['dynamic', 'drop'])

    def test_drop_reuses_the_dynamic_island_and_follows_the_slide(self):
        drop = self.source('bar/BarDrop.qml')
        self.assertIn('DynamicIsland {', drop)
        self.assertIn('readonly property real reveal: barHost.autoHideRef.progress', drop)
        # The auto-hide fall follows the slide exactly; only growing into the dashboard eases.
        self.assertIn('eased: drop.reveal >= 1', drop)
        self.assertNotIn('ParentChange', drop)
        self.assertIn('BarDrop bar/BarDrop.qml', self.source('qmldir'))

    def test_drop_pill_stays_in_place_while_the_rest_of_the_bar_slides(self):
        window = self.source('bar/BarWindow.qml')
        self.assertIn('readonly property real distance: bar.dropLayout ? 0 :', window)
        self.assertIn('readonly property bool floatingIslands: islandsLayout || dynamicLayout || dropLayout', window)
        self.assertIn('IslandMask { surfaces: barHost.dropSurfaces ? barHost.dropSurfaces.surfaces : [] }', self.source('bar/BarInputMask.qml'))


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class DropRenderTests(unittest.TestCase):
    def test_rest_pill_and_auto_hide_dot_on_every_edge(self):
        with tempfile.TemporaryDirectory(prefix='eitr-drop-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
            geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
            geometry = ('width: host.verticalBar ? bar.thinThickness' + geometry).replace('host.', 'shell.')
            reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
            for edge in EDGES:
                for light in (False, True):
                    capture = capture_path('DROP', directory, f'{edge}-{"light" if light else "dark"}')
                    fixture = layout_fixture('drop').replace('GEOMETRY', geometry).replace('RESERVED', reserved)
                    fixture = fixture.replace('EDGE', json.dumps(edge)).replace('LIGHT', str(light).lower())
                    fixture = fixture.replace('CAPTURE', json.dumps(str(capture)))
                    (folder / 'fixture.qml').write_text(fixture)
                    code, output = render(folder / 'fixture.qml', render_environment(directory), 20)
                    with self.subTest(edge=edge, light=light):
                        self.assertEqual(code, 0, output)
                        self.assertIn('DROP_OK', output)
                        for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                            self.assertNotIn(error, output)
                        for shot in ('rest', 'dot', 'grow'):
                            self.assertTrue(Path(f'{capture}-{shot}.png').is_file())

    def test_hover_card_clicks_weather_and_auto_hide(self):
        with tempfile.TemporaryDirectory(prefix='eitr-drop-clock-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
            geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
            geometry = ('width: host.verticalBar ? bar.thinThickness' + geometry).replace('host.', 'shell.')
            reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
            fixture = layout_fixture('drop').split('            Bar.DockPanel {', 1)[0]
            fixture = fixture.replace('import QtQuick\n', 'import QtQuick\nimport QtTest\n')
            fixture = fixture.replace('property var contentItem: window.contentItem', 'property var contentItem: bar')
            fixture = fixture.replace('autoHide: shell.barAutoHide }',
                                      'autoHide: shell.barAutoHide; held: drop.clockCardOpen }')
            fixture = fixture.replace('property bool barAutoHide: false', 'property bool barAutoHide: true')
            fixture = fixture.replace('id: bar\n', 'id: bar\n            property bool attachedIslands: ATTACHED\n')
            fixture = fixture.replace('property real islandGap: 6', 'property real islandGap: ATTACHED ? 0 : 6')
            fixture = fixture.replace('alerting: false})', 'alerting: bar.testAlert})')
            fixture = fixture.replace('property var calendarMenu: null', '''property var calendarMenu: ({
                reminders: [{id: "one", text: "Reminder", due: new Date().setHours(10, 0, 0, 0) / 1000}], events: []
            })''')
            fixture = fixture.replace('property bool opened: false\n                function show(page) {}', '''property bool opened: false
                property real width: 520
                property real height: 220
                property real revealProgress: 0
                function show(page) { bar.destination = page; opened = true; }
                function showWeather() { show("weather"); }''')
            fixture = fixture.replace('            function closePanels() {}', '''
            property bool testAlert: false
            property string destination: ""
            function panel(kind) { return kind === "dashboard" ? dropDashboard : null; }
            function togglePanel(target) { target.show("home"); }
            function closePanels() { dropDashboard.opened = false; }
''')
            fixture = fixture.replace('implicitWidth: shell.verticalBar ? 240 : 1920', 'implicitWidth: 900')
            broker = folder / 'services/DesktopData.qml'
            broker.write_text(broker.read_text().replace('    Component.onCompleted: broker.running = true\n', ''))
            registry = next(folder.rglob('PluginRegistry.qml'))
            registry.write_text(registry.read_text().replace(
                next(line for line in registry.read_text().splitlines() if 'readonly property bool weatherEnabled:' in line),
                '    readonly property bool weatherEnabled: true'))
            fixture += """
            TestCase { id: mouse; name: "DropClockHover"; when: false }
            function findWeather(item) {
                if (item.objectName === "dropClockWeather") return item;
                for (const child of item.children) {
                    const found = findWeather(child);
                    if (found) return found;
                }
                return null;
            }
            Component.onCompleted: {
                if (!WEATHER) return;
                Bar.DesktopData.client.states["weather.default"] = {data: {text: "󰖙 24°", temp: "24°"}};
                Bar.DesktopData.publish();
            }
            Timer {
                interval: 800; running: true
                property int stage: 0
                onTriggered: {
                    const pill = drop.pillSurface;
                    const centre = pill.mapToItem(bar, pill.width / 2, pill.height / 2);
                    const restY = shell.barEdge === "top" ? bar.edgeGap + 15 : bar.height - bar.edgeGap - 15;
                    try {
                        if (stage === 0) {
                            if (drop.clockCardOpen || drop.reveal !== 0) throw new Error("Hidden Drop opened its card");
                            Bar.DesktopStyle.reduceMotion = false;
                            autoHide.pointerInside = true;
                            interval = 400;
                        } else if (stage === 1) {
                            mouse.mouseMove(bar, bar.width / 2, restY);
                            autoHide.pointerInside = false;
                            interval = 130;
                        } else if (stage === 2) {
                            if (!drop.clockCardOpen || pill.depth <= pill.thickness || pill.depth >= pill.targetDepth)
                                throw new Error("Hover failed to animate: " + [pill.depth, drop.reveal, drop.canGlance, drop.pointerInsidePill, drop.pillOrigin, pill.hovered, restY, pill.hoverExpanded, drop.clockCardOpen, pill.targetDepth, pill.eased, Bar.DesktopStyle.reduceMotion]);
                            interval = 430;
                        } else if (stage === 3) {
                            if (Math.abs(centre.x - bar.width / 2) > 0.5 || pill.depth !== 190) throw new Error("Card not centred or full depth");
                            mouse.mouseMove(bar, centre.x, centre.y);
                            bar.grabToImage(result => result.saveToFile(CAPTURE));
                        } else if (stage === 4) {
                            if (!drop.clockCardOpen || drop.reveal !== 1) throw new Error("Card did not hold under pointer");
                            mouse.mouseMove(bar, 40, bar.height / 2);
                            interval = 150;
                        } else if (stage === 5) {
                            if (!drop.clockCardOpen) throw new Error("Card collapsed before leave delay");
                            interval = 550;
                        } else if (stage === 6) {
                            if (drop.clockCardOpen || pill.depth > 31) throw new Error("Card did not collapse");
                            Bar.DesktopStyle.reduceMotion = true;
                            autoHide.pointerInside = true;
                            shell.barPointerHeld = true;
                            mouse.mouseMove(bar, bar.width / 2, restY);
                            interval = 90;
                        } else if (stage === 7) {
                            if (drop.clockCardOpen) throw new Error("Card opened during a drag");
                            bar.testAlert = true;
                            shell.barPointerHeld = false;
                        } else if (stage === 8) {
                            if (drop.clockCardOpen) throw new Error("Card overrode a notification alert");
                            bar.testAlert = false;
                        } else if (stage === 9) {
                            if (!drop.clockCardOpen || pill.depth !== 190) throw new Error("Reduce motion did not settle");
                            mouse.mouseClick(bar, centre.x, centre.y, Qt.RightButton);
                            if (bar.destination !== "controls" || pill.panel !== bar.dropDashboard) throw new Error("Right click missed Quick controls");
                            mouse.mouseMove(bar, 40, bar.height / 2);
                            bar.closePanels();
                        } else if (stage === 10) {
                            mouse.mouseMove(bar, bar.width / 2, restY);
                        } else {
                            if (!drop.clockCardOpen) throw new Error("Card did not reopen");
                            const weather = bar.findWeather(pill.hoverCard);
                            if (!!(weather && weather.visible) !== WEATHER) throw new Error("Weather visibility does not match available data: " + [weather, weather && weather.temperature, Bar.PluginRegistry.weatherEnabled, JSON.stringify(Bar.DesktopData.topics)]);
                            if (WEATHER) {
                                const target = weather.mapToItem(bar, weather.width / 2, weather.height / 2);
                                mouse.mouseClick(bar, target.x, target.y);
                            } else mouse.mouseClick(bar, centre.x, centre.y);
                            if (bar.destination !== (WEATHER ? "weather" : "home") || pill.panel !== bar.dropDashboard)
                                throw new Error("Click sent to wrong page: " + bar.destination);
                            console.log("DROP_CLOCK_OK"); Qt.quit();
                        }
                        stage++;
                        restart();
                    } catch (error) { console.error(error); Qt.exit(1); }
                }
            }
        }
    }
}
"""
            for edge in ('top', 'bottom'):
                for light in (False, True):
                    for attached in (False, True):
                        for weather in (False, True):
                            with self.subTest(edge=edge, light=light, attached=attached, weather=weather):
                                filename = f'clock-{edge}-{"light" if light else "dark"}-{"attached" if attached else "floating"}-{"weather" if weather else "no-weather"}.png'
                                capture = capture_path('DROP_CLOCK', directory, filename)
                                rendered = fixture
                                for token, value in {'GEOMETRY': geometry, 'RESERVED': reserved, 'EDGE': json.dumps(edge),
                                                     'LIGHT': json.dumps(light), 'ATTACHED': json.dumps(attached),
                                                     'WEATHER': json.dumps(weather), 'CAPTURE': json.dumps(str(capture))}.items():
                                    rendered = rendered.replace(token, value)
                                (folder / 'fixture.qml').write_text(rendered)
                                code, output = render(folder / 'fixture.qml', render_environment(directory, (900, 400)), 8)
                                self.assertEqual(code, 0, output)
                                self.assertIn('DROP_CLOCK_OK', output)
                                for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign'):
                                    self.assertNotIn(error, output)
                                self.assertTrue(capture.is_file())


if __name__ == '__main__':
    unittest.main()
