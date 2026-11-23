"""Render the Clock alarm list and ringing content without scheduling or playing audio."""
import json
import os
from pathlib import Path
import time
import tempfile
import unittest

from layout_render import capture_path, render, render_environment
from test_clock import copy_clock_runtime, make_probe_bin

FIXTURE = '''import QtQuick
import Quickshell
import "." as Bar

ShellRoot {
    id: fixture
    property int step: 0
    readonly property bool light: step % 2 === 1
    readonly property bool ringing: step >= 2
    readonly property color fg: light ? "#273b32" : "#cdd6f4"
    readonly property color bg: light ? "#f3f8f1" : "#181824"
    readonly property color accent: light ? "#32644c" : "#89b4fa"
    Binding { target: Bar.PluginRegistry; property: "clockFormat"; value: fixture.light ? "24h" : "12h" }
    FloatingWindow {
        visible: true
        implicitWidth: 420
        implicitHeight: 660
        Bar.ClockContent {
            id: clock
            anchors.fill: parent
            visible: !fixture.ringing
            foreground: fixture.fg
            accent: fixture.accent
            background: fixture.bg
            page: "alarms"
            opened: true
            live: false
        }
    }
    FloatingWindow {
        visible: fixture.ringing
        implicitWidth: 960
        implicitHeight: 600
        Bar.AlarmRingingContent {
            id: alarm
            anchors.fill: parent
            foreground: fixture.fg
            accent: fixture.accent
            color: fixture.bg
            alarmName: "Morning walk"
            alarmTime: fixture.light ? "07:30" : "7:30 AM"
        }
    }
    Timer {
        interval: 350
        running: true
        repeat: true
        onTriggered: {
            const surface = fixture.ringing ? alarm : clock;
            const filename = (fixture.ringing ? "ringing-" : "alarms-") + (fixture.light ? "light" : "dark");
            surface.grabToImage(result => {
                if (!result.saveToFile("OUTPUT/" + filename + ".png")) {
                    Qt.exit(1);
                    return;
                }
                if (++fixture.step === 4) {
                    console.log("ALARM_RENDER_OK");
                    Qt.quit();
                }
            });
        }
    }
}
'''

STATE = '''[
    {"id":"1","text":"Morning walk","due":1900000000,"alarm":{"clock":"07:30","days":[0,2,4],"sound":"alarm-clock-elapsed","enabled":true}},
    {"id":"2","text":"Call the bakery","due":1900003600,"alarm":{"clock":"13:15","days":[],"sound":"message-new-instant","enabled":false}}
]'''


