"""Unit and offscreen Quickshell tests for Clock, ClockTimers, FocusTimer and renders."""
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

from layout_render import BAR, capture_path, copy_runtime, render, render_environment

ALARM_SOUND = "/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga"


def make_probe_bin(folder: Path, restart_match: str = "") -> Path:
    bin_dir = folder / "probe-bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    log_path = folder / "probes.jsonl"
    notify = bin_dir / "notify-send"
    notify.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        "args = sys.argv[1:]\n"
        f"open({str(log_path)!r}, 'a').write(json.dumps({{'cmd': 'notify-send', 'args': args}}) + '\\n')\n"
        + (f"if any({restart_match!r} in arg for arg in args):\n    print('restart', flush=True)\n" if restart_match else ""),
        encoding="utf-8",
    )
    notify.chmod(0o755)
    pw_play = bin_dir / "pw-play"
    pw_play.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys\n"
        f"open({str(log_path)!r}, 'a').write(json.dumps({{'cmd': 'pw-play', 'args': sys.argv[1:]}}) + '\\n')\n",
        encoding="utf-8",
    )
    pw_play.chmod(0o755)
    return bin_dir


def copy_clock_runtime(folder: Path) -> None:
    copy_runtime(folder)
    (folder / "services/DesktopData.qml").write_text(
        """pragma Singleton
import QtQuick
QtObject {
 property var topics: ({})
 property var client: QtObject { function detachAction(identifier) {} }
 function observe(topic, owner, interval) { return topic; }
 function release(token) {}
 function releaseOwner(owner) {}
 function refresh(topic) {}
 function queryCatalog(name, args, owner, callback) { callback("", {}); }
}
"""
    )


