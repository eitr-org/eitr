pragma Singleton
import ".."
import QtQuick
import Quickshell.Io
import Eitr as Eitr
import "../ClockModel.js" as ClockModel

// Owns multi-timer countdowns, the stopwatch with laps, bar clock activity
// selection, and atomic state persistence in $XDG_STATE_HOME/eitr/clock.json.
QtObject {
    id: clockTimers

    property var timers: []
    property var stopwatch: ClockModel.emptyStopwatch()
    property var focusSnapshot: ClockModel.emptyFocus()
    property double now: Date.now()
    property int activeAlerts: 0
    property bool saving: false
    property bool stateLoaded: false
    property string restoredFocusEvent: ""
    property bool _dirtyBeforeLoad: false
    property int _idCounter: 0

    readonly property string statePath: Eitr.Paths.state("eitr/clock.json")

    signal focusRestored(var focusState, string eventName)

    readonly property bool hasRunningTimers: {
        for (let index = 0; index < timers.length; index += 1) {
            if (timers[index].running && !timers[index].ended) return true;
        }
        return false;
    }
    readonly property bool stopwatchRunning: stopwatch.running === true
    readonly property bool stopwatchPaused: stopwatch.paused === true
    readonly property bool stopwatchActive: stopwatchRunning || stopwatchPaused
    readonly property real stopwatchElapsed: ClockModel.stopwatchElapsedMs(stopwatch, now)
    readonly property var stopwatchLaps: ClockModel.computeLapRows(stopwatch)
    readonly property bool anyRunning: hasRunningTimers || stopwatchRunning || (focusSnapshot.active === true && focusSnapshot.running === true)

    readonly property var activity: ClockModel.computeActivity(timers, focusSnapshot, stopwatch, now)
    readonly property bool activityActive: activity.active
    readonly property string activityPage: activity.page
    readonly property real activityProgress: activity.progress
    readonly property bool activityIsBreak: activity.isBreak
    readonly property string activityTimeText: activity.timeText
    readonly property string activityKind: activity.kind
    readonly property string activityName: activity.name

    function refreshNow() {
        const current = Date.now();
        now = current;
        return current;
    }

    function markDirty() {
        if (!stateLoaded) _dirtyBeforeLoad = true;
    }

    function saveState() {
        markDirty();
        saving = true;
        stateFile.setText(JSON.stringify(ClockModel.serializeState(timers, stopwatch, focusSnapshot)) + "\n");
    }

    function nextId() {
        _idCounter += 1;
        return "t-" + Math.round(Date.now()) + "-" + _idCounter;
    }

    function addTimer(durationMs, name) {
        const current = refreshNow();
        const length = Math.max(1000, Math.round(Number(durationMs) || 0));
        if (!(length > 0)) return "";
        const entry = ClockModel.createTimer(nextId(), length, name, current, true);
        timers = ClockModel.sortTimers(timers.concat([entry]), current);
        saveState();
        return entry.id;
    }

    function addQuickTimer(minutes, name) {
        return addTimer(Math.round(Number(minutes) * 60000), name);
    }

    function addCustomTimer(hours, minutes, seconds, name) {
        const length = ClockModel.parseCustomDurationMs(hours, minutes, seconds);
        return length > 0 ? addTimer(length, name) : "";
    }

    function updateTimerById(id, updater) {
        const current = refreshNow();
        let found = false;
        const next = [];
        for (let index = 0; index < timers.length; index += 1) {
            const item = timers[index];
            if (item.id === id) {
                found = true;
                const updated = updater(item, current);
                if (updated) next.push(updated);
            } else {
                next.push(item);
            }
        }
        if (!found) return false;
        timers = ClockModel.sortTimers(next, current);
        saveState();
        return true;
    }

    function pauseTimer(id) {
        return updateTimerById(id, function(item, current) {
            if (!item.running || item.ended) return item;
            return Object.assign({}, item, {
                running: false,
                remainingMs: ClockModel.timerRemainingMs(item, current)
            });
        });
    }

    function resumeTimer(id) {
        let endedEntry = null;
        let shouldNotify = false;
        const ok = updateTimerById(id, function(item, current) {
            if (item.running || item.ended) return item;
            const left = Math.max(0, Number(item.remainingMs) || 0);
            if (left <= 0) {
                shouldNotify = !item.alerted;
                endedEntry = Object.assign({}, item, {running: false, ended: true, remainingMs: 0, alerted: true});
                return endedEntry;
            }
            return Object.assign({}, item, {
                running: true,
                ended: false,
                endAtMs: current + left
            });
        });
        if (endedEntry && shouldNotify) notifyTimerEnded(endedEntry);
        return ok;
    }

    function restartTimer(id) {
        return updateTimerById(id, function(item, current) {
            return Object.assign({}, item, {
                running: true,
                ended: false,
                alerted: false,
                remainingMs: item.durationMs,
                endAtMs: current + item.durationMs
            });
        });
    }

    function removeTimer(id) {
        return updateTimerById(id, function(_item, _current) { return null; });
    }

    function clearEndedTimers() {
        const current = refreshNow();
        const kept = [];
        let removed = false;
        for (let index = 0; index < timers.length; index += 1) {
            if (timers[index].ended) removed = true;
            else kept.push(timers[index]);
        }
        if (!removed) return;
        timers = ClockModel.sortTimers(kept, current);
        saveState();
    }

    function timerRemaining(entry) {
        return ClockModel.timerRemainingMs(entry, now);
    }

    function timerProgress(entry) {
        return ClockModel.timerProgress(entry, now);
    }

    function timerLabel(entry) {
        if (entry && entry.name && entry.name.length > 0) return entry.name;
        return entry && entry.durationMs
            ? Eitr.I18n.tr("{time} timer", {time: ClockModel.formatClock(entry.durationMs)})
            : Eitr.I18n.tr("Timer");
    }

    function startStopwatch() {
        const current = refreshNow();
        stopwatch = {running: true, paused: false, startedAtMs: current, bankedMs: 0, laps: []};
        saveState();
    }

    function pauseStopwatch() {
        if (!stopwatch.running) return;
        const current = refreshNow();
        stopwatch = {
            running: false,
            paused: true,
            startedAtMs: 0,
            bankedMs: ClockModel.stopwatchElapsedMs(stopwatch, current),
            laps: stopwatch.laps.slice()
        };
        saveState();
    }

    function resumeStopwatch() {
        if (!stopwatch.paused) return;
        const current = refreshNow();
        stopwatch = {
            running: true,
            paused: false,
            startedAtMs: current,
            bankedMs: stopwatch.bankedMs,
            laps: stopwatch.laps.slice()
        };
        saveState();
    }

    function lapStopwatch() {
        if (!stopwatchActive) return;
        const current = refreshNow();
        const totalMs = ClockModel.stopwatchElapsedMs(stopwatch, current);
        if (totalMs <= 0 && !stopwatch.running) return;
        const laps = stopwatch.laps.slice();
        const previousTotal = laps.length > 0 ? laps[laps.length - 1].totalMs : 0;
        laps.push({splitMs: Math.max(0, totalMs - previousTotal), totalMs: totalMs});
        stopwatch = Object.assign({}, stopwatch, {laps: laps});
        saveState();
    }

    function resetStopwatch() {
        refreshNow();
        stopwatch = ClockModel.emptyStopwatch();
        saveState();
    }

    function setFocusState(snapshot) {
        focusSnapshot = snapshot || ClockModel.emptyFocus();
        saveState();
    }

    function consumeRestoredFocusEvent() {
        const pending = restoredFocusEvent;
        restoredFocusEvent = "";
        return pending;
    }

    function formatClock(milliseconds) { return ClockModel.formatClock(milliseconds); }
    function formatStopwatch(milliseconds) { return ClockModel.formatStopwatch(milliseconds); }

    function notifyTimerEnded(entry) {
        EventSounds.play(EventSounds.timerSound);
        const title = entry.name && entry.name.length > 0
            ? Eitr.I18n.tr("Timer finished: {name}", {name: entry.name})
            : Eitr.I18n.tr("Timer finished");
        const body = ClockModel.formatClock(entry.durationMs);
        const process = notifyProcess.createObject(clockTimers, {
            timerId: entry.id,
            // The timer plays its own sound; the hint keeps the desktop's notification chime quiet.
            command: ["notify-send", "-a", "Eitr", "-u", "critical", "--wait", "-h", "boolean:suppress-sound:true",
                "-A", "restart=" + Eitr.I18n.tr("Restart"), title, body]
        });
        if (process) {
            activeAlerts++;
            process.running = true;
        }
    }

    function tickTimers() {
        const current = refreshNow();
        const step = ClockModel.advanceTimers(timers, current);
        if (step.changed) {
            timers = step.timers;
            saveState();
            for (let index = 0; index < step.newlyEnded.length; index += 1) {
                notifyTimerEnded(step.newlyEnded[index]);
            }
        }
    }

    property Timer tick: Timer {
        interval: clockTimers.stopwatchRunning ? 100 : 250
        repeat: true
        running: clockTimers.anyRunning
        onTriggered: clockTimers.tickTimers()
    }

    property Component notifyProcess: Component {
        Process {
            id: alertProc
            property string timerId: ""
            property bool processExited: false
            property bool streamDone: false
            Component.onDestruction: clockTimers.activeAlerts--
            function maybeDestroy() {
                if (processExited && streamDone) alertProc.destroy();
            }
            stdout: StdioCollector {
                onStreamFinished: {
                    if (text.trim() === "restart") clockTimers.restartTimer(alertProc.timerId);
                    alertProc.streamDone = true;
                    alertProc.maybeDestroy();
                }
            }
            onExited: {
                alertProc.processExited = true;
                alertProc.maybeDestroy();
            }
        }
    }

    property FileView stateFile: FileView {
        path: clockTimers.statePath
        watchChanges: false
        atomicWrites: true
        printErrors: false
        onSaved: clockTimers.saving = false
        onSaveFailed: clockTimers.saving = false
        onLoaded: {
            clockTimers.stateLoaded = true;
            if (clockTimers._dirtyBeforeLoad) {
                clockTimers._dirtyBeforeLoad = false;
                clockTimers.saveState();
                return;
            }
            const current = clockTimers.refreshNow();
            const restored = ClockModel.restoreState(text(), current, 5);
            clockTimers.timers = restored.timers;
            clockTimers.stopwatch = restored.stopwatch;
            clockTimers.focusSnapshot = restored.focus;
            clockTimers.restoredFocusEvent = restored.focusEvent;
            clockTimers.focusRestored(restored.focus, restored.focusEvent);
            if (restored.needsSave) clockTimers.saveState();
            for (let index = 0; index < restored.newlyEndedTimers.length; index += 1) {
                clockTimers.notifyTimerEnded(restored.newlyEndedTimers[index]);
            }
        }
        onLoadFailed: {
            clockTimers.stateLoaded = true;
        }
    }
}
