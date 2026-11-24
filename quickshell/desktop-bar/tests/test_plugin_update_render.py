"""Offscreen regression for relative QML types cached by URL across live updates."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

from layout_render import BAR, capture_path, copy_runtime, render, render_environment

sys.path.insert(0, str(BAR.parents[1] / 'distro/lib'))
from eitr_plugin_runtime import stage_ui


class PluginUpdateRenderTests(unittest.TestCase):
    def test_open_panel_loads_changed_relative_type_after_registry_refresh(self):
        with tempfile.TemporaryDirectory(prefix='eitr-plugin-update-render-') as directory:
            folder = Path(directory)
            copy_runtime(folder / 'quickshell/desktop-bar')
            approval = folder / 'eitr/plugins.json'
            approval.parent.mkdir()
            helper = folder / 'walker/scripts/actions/install/plugins.py'
            helper.parent.mkdir(parents=True)
            helper.write_text("""import os
from pathlib import Path
print((Path(os.environ['XDG_STATE_HOME']) / 'eitr/plugins.json').read_text())
""")
            cache = folder / 'eitr/plugin-ui/fixture'
            snapshots = []
            for version, label in enumerate(('First revision', 'Updated relative type'), start=1):
                root = folder / f'checkout-{version}'
                root.mkdir()
                top = root / 'Plugin.qml'
                top.write_text('import QtQuick\nItem { required property var api; implicitHeight: 80; Detail {} }')
                detail = root / 'Detail.qml'
                detail.write_text(f'import QtQuick\nText {{ x: 20; y: 20; color: "white"; text: "{label}"; font.pixelSize: 22 }}')
                commit = str(version) * 40
                staged = stage_ui(cache, commit, root, [top, detail])
                entry = dict(plugin='fixture', pluginName='Fixture', id='panel', kind='panels',
                             title='Fixture', qml=top.name, source=(staged / top.name).as_uri(),
                             commit=commit, disabled=False)
                snapshots.append(json.dumps(dict(entries=[entry], installed=[], placements={})))
            snapshots.append(json.dumps(dict(entries=[], installed=[], placements={})))
            approval.write_text(snapshots[0])
            capture = capture_path('PLUGIN_UPDATE', directory, 'plugin-update.png')
            fixture = folder / 'shell.qml'
            fixture.write_text(r'''import QtQuick
import Quickshell
import Quickshell.Io
import "quickshell/desktop-bar" as Bar

ShellRoot {
    FloatingWindow {
        id: window
        visible: true
        implicitWidth: 320; implicitHeight: 100
        color: "#18212b"
        property int phase: 0
        property var snapshots: SNAPSHOTS
        Bar.PluginComponent {
            id: host
            anchors.fill: parent
            foreground: "white"; background: "#18212b"; accent: "gold"
            entry: Bar.PluginRegistry.entries[0] || ({disabled: true})
        }
        Bar.PluginPanel {
            id: popup
            target: host
            foreground: "white"; background: "#18212b"; accent: "gold"
        }
        Process { id: save }
        function showNext() {
            phase++;
            save.command = ["python3", "-c",
                "from pathlib import Path; import sys; target = Path(sys.argv[1]); temp = target.with_suffix('.tmp'); temp.write_text(sys.argv[2]); temp.replace(target)",
                APPROVAL, snapshots[phase]];
            save.running = true;
        }
        function shows(item, label) {
            if (item.text === label) return true;
            return item.children.some(child => shows(child, label));
        }
        Timer {
            interval: 25; running: true; repeat: true
            onTriggered: {
                if (window.phase === 0 && window.shows(host, "First revision")) {
                    popup.history = [{plugin: "fixture", id: "panel"}];
                    window.showNext();
                } else if (window.phase === 1 && window.shows(host, "Updated relative type")) {
                    if (!popup.back() || popup.entry.commit !== host.entry.commit) { Qt.exit(1); return; }
                    stop();
                    host.grabToImage(result => {
                        if (!result.saveToFile(CAPTURE)) { Qt.exit(1); return; }
                        window.showNext();
                        start();
                    });
                } else if (window.phase === 2 && Bar.PluginRegistry.entries.length === 0
                       && !window.shows(host, "Updated relative type")) {
                    console.log("PLUGIN_UPDATE_OK");
                    Qt.quit();
                }
            }
        }
    }
}'''.replace('SNAPSHOTS', json.dumps(snapshots)).replace('APPROVAL', json.dumps(str(approval)))
                .replace('CAPTURE', json.dumps(str(capture))))
            environment = render_environment(directory)
            environment['EITR_CODE_ROOT'] = directory
            code, output = render(fixture, environment, 12)
            self.assertEqual(code, 0, output)
            self.assertIn('PLUGIN_UPDATE_OK', output)
            self.assertNotIn('ReferenceError', output)
            self.assertNotIn('TypeError', output)
