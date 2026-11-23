"""Render the existing carousel inside the real Dynamic and Drop clock islands."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bar_frame_source import eager_projection
from layout_render import BAR, capture_path, copy_runtime, layout_fixture, render, render_environment


def offscreen_picker(folder):
    picker = folder / 'panels/AppearancePicker.qml'
    source = picker.read_text()
    start = source.index('    Variants {')
    end = source.index('    PanelWindow {\n        id: overlay', start)
    source = source[:start] + source[end:]
    source = source.replace('PanelWindow {', 'FloatingWindow {\n        implicitWidth: 1280; implicitHeight: 800')
    source = '\n'.join(line for line in source.splitlines() if not any(
        token in line for token in ('anchors { top:', 'exclusionMode:', 'WlrLayershell.', 'screen: picker.targetScreen')))
    source = source.replace('layer.enabled: true', 'layer.enabled: false')
    source = source.replace('layer.effect: MultiEffect { maskEnabled: true; maskSource: roundedMask }', '')
    picker.write_text(source)
    # The render uses fixture catalogs. No wallpaper previews are applied to the desktop.
    model = folder / 'settings/SettingsAppearanceModel.qml'
    model.write_text(model.read_text().replace('function wallpaperAction(action, extra) {',
                                               'function wallpaperAction(action, extra) {}\n    function unusedAction(action, extra) {')
                     .replace('    Component.onDestruction: {', '    function unusedDestruction() {')
                     .replace('applyProcess.command = [Eitr.Paths.code("walker/scripts/actions/") + script, items[selectedIndex].value];',
                              'applyProcess.command = ["true"];'))


def docked_fixture(layout, mode, geometry, reserved, catalog, capture, width):
    fixture = layout_fixture(layout).split('            Bar.DockPanel {', 1)[0]
    fixture = fixture.replace('            property Item stripItem: strip\n', '')
    fixture = fixture.replace('            property var contentItem: window.contentItem\n', '')
    fixture = fixture.replace('            property bool overviewOpen: false\n', '')
    bar_properties = '''
            property var contentItem: window.contentItem
            property alias appearanceCard: carousel
            property Item stripItem: strip
            property bool overviewOpen: false
            Bar.BarAppearanceCard { id: carousel; barHost: bar; picker: picker }
    '''
    if layout == 'dynamic':
        bar_properties += '''
            property var dropSurfaces: null
            Bar.BarAutoHide { id: autoHide; held: carousel.requested }
            property alias autoHideRef: autoHide
            function closePanels() { calendar.opened = false; calendar.visible = false }
        '''
    else:
        fixture = fixture.replace('autoHide: shell.barAutoHide }', 'autoHide: shell.barAutoHide; held: carousel.requested }')
        bar_properties += '''
            property var dynamicSurfaces: null
            property Item dropSurfaces: drop
            property var dockPanels: []
        '''
    fixture = fixture.replace('            id: bar\n', '            id: bar\n' + bar_properties)
    fixture = fixture.replace('import QtQuick\n', 'import QtQuick\nimport QtTest\n')
    fixture = fixture.replace('    FloatingWindow {', '''
    Bar.AppearancePicker { id: picker; docked: true }
    FloatingWindow {''', 1)
    fixture = fixture.replace('implicitWidth: shell.verticalBar ? 240 : 1920', f'implicitWidth: {width}')
    fixture = fixture.replace('implicitHeight: shell.verticalBar ? 1920 : 240', 'implicitHeight: 800')
    fixture = fixture.replace('implicitHeight: shell.verticalBar ? 1080 : 240', 'implicitHeight: 800')
    fixture = fixture.replace('property bool barAutoHide: false', 'property bool barAutoHide: true')
    fixture += '''
            TestCase { id: keyboard; name: "DockedCarousel"; when: false }
            Timer {
                interval: 400; running: true
                onTriggered: {
                    picker.mode = MODE;
                    picker.items = CATALOG;
                    picker.allItems = picker.items;
                    picker.selectedIndex = 1;
                    picker.contextReady = true;
                    picker.targetScreen = bar.screen;
                    BEFORE_OPEN
                    picker.opened = true;
                    captureTimer.start();
                }
            }
            Timer {
                id: captureTimer; interval: 850
                onTriggered: {
                    const island = carousel.island;
                    if (island.panel !== carousel || picker.dockedContent !== carousel.content || carousel.content.opacity < 0.99)
                        { console.error("Carousel was not hosted by the clock"); Qt.exit(1); return; }
                    const centre = island.mapToItem(bar, island.width / 2, 0);
                    if (Math.abs(centre.x - bar.width / 2) > 0.5 || island.targetDepth <= island.thickness)
                        { console.error("Carousel did not grow from the screen-centred clock"); Qt.exit(1); return; }
                    bar.grabToImage(result => {
                        result.saveToFile(CAPTURE);
                        keyboard.keyClick(Qt.Key_E);
                        if (picker.searchText !== "e") { console.error("Search lost its focus"); Qt.exit(1); return; }
                        keyboard.keyClick(Qt.Key_Escape);
                        if (picker.searchText || !picker.opened) { console.error("Escape did not clear search"); Qt.exit(1); return; }
                        keyboard.keyClick(Qt.Key_Escape);
                        if (picker.opened) { console.error("Escape did not close the carousel"); Qt.exit(1); return; }
                        closeTimer.start();
                    });
                }
            }
            Timer {
                id: closeTimer; interval: 700
                onTriggered: {
                    if (picker.dockedContent || carousel.island.panel || carousel.island.depth > carousel.island.thickness + 0.1)
                        { console.error("Carousel did not retract"); Qt.exit(1); return; }
                    if (CHECK_HIDDEN) { console.error("Auto-hidden Drop did not retract"); Qt.exit(1); return; }
                    picker.opened = true;
                    outsideTimer.start();
                }
            }
            Timer {
                id: outsideTimer; interval: 850
                onTriggered: {
                    keyboard.mouseClick(bar, 10, shell.barEdge === "top" ? window.height - 12 : 12);
                    if (picker.opened) { console.error("Outside click did not close the carousel"); Qt.exit(1); return; }
                    picker.opened = true;
                    applyTimer.start();
                }
            }
            Timer {
                id: applyTimer; interval: 850
                onTriggered: {
                    keyboard.keyClick(Qt.Key_Return);
                    if (picker.opened) { console.error("Enter did not apply and close"); Qt.exit(1); return; }
                    console.log("DOCKED_APPEARANCE_OK");
                    Qt.quit();
                }
            }
        }
    }
}
'''
    replacements = {
        'GEOMETRY': geometry, 'RESERVED': reserved, 'EDGE': '"top"' if layout == 'dynamic' else '"bottom"',
        'LIGHT': 'false', 'WEBSITE': 'false', 'ATTACHED': 'false', 'MODE': json.dumps(mode),
        'CATALOG': json.dumps(catalog), 'CAPTURE': json.dumps(str(capture)),
        'BEFORE_OPEN': ('calendar.visible = true; calendar.opened = true; dynamic.middleIsland.hoverExpanded = true;'
                        if layout == 'dynamic' else ''),
        'CHECK_HIDDEN': 'false' if layout == 'dynamic' else 'drop.pillSurface.visible',
    }
    for token, replacement in replacements.items():
        fixture = fixture.replace(token, replacement)
    return fixture


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class DockedAppearanceTests(unittest.TestCase):
    def test_shared_carousel_opens_and_closes_in_dynamic_and_drop(self):
        with tempfile.TemporaryDirectory(prefix='eitr-docked-look-') as directory:
            folder = Path(directory)
            copy_runtime(folder)
            offscreen_picker(folder)
            source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
            geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
            geometry = ('width: host.verticalBar ? bar.thinThickness' + geometry).replace('host.', 'shell.')
            reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
            themes = BAR.parents[1] / 'themes'
            samples = {
                'theme': [('Afterglow', themes / 'afterglow/preview.png'),
                          ('Eitr', themes / 'eitr/preview.png'), ('Eitr Light', themes / 'eitr-light/preview.png')],
                'wallpaper': [('Aurora Fjord', themes / 'eitr/backgrounds/01-aurora-fjord.jpg'),
                              ('Dusk Fjord', themes / 'eitr/backgrounds/02-dusk-fjord.jpg'),
                              ('Rune Seal', themes / 'eitr/backgrounds/03-rune-seal.jpg')],
            }
            for layout in ('dynamic', 'drop'):
                for mode, entries in samples.items():
                    with self.subTest(layout=layout, mode=mode):
                        catalog = [{'name': name, 'theme': 'Eitr', 'image': path.as_uri(), 'value': str(path)} for name, path in entries]
                        capture = capture_path('DOCKED_APPEARANCE', directory, f'carousel-{layout}-{mode}.png')
                        fixture = folder / 'fixture.qml'
                        width = 640 if layout == 'dynamic' and mode == 'wallpaper' else 1280
                        fixture.write_text(docked_fixture(layout, mode, geometry, reserved, catalog, capture, width))
                        code, output = render(fixture, render_environment(directory, (width, 800)), 12)
                        self.assertEqual(code, 0, output)
                        self.assertIn('DOCKED_APPEARANCE_OK', output)
                        for error in ('TypeError', 'ReferenceError', 'Binding loop', 'Unable to assign'):
                            self.assertNotIn(error, output)
                        self.assertTrue(capture.is_file())
