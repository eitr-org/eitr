"""Render the actual plugin host with trusted example and failed components."""
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
class VisualPluginLayoutTests(unittest.TestCase):
    def test_example_and_load_failure_in_both_themes(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            for source in BAR.iterdir():
                if source.suffix in ('.qml', '.js') or source.name == 'qmldir':
                    shutil.copy(source, folder / source.name)
            broken = folder / 'Broken.qml'
            broken.write_text('import QtQuick\nItem { invalid syntax }\n')
            entries = []
            for kind, key, title, source in (
                    ('tiles', 'hello', 'Hello', ROOT / 'distro/plugins/example/HelloTile.qml'),
                    ('panels', 'hello-panel', 'Hello status', ROOT / 'distro/plugins/example/HelloPanel.qml'),
                    ('tiles', 'broken', 'Broken example', broken)):
                entries.append(dict(plugin='example', commit='a' * 40, kind=kind, id=key,
                                    title=title, icon='☀' if key == 'hello' else '', qml=source.name, source=source.as_uri(), disabled=False))
            for theme, state in [(theme, state) for theme in ('dark', 'light') for state in ('tiles', 'panel', 'broken', 'disabled')]:
                captures = Path(os.environ.get('EITR_PLUGIN_REVIEW_RENDERS', directory))
                captures.mkdir(parents=True, exist_ok=True)
                capture = captures / ('plugins-' + theme + '-' + state + '.png')
                background, foreground = ('#18212b', '#e9eef1') if theme == 'dark' else ('#f5f0e7', '#252936')
                selected = [dict(entry, panel='hello-panel') if entry['id'] == 'hello' else entry for entry in entries]
                if state == 'disabled':
                    selected = [dict(entry, disabled=True) for entry in selected if entry['id'] != 'broken']
                elif state != 'broken':
                    selected = [entry for entry in selected if entry['id'] != 'broken']
                fixture = folder / 'fixture.qml'
                fixture.write_text('''import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
    FloatingWindow {
        visible: true; implicitWidth: 480; implicitHeight: 400
        Rectangle {
            id: sample; anchors.fill: parent; color: "BACKGROUND"
            Bar.PluginArea {
                id: area; x: 24; y: 24; width: 432
                foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "#7ee0b5"
                queryEnabled: false; entries: ENTRIES
                Component.onCompleted: { OPEN_PANEL }
            }
            Timer {
                interval: 1200; running: true
                onTriggered: {
                    if (!area.visible || area.tiles.length === 0)
                        throw new Error("Plugin area did not populate");
                    if (area.height > sample.height - 48) throw new Error("Plugin area clipped");
                    sample.grabToImage(function(result) {
                        result.saveToFile("CAPTURE");
                        if (area.selectedPanel) {
                            if (!area.back() || area.selectedPanel !== null || area.back())
                                throw new Error("Back did not return to tiles before closing");
                        }
                        const cachedEntries = area.entries;
                        const tilesHeight = area.height;
                        area.active = false;
                        area.active = true;
                        if (area.entries !== cachedEntries || area.height !== tilesHeight)
                            throw new Error("Opening rebuilt cached placements or changed row geometry");
                        console.log("PLUGIN_RENDER_OK"); Qt.quit();
                    });
                }
            }
        }
    }
}'''.replace('BACKGROUND', background).replace('FOREGROUND', foreground)
                    .replace('OPEN_PANEL', 'openPanel("example", "hello-panel")' if state == 'panel' else '').replace('ENTRIES', json.dumps(selected)).replace('CAPTURE', str(capture)))
                environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                   QML_IMPORT_PATH=str(ROOT / 'quickshell'), EITR_CODE_ROOT=str(ROOT),
                                   XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_DATA_HOME=directory,
                                   XDG_CACHE_HOME=directory, XDG_RUNTIME_DIR=directory,
                                   DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', HYPRLAND_INSTANCE_SIGNATURE='')
                result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                        text=True, capture_output=True, timeout=15)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('PLUGIN_RENDER_OK', result.stdout + result.stderr)
                if state == 'broken':
                    self.assertIn('Could not load', result.stdout + result.stderr)
                self.assertNotIn('HelloTile.qml: Cannot', result.stdout + result.stderr)
                self.assertTrue(capture.is_file())
