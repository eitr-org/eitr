const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const root = path.resolve(__dirname, "..");
const context = vm.createContext({});
const source = fs.readFileSync(path.join(root, "ClockModel.js"), "utf8").replace(".pragma library", "");
vm.runInContext(source, context);

assert.equal(context.parseCustomDurationMs(1, 5, 9), 3909000);
assert.equal(context.parseCustomDurationMs(-2, 0, 15), 15000);
assert.equal(context.formatClock(0), "0:00");
assert.equal(context.formatClock(42000), "0:42");
assert.equal(context.formatClock(100), "0:01");
assert.equal(context.formatClock(3909000), "1:05:09");
assert.equal(context.formatStopwatch(0), "0:00.0");
assert.equal(context.formatStopwatch(12340), "0:12.3");
assert.equal(context.formatStopwatch(3661900), "1:01:01.9");
assert.equal(context.formatDeltaTenths(null), "");
assert.equal(context.formatDeltaTenths(-12), "-1.2s");
assert.equal(context.formatDeltaTenths(5), "+0.5s");
assert.equal(context.formatDeltaTenths(615), "+1:01.5");

// Multi-timer sorting: running shortest first, then paused, then ended newest first.
const now = 1000000;
const timerLong = context.createTimer("t1", 600000, "Work", now, true);
const timerShort = context.createTimer("t2", 60000, "Tea", now, true);
const timerPaused = Object.assign(context.createTimer("t3", 300000, "Paused", now, true), {running: false, remainingMs: 45000});
const timerEnded = Object.assign(context.createTimer("t4", 30000, "Done", now - 40000, true), {running: false, ended: true, alerted: true, remainingMs: 0, endAtMs: now - 10000});
const sorted = context.sortTimers([timerEnded, timerLong, timerPaused, timerShort], now);
assert.deepEqual(Array.from(sorted.map(entry => entry.id)), ["t2", "t1", "t3", "t4"]);

// Timer completion transitions running -> ended and flags newly ended once.
const afterMinute = context.advanceTimers(sorted, now + 60000);
assert.equal(afterMinute.newlyEnded.length, 1);
assert.equal(afterMinute.newlyEnded[0].id, "t2");
assert.equal(afterMinute.timers.find(entry => entry.id === "t2").ended, true);
const secondTick = context.advanceTimers(afterMinute.timers, now + 61000);
assert.equal(secondTick.newlyEnded.length, 0);

// Stopwatch elapsed & laps newest first with comparison to previous lap.
const sw = {
    running: true,
    paused: false,
    startedAtMs: now - 28500,
    bankedMs: 0,
    laps: [
        {splitMs: 10500, totalMs: 10500},
        {splitMs: 9200, totalMs: 19700},
        {splitMs: 11400, totalMs: 31100}
    ]
};
assert.equal(context.stopwatchElapsedMs(sw, now), 28500);
const lapRows = context.computeLapRows(sw);
assert.deepEqual(Array.from(lapRows.map(row => row.number)), [3, 2, 1]);
assert.equal(lapRows[0].trend, "slower");
assert.equal(lapRows[0].deltaText, "+2.2s");
assert.equal(lapRows[1].trend, "faster");
assert.equal(lapRows[1].deltaText, "-1.3s");
assert.equal(lapRows[2].trend, "first");
assert.equal(lapRows[2].deltaText, "");

// Bar activity priority: countdown ending first > running focus > running stopwatch.
const focusRunning = {active: true, running: true, paused: false, phase: "focus", rounds: 0, breakMinutes: 5, durationMs: 1500000, bankedMs: 0, startedAtMs: now - 60000};
const actTimerFirst = context.computeActivity([timerLong, timerShort], focusRunning, sw, now);
assert.equal(actTimerFirst.kind, "timer");
assert.equal(actTimerFirst.page, "timers");
assert.equal(actTimerFirst.timerId, "t2");

const actFocusNext = context.computeActivity([], focusRunning, sw, now);
assert.equal(actFocusNext.kind, "focus");
assert.equal(actFocusNext.page, "focus");

const actStopwatchNext = context.computeActivity([], context.emptyFocus(), sw, now);
assert.equal(actStopwatchNext.kind, "stopwatch");
assert.equal(actStopwatchNext.page, "stopwatch");

// Idle when only ended timers or paused stopwatch exist.
const actIdle = context.computeActivity([timerEnded], context.emptyFocus(), Object.assign({}, sw, {running: false, paused: true}), now);
assert.equal(actIdle.active, false);

// Wall-clock persistence restore: ended-while-down notifies once, focus break advances.
const rawSaved = JSON.stringify(context.serializeState([timerShort, timerLong], sw, focusRunning));
const restoredLater = context.restoreState(rawSaved, now + 1500000, 5);
assert.equal(restoredLater.newlyEndedTimers.length, 2);
assert.equal(restoredLater.focus.phase, "break");
assert.equal(restoredLater.focus.rounds, 1);
assert.equal(restoredLater.focusEvent, "break-started");
assert.equal(restoredLater.stopwatch.laps.length, 3);

// Second restart after saving alerted state must not notify again.
const savedAgain = JSON.stringify(context.serializeState(restoredLater.timers, restoredLater.stopwatch, restoredLater.focus));
const restoredThird = context.restoreState(savedAgain, now + 1505000, 5);
assert.equal(restoredThird.newlyEndedTimers.length, 0);

console.log("ClockModel unit tests passed");
