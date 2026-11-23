"""Render the existing carouselHost.item inside the real Drop pill."""
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


def docked_fixture(edge, mode, geometry, reserved, catalog, capture, width):
    fixture = layout_fixture('drop').split('            Bar.DockPanel {', 1)[0]
    fixture = fixture.replace('            property Item stripItem: strip\n', '')
    fixture = fixture.replace('            property var appearanceCard: null\n', '')
    fixture = fixture.replace('            property var contentItem: window.contentItem\n', '')
    fixture = fixture.replace('            property bool overviewOpen: false\n', '')
    # The bar item fills the test window, so photographing it includes the card on it.
    bar_properties = '''
            property var contentItem: bar
            property alias appearanceCard: carouselHost.item
            property Item stripItem: strip
            property Item dropSurfaces: drop
            property bool overviewOpen: false
            // Loaded like BarWindow does: an unsized Loader, so the card keeps its own size.
            Loader {
                id: carouselHost
                sourceComponent: Bar.BarAppearanceCard { barHost: bar; picker: bar.appearancePicker }
            }
            readonly property var appearancePicker: picker
    '''
    fixture = fixture.replace('autoHide: shell.barAutoHide }',
                              'autoHide: shell.barAutoHide; held: carouselHost.item.requested || drop.clockCardOpen }')
    bar_properties += '            property var dockPanels: []\n'
    fixture = fixture.replace('            id: bar\n', '            id: bar\n' + bar_properties)
    fixture = fixture.replace('import QtQuick\n', 'import QtQuick\nimport QtTest\n')
    fixture = fixture.replace('    FloatingWindow {', '''
    Bar.AppearancePicker { id: picker; docked: true }
    FloatingWindow {''', 1)
    fixture = fixture.replace('implicitWidth: shell.verticalBar ? 240 : 1920', f'implicitWidth: {width}')
    fixture = fixture.replace('implicitHeight: shell.verticalBar ? 1080 : 240', 'implicitHeight: 800')
    fixture = fixture.replace('property bool barAutoHide: false', 'property bool barAutoHide: true')
    fixture += '''
            TestCase { id: keyboard; name: "DockedCarousel"; when: false }
            Timer {
                interval: 400; running: true
                onTriggered: {
                    picker.mode = MODE;
                    // All themes adds each wallpaper's theme to its name.
                    if (MODE === "wallpaper") picker.wallpaperScope = "all";
                    picker.items = CATALOG;
                    picker.allItems = picker.items;
                    picker.selectedIndex = 1;
                    picker.contextReady = true;
                    picker.targetScreen = bar.screen;
                    picker.opened = true;
                    captureTimer.start();
                }
            }
            Timer {
                id: captureTimer; interval: 850
                onTriggered: {
                    const island = carouselHost.item.island;
                    if (island.panel !== carouselHost.item || picker.dockedContent !== carouselHost.item.content || carouselHost.item.content.opacity < 0.99)
                        { console.error("Carousel was not hosted by the clock"); Qt.exit(1); return; }
                    const centre = island.mapToItem(bar, island.width / 2, 0);
                    if (Math.abs(centre.x - bar.width / 2) > 0.5 || island.targetDepth <= island.thickness)
                        { console.error("Carousel did not grow from the screen-centred clock"); Qt.exit(1); return; }
                    const content = carouselHost.item.content.children.find(child => child.item && child.item.previewWidth > 0).item;
                    const part = name => content.children.find(child => child.objectName === name);
                    const heading = part("appearanceHeading");
                    const filters = part("appearanceFilters");
                    const preview = part("appearanceSelectedPreview");
                    const caption = part("appearanceSelectedName");
                    if (carouselHost.item.width > Math.min(640, bar.width - 2 * bar.edgeGap) || carouselHost.item.height > 260
                        || heading.x + heading.width > filters.x || filters.x + filters.width > carouselHost.item.width
                        || heading.y + heading.height > preview.y || filters.y + filters.height > preview.y
                        || preview.y + preview.height > caption.y || caption.y + caption.height > carouselHost.item.height
                        || Math.abs(preview.width - 280) > 1 || Math.abs(preview.x + preview.width / 2 - carouselHost.item.width / 2) > 0.5)
                        { console.error("Compact layout does not fit", carouselHost.item.width, carouselHost.item.height, preview.width); Qt.exit(1); return; }
                    const overflowing = content.children.filter(child => child.visible && child.text !== undefined
                        && child.y + child.height > carouselHost.item.height);
                    if (overflowing.length || (MODE === "wallpaper" && caption.text.indexOf("Eitr") < 0))
                        { console.error("Text outside the strip", overflowing.map(child => child.text)); Qt.exit(1); return; }
                    bar.grabToImage(result => {
                        result.saveToFile(CAPTURE);
                        keyboard.keyClick(Qt.Key_E);
                        if (picker.searchText !== "e" || heading.text !== "e") { console.error("Search lost its focus"); Qt.exit(1); return; }
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
                    if (picker.dockedContent || carouselHost.item.island.panel || carouselHost.item.island.depth > carouselHost.item.island.thickness + 0.1)
                        { console.error("Carousel did not retract"); Qt.exit(1); return; }
                    if (drop.pillSurface.visible) { console.error("Auto-hidden Drop did not retract"); Qt.exit(1); return; }
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
        'GEOMETRY': geometry, 'RESERVED': reserved, 'EDGE': json.dumps(edge),
        'LIGHT': 'false', 'MODE': json.dumps(mode), 'CATALOG': json.dumps(catalog),
        'CAPTURE': json.dumps(str(capture)),
    }
    for token, replacement in replacements.items():
        fixture = fixture.replace(token, replacement)
    return fixture


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required')
class DockedAppearanceTests(unittest.TestCase):
    def test_bar_window_loader_leaves_the_card_its_own_size(self):
        # A sized Loader stretches what it loads: the card then covered the whole screen.
        source = (BAR / 'bar/BarWindow.qml').read_text(encoding='utf-8')
        start = source.index('id: appearanceHost')
        block = source[start:source.index('sourceComponent', start)]
        for sizing in ('anchors.', 'width:', 'height:'):
            self.assertNotIn(sizing, block)

    def test_shared_carousel_fits_drop_on_both_edges(self):
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
            for width in (900, 1280, 1920):
                for edge, mode in (('top', 'theme'), ('bottom', 'wallpaper'),
                                   ('bottom', 'theme'), ('top', 'wallpaper')):
                    with self.subTest(edge=edge, mode=mode, width=width):
                        catalog = [{'name': name, 'theme': 'Eitr', 'image': path.as_uri(), 'value': str(path)}
                                   for name, path in samples[mode]]
                        capture = capture_path('DOCKED_APPEARANCE', directory, f'carousel-{edge}-{mode}-{width}.png')
                        fixture = folder / 'fixture.qml'
                        fixture.write_text(docked_fixture(edge, mode, geometry, reserved, catalog, capture, width))
                        code, output = render(fixture, render_environment(directory, (width, 800)), 12)
                        self.assertEqual(code, 0, output)
                        self.assertIn('DOCKED_APPEARANCE_OK', output)
                        for error in ('TypeError', 'ReferenceError', 'Binding loop', 'Unable to assign'):
                            self.assertNotIn(error, output)
                        self.assertTrue(capture.is_file())