class AlarmRenderTests(unittest.TestCase):
    def test_alarm_surfaces(self):
        with tempfile.TemporaryDirectory(prefix="eitr-alarm-render-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            (folder / "eitr").mkdir()
            (folder / "eitr/reminders.json").write_text(STATE)
            output = capture_path("ALARM", folder, "alarms-dark.png").parent
            fixture = folder / "alarm-render.qml"
            fixture.write_text(FIXTURE.replace("OUTPUT", str(output)))
            code, log = render(fixture, render_environment(folder), timeout=12)
            self.assertEqual(code, 0, log)
            self.assertIn("ALARM_RENDER_OK", log)
            for name in ("alarms-dark", "alarms-light", "ringing-dark", "ringing-light"):
                self.assertTrue((output / f"{name}.png").read_bytes().startswith(b"\x89PNG"))

    def test_ringing_keyboard_shortcuts(self):
        with tempfile.TemporaryDirectory(prefix="eitr-alarm-keys-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            fixture = folder / "alarm-keys.qml"
            fixture.write_text(KEYS)
            code, log = render(fixture, render_environment(folder), timeout=12)
            self.assertEqual(code, 0, log)
            self.assertIn("ALARM_KEYS_OK", log)

    def test_locked_alarm_plays_one_shared_sound_and_observes_unlock(self):
        with tempfile.TemporaryDirectory(prefix="eitr-alarm-service-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            code_root = folder / "code"
            launch = code_root / "quickshell/lockscreen/scripts/launch.sh"
            launch.parent.mkdir(parents=True)
            launch.write_text('[[ "$1" == active && -f "$XDG_RUNTIME_DIR/locked" ]]\n')
            (folder / "locked").touch()
            helper = code_root / "walker/scripts/actions/tools/reminders.py"
            helper.parent.mkdir(parents=True)
            helper.write_text("""import json, os, sys
from pathlib import Path
state = Path(os.environ["XDG_STATE_HOME"])
if sys.argv[1:] != ["alarm-stop", "1"]:
    raise SystemExit(1)
(state / "eitr/updated.json").write_text("[]")
(state / "eitr/updated.json").replace(state / "eitr/reminders.json")
""")
            bin_dir = make_probe_bin(folder)
            (folder / "eitr").mkdir()
            state = json.loads(STATE)
            state[0]["alarm"].update(ringUntil=int(time.time()) + 30, ringTime="07:30")
            (folder / "eitr/reminders.json").write_text(json.dumps(state))
            fixture = folder / "alarm-service.qml"
            fixture.write_text(SERVICE.replace("FIXTURE_DIR", str(folder)))
            environment = render_environment(folder)
            environment.update(EITR_CODE_ROOT=str(code_root), PATH=f"{bin_dir}:{os.environ['PATH']}")
            code, log = render(fixture, environment, timeout=12)
            self.assertEqual(code, 0, log)
            self.assertIn("ALARM_SERVICE_OK", log)
            calls = [json.loads(line) for line in (folder / "probes.jsonl").read_text().splitlines()]
            self.assertTrue(calls)
            self.assertTrue(all(call["cmd"] == "pw-play" and call["args"][0].endswith("alarm-clock-elapsed.oga")
                                for call in calls))


KEYS = '''import QtQuick
import QtTest
import Quickshell
import "." as Bar

ShellRoot {
    id: root
    property int stops: 0
    property int snoozes: 0
    FloatingWindow {
        id: window
        visible: true
        implicitWidth: 640
        implicitHeight: 480
        Bar.AlarmRingingContent {
            id: alarm
            anchors.fill: parent
            foreground: "white"
            accent: "lightblue"
            color: "black"
            alarmName: "Morning"
            alarmTime: "07:30"
            onStopped: root.stops++
            onSnoozed: root.snoozes++
        }
    }
    TestCase {
        name: "AlarmKeys"
        when: window.visible
        function test_shortcuts() {
            wait(100);
            alarm.forceActiveFocus();
            keyClick(Qt.Key_Return);
            keyClick(Qt.Key_Enter);
            keyClick(Qt.Key_Escape);
            keyClick(Qt.Key_Space);
            keyClick(Qt.Key_S);
            compare(root.stops, 3);
            compare(root.snoozes, 2);
            console.log("ALARM_KEYS_OK");
            Qt.quit();
        }
    }
}
'''

SERVICE = '''import QtQuick
import Quickshell
import Quickshell.Io
import "." as Bar

ShellRoot {
    id: root
    property int step: 0
    FileView {
        id: audioProbe
        path: "FIXTURE_DIR/probes.jsonl"
        watchChanges: true
        printErrors: false
        onFileChanged: reload()
    }
    Timer {
        interval: 250
        running: true
        repeat: true
        onTriggered: {
            if (root.step === 0 && Bar.ClockAlarms.ringing && audioProbe.text().includes("pw-play")) {
                if (Bar.ClockAlarms.unlocked) {
                    console.error("Overlay activated while locked");
                    Qt.exit(1);
                    return;
                }
                root.step = 1;
                Quickshell.execDetached(["rm", "FIXTURE_DIR/locked"]);
            } else if (root.step === 1 && Bar.ClockAlarms.unlocked) {
                root.step = 2;
                Bar.ClockAlarms.run("alarm-stop", "1");
            } else if (root.step === 2 && !Bar.ClockAlarms.ringing && !Bar.ClockAlarms.unlocked) {
                console.log("ALARM_SERVICE_OK");
                Qt.quit();
            }
        }
    }
}
'''
