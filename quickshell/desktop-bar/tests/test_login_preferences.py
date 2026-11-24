"""Saved bar preferences load in an isolated offscreen shell, before presentation."""
import json
from pathlib import Path
import re
import tempfile
import unittest
from layout_render import BAR, render, render_environment, capture_path


class LoginPreferencesTests(unittest.TestCase):
    def test_saved_layout_and_defaults(self):
        for saved in ({'layout': 'dynamic', 'edge': 'left', 'clock': '24h'},
                      {'layout': 'split'}, {'layout': 'invalid'}):
            with tempfile.TemporaryDirectory() as directory:
                folder = Path(directory)
                (folder / 'settings.json').write_text(json.dumps(saved))
                for name in ('login-settings.json', 'ChoiceLists.js', 'JsonState.js'):
                    (folder / name).write_text((BAR / name).read_text())
                source = (BAR / 'services/BarPreferences.qml').read_text().replace('import ".."\n', '').replace('import Eitr as Eitr\n', '')
                source = source.replace('"../ChoiceLists.js"', '"ChoiceLists.js"').replace('"../JsonState.js"', '"JsonState.js"')
                source = re.sub(r'Eitr.Paths.config\("[^"\n]+"\)', json.dumps(str(folder / 'settings.json')), source)
                source = source.replace('        running: true', '        running: false')
                source = source.replace('    IpcHandler {\n        target: "bar"',
                                        '    readonly property alias barIpc: barIpc\n'
                                        '    IpcHandler {\n        id: barIpc; target: "bar"')
                (folder / 'BarPreferences.qml').write_text(source)
                (folder / 'PreferenceWatch.qml').write_text('import QtQuick\nQtObject { property string path; property string ancestor; signal changed() }')
                (folder / 'DesktopStyle.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property bool reduceMotion: false; property int workspaceCount: 10; property color criticalColor: "red" }')
                (folder / 'PluginRegistry.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property string clockFormat: "12h"; property var palette: ({}) }')
                (folder / 'qmldir').write_text('singleton DesktopStyle DesktopStyle.qml\nsingleton PluginRegistry PluginRegistry.qml\nBarPreferences BarPreferences.qml\nPreferenceWatch PreferenceWatch.qml\n')
                with (folder / 'qmldir').open('a') as registry:
                    registry.write('singleton FocusMode FocusMode.qml\n')
                (folder / 'FocusMode.qml').write_text('pragma Singleton\nimport QtQuick\nQtObject { property bool enabled: false }')
                fields = set(re.findall(r'host\.([A-Za-z]+)', source))
                booleans = {'settingsDirty', 'barPinned', 'barLyrics', 'barMoments', 'barAutoHide', 'barDock', 'barDockPreviews', 'barVisible', 'idleLockEnabled'}
                booleans.update({'verticalBar', 'centeredLayout', 'notchLayout', 'dynamicLayout',
                                 'dropLayout', 'islandsLayout', 'statusOpen', 'iconsOpen'})
                integers = {'workspaceCount'}
                properties = '\n'.join('property ' + ('bool' if field in booleans else 'int' if field in integers else 'string') + ' ' + field + ': ' + ('false' if field in booleans else '5' if field in integers else '""') for field in sorted(fields))
                expected = {'dynamic': 'dynamic', 'split': 'centered'}.get(saved['layout'], 'unified')
                capture = capture_path('LOGIN', folder, saved['layout'] + '.png')
                (folder / 'fixture.qml').write_text('''import QtQuick
import Quickshell
ShellRoot {
 QtObject { id: barHost; PROPERTIES }
 BarPreferences {
  id: preferences
  host: barHost
  barWindows: bars
 }
 Variants {
  id: bars
  model: ["fixture"]
  delegate: Component {
   QtObject {
    required property string modelData
    readonly property var screen: ({name: modelData})
    readonly property var rightSide: ({rightZone: {items: [{id: "wifi"}, {id: "notifications"}], hasHideable: true}})
    readonly property var statusToggle: ({visible: true, width: 24})
   }
  }
 }
 FloatingWindow { id: window; visible: true; implicitWidth: 420; implicitHeight: 90
  color: "#181824"
  Item { id: canvas; anchors.fill: parent
  Text { anchors.centerIn: parent; color: "#cdd6f4"; text: barHost.barLayout + " / " + barHost.barEdge; font.pixelSize: 20 }
  Timer { interval: 150; running: true; onTriggered: {
   if (barHost.barLayout !== EXPECTED) { console.error("saved layout missing: " + barHost.barLayout); Qt.exit(1); return; }
   try {
    const status = JSON.parse(preferences.barIpc.status());
    const screen = status.bars[0];
    if (status.layout !== EXPECTED || status.focus || typeof status.notchLayout !== "boolean" ||
        screen.screen !== "fixture" || !screen.hasHideable || !screen.toggleVisible ||
        screen.toggleWidth !== 24 || screen.rightItemIds.join(",") !== "wifi,notifications")
     throw new Error("Unexpected bar status output: " + JSON.stringify(status));
    canvas.grabToImage(function(capture) { capture.saveToFile(CAPTURE); Qt.quit(); });
   } catch (error) {
    console.error(error);
    Qt.exit(1);
   }
  } }
  }
 }
}'''.replace('PROPERTIES', properties).replace('EXPECTED', json.dumps(expected)).replace('CAPTURE', json.dumps(str(capture))))
                code, output = render(folder / 'fixture.qml', render_environment(folder), 15)
                self.assertEqual(code, 0, output)
                for problem in ('ReferenceError', 'TypeError', 'Error:'):
                    self.assertNotIn(problem, output)
                self.assertTrue(capture.exists(), output)


if __name__ == '__main__':
    unittest.main()
