"""Render the production Focus view with sanitized fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
BAR = ROOT / 'quickshell/desktop-bar'


def render_all(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for light in (False, True):
        for count in (1, 3, 8):
            for split in (False, True):
                if split and count == 1:
                    continue
                with tempfile.TemporaryDirectory(prefix='eitr-focus-render-') as directory:
                    folder = Path(directory)
                    capture = destination / f'{"light" if light else "dark"}-{count}{"-split" if split else ""}.png'
                    titles = ['Terminal', 'Editor — main.py', 'Browser — Documentation', 'Build', 'Tests', 'Logs', 'Notes', 'Files']
                    tabs = [{'address': hex(index+1), 'title': titles[index], 'active': index == 0,
                             'pane': index == 0 or (split and index == 1)} for index in range(count)]
                    fixture = '''import QtQuick
import Quickshell
import "BAR"
ShellRoot {
    Window {
        visible: true; width: 1280; height: 28
        FocusStrip {
            id: sample; anchors.fill: parent
            tabs: TABS
            foreground: FOREGROUND; background: BACKGROUND; accent: ACCENT
            clockText: "14:35"; networkText: "󰤨"; batteryText: "󰁹 82%"
        }
        Timer {
            interval: 300; running: true
            onTriggered: {
                if (sample.height !== 28 || sample.tabWidth < 48 || sample.paneCount !== PANES) Qt.exit(2);
                sample.grabToImage(function(result) {
                    if (!result.saveToFile(CAPTURE)) Qt.exit(3);
                    console.log("FOCUS_RENDER_OK"); Qt.quit();
                });
            }
        }
    }
}
'''
                    fixture = fixture.replace('BAR', BAR.as_uri()).replace('TABS', json.dumps(tabs)).replace('FOREGROUND', json.dumps('#202430' if light else '#eee9df')).replace('BACKGROUND', json.dumps('#eee9df' if light else '#202430')).replace('ACCENT', json.dumps('#486aaa' if light else '#8fb9ee')).replace('CAPTURE', json.dumps(str(capture))).replace('PANES', str(2 if split else 1))
                    path = folder / 'fixture.qml'
                    path.write_text(fixture)
                    environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                                       QML_IMPORT_PATH=str(ROOT / 'quickshell'), HOME=directory,
                                       XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
                                       XDG_RUNTIME_DIR=directory, HYPRLAND_INSTANCE_SIGNATURE='',
                                       DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent')
                    result = subprocess.run(['quickshell', '-p', str(path)], env=environment,
                                            capture_output=True, text=True, timeout=15)
                    output = result.stdout + result.stderr
                    if result.returncode or 'FOCUS_RENDER_OK' not in output or not capture.is_file():
                        raise AssertionError(output)
                    if 'ReferenceError' in output or 'TypeError' in output:
                        raise AssertionError(output)


@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required for offscreen rendering')
class FocusStripTests(unittest.TestCase):
    def test_dark_light_tabs_and_splits(self):
        with tempfile.TemporaryDirectory() as directory:
            render_all(directory)
            self.assertEqual(len(list(Path(directory).glob('*.png'))), 10)




@unittest.skipUnless(shutil.which('quickshell'), 'Quickshell required for offscreen verification')
class FocusControllerTests(unittest.TestCase):
    def test_queued_toggle_and_preference_creation(self):
        with tempfile.TemporaryDirectory(prefix='eitr-focus-controller-') as directory:
            folder = Path(directory)
            (folder / 'scripts').mkdir()
            (folder / 'eitr').mkdir()
            helper = folder / 'scripts/focus-mode.py'
            helper.write_text('''import json,sys,time
from pathlib import Path
folder=Path(__file__).parents[1]
action=sys.argv[1]
with (folder/'actions').open('a') as output: output.write(action+'\\n')
(folder/'eitr/focus.json').write_text(json.dumps({'version':1,'enabled':action=='on'}))
time.sleep(.1)
''')
            fake = folder / 'hyprctl'
            fake.write_text('#!/usr/bin/env python3\nprint("[]")\n')
            fake.chmod(0o755)
            fixture = folder / 'fixture.qml'
            fixture.write_text('''import QtQuick
import Quickshell
import "BAR"
ShellRoot {
    property int ticks: 0
    property bool sawOn: false
    Connections { target: FocusMode; function onEnabledChanged() { if (FocusMode.enabled) sawOn = true; } }
    Timer {
        interval: 25; running: true; repeat: true
        onTriggered: {
            ticks++;
            if (ticks === 2) { FocusMode.select(true); FocusMode.select(false); }
            if (ticks > 20 && !FocusMode.change.running && FocusMode.requested === null) {
                if (!sawOn || FocusMode.enabled || FocusMode.error !== "") {
                    console.error("Focus preference/toggle failure", sawOn, FocusMode.enabled, FocusMode.error);
                    Qt.quit(); return;
                }
                console.log("FOCUS_CONTROLLER_OK"); Qt.quit();
            }
            if (ticks > 100) { console.error("Focus toggle timeout"); Qt.quit(); }
        }
    }
}
'''.replace('BAR', BAR.as_uri()))
            environment = dict(os.environ, QT_QPA_PLATFORM='offscreen', QT_QUICK_BACKEND='software',
                               QML_IMPORT_PATH=str(ROOT / 'quickshell'), HOME=directory,
                               XDG_CONFIG_HOME=directory, XDG_STATE_HOME=directory, XDG_CACHE_HOME=directory,
                               XDG_RUNTIME_DIR=directory, HYPRLAND_INSTANCE_SIGNATURE='',
                               DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent', PATH=directory + os.pathsep + os.environ['PATH'])
            result = subprocess.run(['quickshell', '-p', str(fixture)], env=environment,
                                    capture_output=True, text=True, timeout=10)
            output = result.stdout + result.stderr
            self.assertEqual(result.returncode, 0, output)
            self.assertIn('FOCUS_CONTROLLER_OK', output)
            self.assertEqual((folder / 'actions').read_text().splitlines(), ['on', 'off'])
            self.assertFalse(json.loads((folder / 'eitr/focus.json').read_text())['enabled'])


if __name__ == '__main__':
    import sys
    if len(sys.argv) == 2:
        render_all(sys.argv[1])
    else:
        unittest.main()
