"""Drop rails and in-place plugin panels on an inert, production island surface."""
import json
from pathlib import Path
import tempfile
import unittest

from bar_frame_source import eager_projection
from layout_render import BAR, capture_path, copy_runtime, layout_fixture, render, render_environment


class DropRailRenderTests(unittest.TestCase):
    def test_navigation_plugins_regions_and_surfaces(self):
        cases = [('top-dark', 'top', False, False, True), ('top-light', 'top', True, False, True),
                 ('left-dark', 'left', False, False, True), ('no-plugins', 'top', False, False, False),
                 ('bottom-attached', 'bottom', False, True, True), ('right-attached', 'right', True, True, True),
                 ('website', 'top', False, False, True), ('compact', 'top', False, False, True)]
        with tempfile.TemporaryDirectory(prefix='eitr-drop-rails-') as directory:
            folder = Path(directory)
            self.runtime(folder)
            for name, edge, light, attached, plugins in cases:
                fixture = self.fixture()
                replacements = {'EDGE': json.dumps(edge), 'LIGHT': str(light).lower(),
                                'ATTACHED': str(attached).lower(), 'PLUGINS': str(plugins).lower(),
                                'CAPTURE': json.dumps(str(capture_path('DROP_RAILS', directory, 'drop-rails-' + name))),
                                'PLUGIN_SOURCE': json.dumps((folder / 'Sample.qml').as_uri()),
                                'PANEL_SOURCE': json.dumps((folder / 'SamplePanel.qml').as_uri())}
                for token, value in replacements.items():
                    fixture = fixture.replace(token, value)
                if name == 'website':
                    fixture = fixture.replace('"#e9eef1"', '"#d7bc83"').replace('"#18212b"', '"#161819"')
                if name == 'compact':
                    fixture = fixture.replace('1920', '640').replace('1080', '480')
                (folder / 'fixture.qml').write_text(fixture)
                environment = render_environment(directory, (1920, 1080))
                environment['EITR_CODE_ROOT'] = str(folder)
                code, output = render(folder / 'fixture.qml', environment, 15)
                with self.subTest(case=name):
                    self.assertEqual(code, 0, output)
                    self.assertIn('DROP_RAILS_OK', output)
                    self.assertTrue(capture_path('DROP_RAILS', directory, 'drop-rails-' + name + '.png').is_file())
                    if plugins:
                        self.assertTrue(capture_path('DROP_RAILS', directory, 'drop-rails-' + name + '-plugin.png').is_file())
                    for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Cannot anchor', 'Unable to assign', 'Error:'):
                        self.assertNotIn(error, output)

    def test_stagger_close_reduce_motion_and_scrolled_regions(self):
        with tempfile.TemporaryDirectory(prefix='eitr-rail-motion-') as directory:
            folder = Path(directory)
            self.runtime(folder)
            fixture = """import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 FloatingWindow {
  id: window; visible: true; implicitWidth: 240; implicitHeight: 480
  Bar.DropRail {
   id: rail; x: 40; y: 40; width:32; height:200
   entries: Array.from({length:8}, (unused, index) => ({id:"page-" + index,title:"Page",glyph:"󰃭"}))
   foreground:"white"; background:"#18212b"; accent:"#70ba9a"
  }
  Timer {
   id: steps; interval:80; running:true; repeat:true
   property int phase:0
   onTriggered: {
    try {
     const surfaces = rail.inputSurfaces;
     if (phase === 0) { Bar.DesktopStyle.reduceMotion = false; rail.opened = true; }
     else if (phase === 1) {
      if (surfaces.some(item => item.visible)) throw new Error("Rails appeared before card settled");
      rail.ready = true; interval = 100;
     } else if (phase === 2) {
      if (!surfaces[0].visible || surfaces[7].visible) throw new Error("Pills did not stagger");
      interval = 220;
     } else if (phase === 3) {
      if (!surfaces[0].visible || surfaces[7].visible) throw new Error("Long rail was not clipped");
      rail.current = "page-7";
     } else if (phase === 4) {
      if (surfaces[0].visible || !surfaces[7].visible) throw new Error("Selection did not scroll into view");
      for (const item of surfaces) if (item.visible && (item.x < 0 || item.y < 0 || item.x + item.width > rail.width || item.y + item.height > rail.height)) throw new Error("Input escaped rail viewport");
      rail.opened = false;
     } else if (phase === 5) {
      if (surfaces.some(item => item.visible)) throw new Error("Closing left input regions");
      Bar.DesktopStyle.reduceMotion = true; rail.opened = true;
      if (!surfaces[7].visible) throw new Error("Reduce motion did not open instantly");
      rail.opened = false;
      if (surfaces.some(item => item.visible)) throw new Error("Reduce motion did not close instantly");
      console.log("RAIL_MOTION_OK"); Qt.quit(); stop();
     }
     phase++;
    } catch (error) { console.error(error); Qt.exit(1); }
   }
  }
 }
}"""
            (folder / 'fixture.qml').write_text(fixture)
            environment = render_environment(directory)
            environment['EITR_CODE_ROOT'] = str(folder)
            code, output = render(folder / 'fixture.qml', environment, 8)
            self.assertEqual(code, 0, output)
            self.assertIn('RAIL_MOTION_OK', output)
            for error in ('ReferenceError', 'TypeError', 'Binding loop', 'Unable to assign'):
                self.assertNotIn(error, output)

    def test_bar_mask_uses_individual_rail_regions(self):
        mask = (BAR / 'bar/BarInputMask.qml').read_text()
        self.assertIn('IslandMask { surfaces: barHost.dropDashboard ? barHost.dropDashboard.railSurfaces : [] }', mask)

    @staticmethod
    def fixture():
        source = eager_projection((BAR / 'bar/BarWindow.qml').read_text())
        geometry = source.split('        width: host.verticalBar ? bar.thinThickness', 1)[1].split('        BarTabs {', 1)[0]
        geometry = ('width: host.verticalBar ? bar.thinThickness' + geometry).replace('host.', 'shell.')
        reserved = source.split('readonly property real reservedThickness: ', 1)[1].split('\n', 1)[0]
        fixture = layout_fixture('drop').split('            Bar.DockPanel {', 1)[0]
        fixture = fixture.replace('GEOMETRY', geometry).replace('RESERVED', reserved)
        fixture = fixture.replace('import QtQuick\n', 'import QtQuick\nimport QtTest\n', 1)
        fixture = fixture.replace('implicitWidth: shell.verticalBar ? 240 : 1920', 'implicitWidth: 1920')
        fixture = fixture.replace('implicitHeight: shell.verticalBar ? 1080 : 240', 'implicitHeight: 1080')
        start = fixture.index('            property QtObject dropDashboard:')
        end = fixture.index('            property var notificationsRef:', start)
        fixture = fixture[:start] + '''            property alias dropDashboard: dashboard
            property var host: shell
            property var calendarMenu: ({reminders: [], events: []})
''' + fixture[end:]
        fixture = fixture.replace('            property var calendarMenu: null\n', '')
        fixture = fixture.replace('property real edgeGap: islandGap', 'property bool attachedIslands: ATTACHED\n        property real islandSpacing: 20\n        property real edgeGap: attachedIslands ? 0 : islandGap')
        fixture += layout_fixture('drop_rails')
        return fixture

    @staticmethod
    def runtime(folder):
        copy_runtime(folder)
        registry = folder / 'plugins/PluginRegistry.qml'
        registry.write_text(registry.read_text().replace('Component.onCompleted: { refresh(); startDiagnostics(); }', '')
                            .replace('readonly property bool weatherEnabled: entries.some(entry => entry.plugin === "weather" && !entry.disabled && (entry.capabilities || []).includes("weather"))',
                                     'readonly property bool weatherEnabled: true'))
        (folder / 'services/DesktopData.qml').write_text('''pragma Singleton
import QtQuick
QtObject {
 property var client: ({setCapturePresence:function(present) {}})
 property var captureDomain: ({busy:false})
 function setCapturePresence(present) {}
 property var topics: ({"weather.default":{data:{temp:"21°C", text:"󰖐 21°C"}}})
 function observe(topic, owner, interval) { return ""; }
 function release(token) {}
 function releaseOwner(owner) {}
 function queryCatalog(name, args, owner, callback) { callback("", {}); }
 function cancelQuery(token) {}
}
''')
        # Unrelated pages stay inert; the dashboard, home, rails, loaders and island are real.
        pages = {'media/MediaPage.qml': 'property var player; property var host; property bool active',
                 'drop/DropObsPage.qml': 'property var obs; property bool active',
                 'panels/ControlCenter.qml': 'property var inlineParent; property var target; property var barRef; property var service; property var wifiControl; property var bluetoothControl; property var displayControl; property string wifiGlyph; property var battery; property var mediaPlayer; property bool idleEnabled; property bool idleBusy; property bool opened; signal idleToggleRequested(); signal lockRequested(); signal panelRequested(string kind); signal settingsRequested(string page); signal closeRequested(); function runAfterClose(command) {}',
                 'controls/FocusTimerControls.qml': '',
                 'panels/SystemMonitorMenu.qml': 'property var inlineParent; property var target; property int maximumHeight; property bool opened',
                 'panels/AiUsageMenu.qml': 'property var inlineParent; property var target; property int maximumHeight; property bool opened',
                 'notifications/NotificationList.qml': 'property var service; property real contentHeight: 150; signal activated()'}
        for relative, properties in pages.items():
            path = folder / relative
            if not path.exists():
                path = next(folder.rglob(Path(relative).name))
            path.write_text('import QtQuick\nItem { implicitHeight: 262; property color foreground; '
                            'property color background; property color accent; ' + properties + '\n}')
        (folder / 'Sample.qml').write_text('''import QtQuick
Item {
 required property var api
 implicitWidth: 24; implicitHeight: 24
 Component.onCompleted: api.detail = "Ready"
 Text { anchors.centerIn:parent; text:api.icon; color:api.foreground; font.family:api.fontFamily; font.pixelSize:18 }
}
''')
        (folder / 'SamplePanel.qml').write_text('''import QtQuick
Item {
 objectName: "samplePluginPanel"
 required property var api
 implicitHeight: 260
 property bool observed: api.observed
 Text { anchors.centerIn: parent; text:"Aurora · Plugin panel"; color:api.foreground; font.family:api.fontFamily; font.pixelSize:18 }
}
''')


if __name__ == '__main__':
    unittest.main()