class ClockServiceAndBarTests(unittest.TestCase):
    def test_timers_dnd_restart_focus_config_and_bar_ring_click(self):
        with tempfile.TemporaryDirectory(prefix="eitr-clock-svc-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            (folder / "eitr").mkdir(parents=True, exist_ok=True)
            (folder / "eitr/focus.json").write_text(json.dumps({"version": 1, "enabled": True}) + "\n", encoding="utf-8")
            bin_dir = make_probe_bin(folder, restart_match="Tea")

            fixture = """import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 id: root
 property var openedPages: []
 function showClock(page) { openedPages = openedPages.concat([page]); }
 Timer {
  interval: 150; running: true; repeat: true
  property int phase: 0
  property string teaId: ""
  property double initialTeaEnd: 0
  property bool restartedPhase: false
  onTriggered: {
   if (phase === 0) {
    Bar.FocusTimer.setLengths(45, 10);
    if (Bar.FocusTimer.focusMinutes !== 45 || Bar.FocusTimer.breakMinutes !== 10) throw new Error("focus lengths update");
    Bar.FocusTimer.startFocus();
    Bar.ClockTimers.startStopwatch();
    if (Bar.ClockTimers.activityPage !== "focus") throw new Error("focus beats stopwatch");
    teaId = Bar.ClockTimers.addTimer(1100, "Tea");
    if (Bar.ClockTimers.activityPage !== "timers") throw new Error("timer beats focus");
    const longerId = Bar.ClockTimers.addQuickTimer(10, "Bread");
    if (Bar.ClockTimers.timers[0].id !== teaId || Bar.ClockTimers.timers[1].id !== longerId) throw new Error("timer order");
    initialTeaEnd = Bar.ClockTimers.timers[0].endAtMs;
    Bar.ClockTimers.pauseTimer(longerId);
   } else if (!restartedPhase && phase < 35) {
    // Wait until 1.1s timer expires, chimes, posts notify-send, and auto-restarts via "restart".
    const tea = Bar.ClockTimers.timers.find(entry => entry.id === teaId);
    if (!tea) throw new Error("tea timer missing");
    if (tea.running && !tea.ended && tea.endAtMs > initialTeaEnd + 400) {
     restartedPhase = true;
     Bar.ClockTimers.pauseTimer(teaId);
     Bar.EventSounds.doNotDisturb = true;
     Bar.ClockTimers.addTimer(900, "Silent");
     Bar.FocusTimer.skipBreak();
     Bar.FocusTimer.stop();
     Bar.ClockTimers.lapStopwatch();
     phase = 51;
     return;
    }
   } else if (!restartedPhase) {
    stop();
    throw new Error("tea timer never auto-restarted from notification action");
   } else if (phase >= 51 && phase < 85) {
    // Wait for the 1s Silent timer to end under Do Not Disturb.
    const silent = Bar.ClockTimers.timers.find(entry => entry.name === "Silent");
    if (silent && silent.ended) { phase = 86; return; }
   } else if (phase === 85) {
    stop();
    throw new Error("silent timer did not finish in time");
   } else if (phase === 86 || phase === 87) {
    // Allow async notify-send probe two ticks to finish flushing.
   } else {
    if (Bar.ClockTimers.activityPage !== "stopwatch") throw new Error("running stopwatch should now own ring");
    root.showClock(Bar.ClockTimers.activityPage);
    if (!root.openedPages.length || root.openedPages[0] !== "stopwatch") throw new Error("click target mismatch");
    console.log("CLOCK_SERVICE_OK");
    Qt.quit();
   }
   phase++;
  }
 }
}
"""
            (folder / "fixture.qml").write_text(fixture, encoding="utf-8")
            env = render_environment(folder)
            env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")
            code, output = render(folder / "fixture.qml", env, timeout=20)
            self.assertEqual(code, 0, output)
            self.assertIn("CLOCK_SERVICE_OK", output)
            probes = [json.loads(line) for line in (folder / "probes.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            sound_calls = [item for item in probes if item["cmd"] == "pw-play"]
            notify_calls = [item for item in probes if item["cmd"] == "notify-send"]
            # First timer sounded once; second timer under DND did NOT sound.
            self.assertEqual(len(sound_calls), 1, probes)
            self.assertEqual(sound_calls[0]["args"], [ALARM_SOUND])
            self.assertEqual(len(notify_calls), 2, probes)
            self.assertIn("restart=Restart", notify_calls[0]["args"])

            # Session lengths have their own file; the Focus preset's file stays exactly as it was.
            saved_focus = json.loads((folder / "eitr/focus.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_focus, {"version": 1, "enabled": True})
            saved_sessions = json.loads((folder / "eitr/focus-sessions.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_sessions["focusMinutes"], 45)
            self.assertEqual(saved_sessions["breakMinutes"], 10)

            saved_clock = json.loads((folder / "eitr/clock.json").read_text(encoding="utf-8"))
            self.assertEqual(saved_clock["version"], 1)
            self.assertEqual(len(saved_clock["stopwatch"]["laps"]), 1)

    def test_persistence_across_restart_notifies_expired_timer_only_once(self):
        with tempfile.TemporaryDirectory(prefix="eitr-clock-persist-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            now_ms = int(time.time() * 1000)
            (folder / "eitr").mkdir(parents=True, exist_ok=True)
            (folder / "eitr/clock.json").write_text(json.dumps({
                "version": 1,
                "timers": [
                    {
                        "id": "expired-1",
                        "name": "Oven",
                        "durationMs": 60000,
                        "running": True,
                        "ended": False,
                        "alerted": False,
                        "endAtMs": now_ms - 15000,
                        "remainingMs": 60000,
                        "createdAtMs": now_ms - 75000,
                    },
                    {
                        "id": "live-1",
                        "name": "Laundry",
                        "durationMs": 300000,
                        "running": True,
                        "ended": False,
                        "alerted": False,
                        "endAtMs": now_ms + 120000,
                        "remainingMs": 300000,
                        "createdAtMs": now_ms - 180000,
                    },
                ],
                "stopwatch": {
                    "running": False,
                    "paused": True,
                    "startedAtMs": 0,
                    "bankedMs": 14500,
                    "laps": [{"splitMs": 7000, "totalMs": 7000}, {"splitMs": 7500, "totalMs": 14500}],
                },
                "focus": {
                    "active": True,
                    "running": True,
                    "paused": False,
                    "phase": "focus",
                    "rounds": 1,
                    "breakMinutes": 5,
                    "durationMs": 1500000,
                    "bankedMs": 0,
                    "startedAtMs": now_ms - 1560000,
                },
            }), encoding="utf-8")
            bin_dir = make_probe_bin(folder)
            fixture = """import QtQuick
import Quickshell
import "." as Bar
ShellRoot {
 readonly property var _timersRef: Bar.ClockTimers
 readonly property var _focusRef: Bar.FocusTimer
 Timer {
  interval: 150; running: true; repeat: true
  property bool verified: false
  onTriggered: {
   if (!Bar.ClockTimers.stateLoaded) return;
   if (!verified) {
    const expired = Bar.ClockTimers.timers.find(entry => entry.id === "expired-1");
    const live = Bar.ClockTimers.timers.find(entry => entry.id === "live-1");
    if (!expired || !expired.ended) throw new Error("expired timer state");
    if (!live || !live.running || Bar.ClockTimers.timerRemaining(live) <= 10000) throw new Error("live timer state");
    if (Bar.ClockTimers.stopwatchLaps.length !== 2) throw new Error("restored laps");
    if (!Bar.FocusTimer.active || Bar.FocusTimer.phase !== "break" || Bar.FocusTimer.rounds !== 2) throw new Error("restored focus break");
    verified = true;
    return;
   }
   console.log("RESTORE_OK");
   Qt.quit();
  }
 }
}
"""
            (folder / "fixture.qml").write_text(fixture, encoding="utf-8")
            env = render_environment(folder)
            env["PATH"] = str(bin_dir) + ":" + env.get("PATH", "")

            code, output = render(folder / "fixture.qml", env, timeout=12)
            self.assertEqual(code, 0, output)
            self.assertIn("RESTORE_OK", output)
            probes = [json.loads(line) for line in (folder / "probes.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertEqual([item["cmd"] for item in probes].count("pw-play"), 1, probes)
            # 1 for Oven expired timer + 1 for Focus transitioning into break.
            self.assertEqual([item["cmd"] for item in probes].count("notify-send"), 2, probes)

            # Boot a second instance; already-alerted expired timer must NOT notify or chime again.
            (folder / "probes.jsonl").unlink()
            code2, output2 = render(folder / "fixture.qml", env, timeout=12)
            self.assertEqual(code2, 0, output2)
            self.assertIn("RESTORE_OK", output2)
            self.assertFalse((folder / "probes.jsonl").exists())

    def test_bar_ring_and_drop_pill_click_route_to_matching_page(self):
        with tempfile.TemporaryDirectory(prefix="eitr-clock-bar-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            fixture = """import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 id: shellHost
 property var routed: []
 function showClock(page) { routed = routed.concat([page]); }
 FloatingWindow {
  id: barWin
  visible: true; implicitWidth: 240; implicitHeight: 60
  property color fg: "white"
  property var clockActivity: QtObject {
   readonly property bool timing: Bar.ClockTimers.activityActive
   readonly property string timerPage: Bar.ClockTimers.activityPage
   readonly property bool meetingSoon: false
   readonly property string meetingTitle: ""
   readonly property bool bellOut: false
   readonly property real bellAngle: 0
   readonly property bool flash: false
   readonly property string flashText: ""
   readonly property bool flashCritical: false
   readonly property bool lowBattery: false
  }
  property var notificationsRef: ({count: 0, popupCount: 0, popups: []})
  property var obsMenu: null
  property var mediaStrip: null
  property var battery: null
  property var updates: null
  property bool vertical: false
  function showClock(page) { shellHost.showClock(page); }
  Bar.CaptureIndicator {
   id: captureInd
   width: 80; height: 24
   host: barWin
   activity: barWin.clockActivity
   onTimerClicked: barWin.showClock(barWin.clockActivity.timerPage)
  }
  Bar.DropPillActivity {
   id: dropAct
   host: barWin
   barHost: barWin
   timeOffset: 0
  }
 }
 TestCase {
  name: "BarRingRouting"; when: barWin.visible
  function findRingArea(rootItem) {
   for (const child of rootItem.children || []) {
    if (child && child.cursorShape === Qt.PointingHandCursor && child.parent && child.parent.children.some(sub => sub && sub.minimumArc !== undefined)) {
     return child;
    }
    const found = findRingArea(child);
    if (found) return found;
   }
   return null;
  }
  function test_clicks() {
   Bar.ClockTimers.startStopwatch();
   wait(60);
   compare(barWin.clockActivity.timerPage, "stopwatch");
   compare(dropAct.timerPage, "stopwatch");
   mouseClick(findRingArea(dropAct));
   mouseClick(findRingArea(captureInd));
   Bar.FocusTimer.startFocus();
   wait(60);
   compare(barWin.clockActivity.timerPage, "focus");
   compare(dropAct.timerPage, "focus");
   mouseClick(findRingArea(dropAct));
   Bar.ClockTimers.addQuickTimer(5, "Pizza");
   wait(60);
   compare(barWin.clockActivity.timerPage, "timers");
   compare(dropAct.timerPage, "timers");
   mouseClick(findRingArea(dropAct));
   compare(shellHost.routed.join(","), "stopwatch,stopwatch,focus,timers");
   console.log("BAR_RING_ROUTE_OK");
   Qt.quit();
  }
 }
}
"""
            (folder / "fixture.qml").write_text(fixture, encoding="utf-8")
            code, output = render(folder / "fixture.qml", render_environment(folder, (640, 240)), timeout=12)
            self.assertEqual(code, 0, output)
            self.assertIn("BAR_RING_ROUTE_OK", output)


class ClockWindowAndRenderTests(unittest.TestCase):
    def _run_window_suite(self, theme: str, foreground: str, background: str, accent: str, reduce_motion: bool) -> None:
        with tempfile.TemporaryDirectory(prefix=f"eitr-clock-ui-{theme}-") as directory:
            folder = Path(directory)
            copy_clock_runtime(folder)
            (folder / "eitr").mkdir(parents=True, exist_ok=True)
            installed_json = "[]"
            (folder / "plugins/PluginRegistry.qml").write_text(f"""pragma Singleton
import ".."
import QtQuick
QtObject {{
 property string clockFormat: "24h"
 property var entries: []
 property var installed: {installed_json}
 property var placements: ({{version: 3, widgets: [], barItems: []}})
 property var clockBarItems: []
 property var barItems: []
 property bool weatherEnabled: false
 function placedBarItems() {{ return []; }}
}}
""", encoding="utf-8")

            now_ms = int(time.time() * 1000)
            (folder / "eitr/clock.json").write_text(json.dumps({
                "version": 1,
                "timers": [
                    {"id": "tea", "name": "Mint Tea", "durationMs": 300000, "running": True, "ended": False, "alerted": False, "endAtMs": now_ms + 185000, "remainingMs": 300000, "createdAtMs": now_ms - 115000},
                    {"id": "break", "name": "Stretch", "durationMs": 600000, "running": False, "ended": False, "alerted": False, "endAtMs": 0, "remainingMs": 420000, "createdAtMs": now_ms - 180000},
                    {"id": "done", "name": "Sourdough fold", "durationMs": 180000, "running": False, "ended": True, "alerted": True, "endAtMs": now_ms - 5000, "remainingMs": 0, "createdAtMs": now_ms - 185000},
                ],
                "stopwatch": {
                    "running": False,
                    "paused": True,
                    "startedAtMs": 0,
                    "bankedMs": 94300,
                    "laps": [
                        {"splitMs": 32400, "totalMs": 32400},
                        {"splitMs": 29800, "totalMs": 62200},
                        {"splitMs": 32100, "totalMs": 94300},
                    ],
                },
                "focus": {
                    "active": True,
                    "running": False,
                    "paused": True,
                    "phase": "focus",
                    "rounds": 1,
                    "breakMinutes": 5,
                    "durationMs": 1500000,
                    "bankedMs": 540000,
                    "startedAtMs": 0,
                },
            }), encoding="utf-8")

            out_timers = capture_path("CLOCK", directory, f"clock-timers-{theme}.png")
            out_stopwatch = capture_path("CLOCK", directory, f"clock-stopwatch-{theme}.png")
            out_focus = capture_path("CLOCK", directory, f"clock-focus-{theme}.png")
            out_cc = capture_path("CLOCK", directory, f"clock-control-center-{theme}.png")

            fixture = """import QtQuick
import QtTest
import Quickshell
import "." as Bar
ShellRoot {
 id: root
 Bar.ClockWindow {
  id: clock
  foreground: "FOREGROUND"
  background: "BACKGROUND"
  accent: "ACCENT"
 }
 FloatingWindow {
  id: ccHost
  visible: true
  implicitWidth: 520; implicitHeight: 200
  color: "BACKGROUND"
  Rectangle {
   id: ccCard
   anchors.fill: parent; anchors.margins: 16
   radius: 10
   color: Bar.SettingsPalette.surface
   border.width: 1; border.color: Bar.SettingsPalette.line
   property string requestedPage: ""
   Bar.FocusTimerControls {
    anchors.left: parent.left; anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
    anchors.margins: 16
    foreground: "FOREGROUND"; background: "BACKGROUND"; accent: "ACCENT"
    onClockRequested: function(page) { ccCard.requestedPage = page; }
   }
  }
 }
 TestCase {
  name: "ClockRenderAndUi"; when: ccHost.visible
  function test_pages_and_controls() {
   Bar.SiteStyle.light = "LIGHT_BOOL" === "true";
   Bar.DesktopStyle.reduceMotion = "REDUCE_MOTION" === "true";
   wait(180);
   ccCard.grabToImage(result => { if (!result.saveToFile("OUT_CC")) throw new Error("cc grab"); });
   wait(60);
   ccHost.visible = false;

   clock.show("timers");
   clock.implicitWidth = 1040; clock.implicitHeight = 760;
   wait(220);
   const content = clock.contentItem.children.find(child => child && child.objectName === "clock-content");
   if (!content || !clock.opened) throw new Error("clock content not loaded");
   content.grabToImage(result => { if (!result.saveToFile("OUT_TIMERS")) throw new Error("timers grab"); });
   wait(80);

   clock.show("stopwatch");
   wait(200);
   content.grabToImage(result => { if (!result.saveToFile("OUT_STOPWATCH")) throw new Error("sw grab"); });
   wait(80);

   clock.show("focus");
   wait(200);
   content.grabToImage(result => { if (!result.saveToFile("OUT_FOCUS")) throw new Error("focus grab"); });
   wait(80);

   clock.show("focus");
   wait(80);
   clock.show("");
   if (clock.page !== "focus") throw new Error("session page memory");
   Bar.SettingsPalette.select("website", false);
   wait(100);
   if (!Qt.colorEqual(clock.color, Bar.SiteStyle.bg)) throw new Error("website palette failed to update ClockWindow");
   Bar.SettingsPalette.select("theme", false);
   wait(60);
   content.forceActiveFocus();
   wait(40);
   keyClick(Qt.Key_Escape);
   wait(80);
   if (clock.opened) throw new Error("Esc should close clock");
   console.log("CLOCK_UI_OK");
   Qt.quit();
  }
 }
}
"""
            replacements = {
                "FOREGROUND": foreground,
                "BACKGROUND": background,
                "ACCENT": accent,
                "LIGHT_BOOL": "true" if theme == "light" else "false",
                "REDUCE_MOTION": "true" if reduce_motion else "false",
                "OUT_TIMERS": str(out_timers),
                "OUT_STOPWATCH": str(out_stopwatch),
                "OUT_FOCUS": str(out_focus),
                "OUT_CC": str(out_cc),
            }
            for old, new in replacements.items():
                fixture = fixture.replace(old, new)
            (folder / "fixture.qml").write_text(fixture, encoding="utf-8")
            code, output = render(folder / "fixture.qml", render_environment(folder, (1280, 900)), timeout=25)
            self.assertEqual(code, 0, output)
            self.assertIn("CLOCK_UI_OK", output)
            for label in ("TypeError:", "ReferenceError:", "Binding loop", "Error:"):
                self.assertNotIn(label, output)
            for path in (out_timers, out_stopwatch, out_focus, out_cc):
                self.assertTrue(path.is_file() and path.stat().st_size > 4000, f"Empty capture {path}")

    def test_dark_theme(self):
        self._run_window_suite("dark", "#e4e5ef", "#191b25", "#759456", reduce_motion=False)

    def test_light_theme_with_reduce_motion(self):
        self._run_window_suite("light", "#202431", "#f5f3ee", "#5f7f44", reduce_motion=True)


if __name__ == "__main__":
    unittest.main()
