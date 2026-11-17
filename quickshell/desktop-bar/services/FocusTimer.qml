pragma Singleton
import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../ClockModel.js" as ClockModel

// Focus sessions (defaults 25 minutes focus / 5 minutes break, lengths persisted
// in $XDG_CONFIG_HOME/eitr/focus-sessions.json; focus.json belongs to the Focus style preset,
// which rewrites it whole). Session progress
// survives bar restarts via ClockTimers ($XDG_STATE_HOME/eitr/clock.json).
QtObject {
    id: timer

    property bool running: false
    property bool paused: false
    readonly property bool active: running || paused
    property string phase: "focus"
    property int rounds: 0
    property int focusMinutes: 25
    property int breakMinutes: 5
    property real duration: 0
    property real banked: 0
    property real startedAt: 0
    property var preferenceData: ({version: 1})
    property bool preferenceLoaded: false
    property bool _pendingLengths: false

    readonly property real elapsed: active ? banked + (running ? Math.max(0, ClockTimers.now - startedAt) : 0) : 0
    readonly property real remaining: active ? Math.max(0, duration - elapsed) : 0
    readonly property real progress: duration > 0 && active ? Math.min(1, elapsed / duration) : 0

    function snapshot() {
        return {
            active: active,
            running: running,
            paused: paused,
            phase: phase,
            rounds: rounds,
            breakMinutes: breakMinutes,
            durationMs: duration,
            bankedMs: banked,
            startedAtMs: running ? startedAt : 0
        };
    }

    function sync() {
        ClockTimers.setFocusState(snapshot());
    }

    function begin(milliseconds) {
        const current = ClockTimers.refreshNow();
        duration = Math.max(1000, milliseconds);
        banked = 0;
        startedAt = current;
        paused = false;
        running = true;
        sync();
    }

    function startFocus() {
        phase = "focus";
        rounds = 0;
        begin(focusMinutes * 60000);
    }

    function pause() {
        if (!running) return;
        const current = ClockTimers.refreshNow();
        banked += Math.max(0, current - startedAt);
        running = false;
        paused = true;
        sync();
    }

    function resume() {
        if (!paused) return;
        startedAt = ClockTimers.refreshNow();
        paused = false;
        running = true;
        sync();
    }

    function stop() {
        running = false;
        paused = false;
        banked = 0;
        duration = 0;
        phase = "focus";
        sync();
    }

    function skipBreak() {
        if (!active || phase !== "break") return;
        phase = "focus";
        begin(focusMinutes * 60000);
    }

    function writeLengths() {
        preferenceData = Object.assign({}, preferenceData, {
            version: 1,
            focusMinutes: focusMinutes,
            breakMinutes: breakMinutes
        });
        preference.setText(JSON.stringify(preferenceData, null, 2) + "\n");
    }

    function setLengths(nextFocusMinutes, nextBreakMinutes) {
        const parsedFocus = Math.max(1, Math.min(180, Math.round(Number(nextFocusMinutes) || 25)));
        const parsedBreak = Math.max(1, Math.min(60, Math.round(Number(nextBreakMinutes) || 5)));
        focusMinutes = parsedFocus;
        breakMinutes = parsedBreak;
        if (preferenceLoaded) writeLengths();
        else _pendingLengths = true;
    }

    function finish() {
        if (phase === "focus") {
            rounds += 1;
            phase = "break";
            notifyBreakStarted();
            begin(breakMinutes * 60000);
            return;
        }
        running = false;
        paused = false;
        banked = 0;
        duration = 0;
        phase = "focus";
        sync();
        notifyBreakFinished();
    }

    function notifyBreakStarted() {
        notify(
            Eitr.I18n.tr("Time for a break"),
            Eitr.I18n.tr("{minutes} minutes, then back to focus.", {minutes: breakMinutes}),
            [["skip", Eitr.I18n.tr("Skip break")]]
        );
    }

    function notifyBreakFinished() {
        notify(
            Eitr.I18n.tr("Break is over"),
            Eitr.I18n.tr("Start another focus session when you are ready."),
            [["focus", Eitr.I18n.tr("Start focus")]]
        );
    }

    function act(choice) {
        if (choice === "skip" || choice === "focus") {
            phase = "focus";
            begin(focusMinutes * 60000);
        }
    }

    // No icon name triggers the notification card's bell fallback.
    function notify(title, body, actions) {
        alert.running = false;
        alert.command = ["notify-send", "-a", "Eitr", "-u", "critical", "--wait"]
            .concat(...actions.map(action => ["-A", action[0] + "=" + action[1]])).concat([title, body]);
        alert.running = true;
    }

    function applyRestored(focusState, eventName) {
        const state = focusState || ClockModel.emptyFocus();
        running = state.running === true;
        paused = state.paused === true;
        phase = state.phase === "break" ? "break" : "focus";
        rounds = state.rounds || 0;
        duration = state.durationMs || 0;
        banked = state.bankedMs || 0;
        startedAt = state.startedAtMs || 0;
        if (eventName === "break-started") notifyBreakStarted();
        else if (eventName === "break-finished") notifyBreakFinished();
    }

    function clock(milliseconds) {
        return ClockModel.formatClock(milliseconds);
    }

    Component.onCompleted: {
        if (ClockTimers.stateLoaded) {
            const eventName = ClockTimers.consumeRestoredFocusEvent();
            if (ClockTimers.focusSnapshot.active || eventName) {
                applyRestored(ClockTimers.focusSnapshot, eventName);
            }
        }
    }

    property Connections timerSync: Connections {
        target: ClockTimers
        function onNowChanged() {
            if (timer.running && timer.remaining <= 0) timer.finish();
        }
        function onFocusRestored(focusState, eventName) {
            timer.applyRestored(focusState, eventName);
            ClockTimers.consumeRestoredFocusEvent();
        }
    }

    property Process alert: Process {
        stdout: StdioCollector { onStreamFinished: timer.act(text.trim()) }
    }

    property FileView preference: FileView {
        path: Eitr.Paths.config("eitr/focus-sessions.json")
        watchChanges: true
        atomicWrites: true
        printErrors: false
        onFileChanged: reload()
        onLoaded: {
            timer.preferenceLoaded = true;
            try {
                const loaded = Eitr.Paths.settings(text());
                timer.preferenceData = loaded;
                if (timer._pendingLengths) {
                    timer._pendingLengths = false;
                    timer.writeLengths();
                    return;
                }
                const focusLen = Number(loaded.focusMinutes);
                const breakLen = Number(loaded.breakMinutes);
                if (Number.isFinite(focusLen) && focusLen >= 1) timer.focusMinutes = Math.round(focusLen);
                if (Number.isFinite(breakLen) && breakLen >= 1) timer.breakMinutes = Math.round(breakLen);
            } catch (_error) {
                timer.preferenceData = {version: 1};
                if (timer._pendingLengths) {
                    timer._pendingLengths = false;
                    timer.writeLengths();
                }
            }
        }
        onLoadFailed: {
            timer.preferenceLoaded = true;
            timer.preferenceData = {version: 1};
            if (timer._pendingLengths) {
                timer._pendingLengths = false;
                timer.writeLengths();
                return;
            }
            timer.focusMinutes = 25;
            timer.breakMinutes = 5;
        }
    }
}
