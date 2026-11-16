"""Shared moments on real clock slots and layout surfaces, with inert services."""
import json
from pathlib import Path
import tempfile
import unittest

from bar_frame_source import eager_projection
from layout_render import BAR, copy_runtime, render, render_environment, capture_path, layout_fixture


def prepare(folder):
    copy_runtime(folder)
    # Keep the production clock, media strip, plugin geometry and layout surfaces.
    # Device panels have no role in this fixture and never contact live services.
    stub = layout_fixture('stub')
    (folder / 'Stub.qml').write_text(stub)
    for name in ('CalendarMenu', 'WeatherMenu', 'CaptureIndicator', 'StatusIcon', 'VerticalBarIcon', 'MediaIndicator'):
        source = next(BAR.rglob(name + '.qml')).relative_to(BAR)
        (folder / source).write_text(stub + ('\n' if name != 'MediaIndicator' else ''))
    indicator = folder / 'media/MediaIndicator.qml'
    indicator.write_text(stub.replace('    property bool hovered:', '    signal draggedLeft()\n    property bool hasAudioFrame: false\n    property var levels: []\n    property bool hovered:').replace('width: open ?', 'width: open ?'))
    (folder / 'services/PluginRegistry.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
    property bool weatherEnabled: true
    function slotItems(slot) { return slot === "clock" ? [{title:"LIS 14:05", slot:slot}] : slot === "clockEnd" ? [{title:"󰖙 24°", slot:slot}] : []; }
}''')
    # Registry's production location follows its qmldir entry.
    registry = (BAR / 'qmldir').read_text().split('singleton PluginRegistry 1.0 ')[1].splitlines()[0]
    (folder / registry).write_text((folder / 'services/PluginRegistry.qml').read_text())
    (folder / 'plugins/PluginComponent.qml').write_text('''import QtQuick
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
    implicitWidth: entry.slot === "clockEnd" ? 65 : 85
    signal panelRequested(string plugin, string panel)
    Text { anchors.centerIn: parent; rotation: parent.verticalContent ? 90 : 0; text: parent.entry.title; color: parent.foreground; font.pixelSize:12 }
}''')
    (folder / 'qmldir').write_text((folder / 'qmldir').read_text() + 'Stub Stub.qml\n')
    # MPRIS player is supplied in memory. No player or level commands run.
    path = folder / 'media/MediaStrip.qml'
    path.write_text(path.read_text().replace('property var players: Mpris.players.values', '''property var players: [{trackTitle:"Northern Lights", trackArtist:"Eitr Ensemble", identity:"Fixture", isPlaying:true,
        canControl:true, canTogglePlaying:true, canPlay:true, canPause:true, canGoNext:true, canGoPrevious:true}]'''))
    source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
    geometry = 'width: host.verticalBar ? bar.thinThickness' + source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
    center = source.split('readonly property real centerExtent: ', 1)[1].split('\n    Timer {', 1)[0]
    moment = source.split('property real momentExtent: ', 1)[1].split('\n    Behavior on momentExtent', 1)[0]
    fixture = layout_fixture('bar_moments').replace('GEOMETRY', geometry).replace('CENTER_EXTENT', center).replace('MOMENT_EXTENT', moment)
    return fixture.replace('host.', 'shell.')


class BarMomentRenderTests(unittest.TestCase):
    def test_layouts_themes_hover_and_stable_neighbours(self):
        with tempfile.TemporaryDirectory(prefix='eitr-all-moments-') as directory:
            folder = Path(directory)
            base = prepare(folder)
            for layout, edge in [('full', 'top'), ('tabs', 'top'), ('centered', 'top'),
                                 ('islands', 'top'), ('drop', 'top'), ('full', 'left')]:
                for light in (False, True):
                    theme = 'light' if light else 'dark'
                    capture = capture_path('BAR_MOMENT', folder, '')
                    fixture = base
                    for token, value in {'LAYOUT': json.dumps(layout), 'EDGE': json.dumps(edge), 'LIGHT': str(light).lower(),
                                         'CAPTURE': json.dumps(str(capture)), 'THEME': json.dumps(theme),
                                         'SUFFIX': json.dumps('' if edge == 'top' else '-' + edge)}.items():
                        fixture = fixture.replace(token, value)
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    code, output = render(path, render_environment(folder), 12)
                    with self.subTest(layout=layout, edge=edge, light=light):
                        self.assertEqual(code, 0, output)
                        self.assertIn('BAR_MOMENTS_OK', output)
                        for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                            self.assertNotIn(error, output)
                        self.assertTrue((capture / f'moment-{layout}-volume-{theme}{"" if edge == "top" else "-left"}.png').is_file())
