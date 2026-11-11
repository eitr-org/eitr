pragma Singleton
import ".."
import QtQuick
import Quickshell
import Eitr as Eitr

// One timer for Drop's dashboard and pill: a countdown, a stopwatch, or focus sessions (25
// minutes of focus, then a 5-minute break). It keeps running with the dashboard closed;
// a finished countdown or focus phase sends a notification, which rings the pill's bell.
QtObject {
    id: timer
    // "timer", "stopwatch" or "focus"; idle when nothing runs.
    property string mode: "timer"
    property bool running: false
    property bool paused: false
    readonly property bool active: running || paused
    // A countdown's length and the time it had already run before the last pause (ms).
    property real duration: 0
    property real banked: 0
    property real startedAt: 0
    property real now: Date.now()
    // Focus: "focus" or "break", and how many focus sessions finished today's run.
    property string phase: "focus"
    property int rounds: 0
    property int focusMinutes: 25
    property int breakMinutes: 5
    readonly property real elapsed: banked + (running ? now - startedAt : 0)
    readonly property real remaining: Math.max(0, duration - elapsed)
    // 0..1 through a countdown or focus phase; a stopwatch fills once a minute.
    readonly property real progress: mode === "stopwatch" ? (elapsed % 60000) / 60000 : duration > 0 ? Math.min(1, elapsed / duration) : 0

    property Timer tick: Timer {
        interval: 250; repeat: true; running: timer.running
        onTriggered: {
            timer.now = Date.now();
            if (timer.mode !== "stopwatch" && timer.remaining <= 0) timer.finish();
        }
    }
    function begin(kind, milliseconds) {
        mode = kind; duration = milliseconds; banked = 0;
        now = Date.now(); startedAt = now; paused = false; running = true;
    }
    function startTimer(minutes) { begin("timer", minutes * 60000); }
    function startStopwatch() { begin("stopwatch", 0); }
    function startFocus() { phase = "focus"; rounds = 0; begin("focus", focusMinutes * 60000); }
    function pause() {
        if (!running) return;
        now = Date.now(); banked += now - startedAt; running = false; paused = true;
    }
    function resume() {
        if (!paused) return;
        now = Date.now(); startedAt = now; paused = false; running = true;
    }
    function stop() { running = false; paused = false; banked = 0; duration = 0; }
    function finish() {
        if (mode === "focus" && phase === "focus") {
            rounds += 1; phase = "break";
            notify(Eitr.I18n.tr("Time for a break"), Eitr.I18n.tr("{minutes} minutes, then back to focus.", {minutes: breakMinutes}));
            begin("focus", breakMinutes * 60000);
            return;
        }
        stop();
        if (mode === "focus") notify(Eitr.I18n.tr("Break is over"), Eitr.I18n.tr("Start another focus session when you are ready."));
        else notify(Eitr.I18n.tr("Timer finished"), "");
        if (mode === "focus") phase = "focus";
    }
    function notify(title, body) {
        Quickshell.execDetached(["notify-send", "-a", "Eitr", "-u", "critical", "-i", "alarm-symbolic", title, body]);
    }
    // 1:05:09, 25:00 or 0:42.
    function clock(milliseconds) {
        const seconds = Math.ceil(Math.max(0, milliseconds) / 1000 - 0.001);
        const hours = Math.floor(seconds / 3600), minutes = Math.floor(seconds / 60) % 60, rest = seconds % 60;
        return (hours ? hours + ":" + String(minutes).padStart(2, "0") : String(minutes)) + ":" + String(rest).padStart(2, "0");
    }
}
