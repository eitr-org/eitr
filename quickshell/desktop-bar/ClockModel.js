.pragma library

// Pure timer, stopwatch, focus-restoration, and persistence helpers shared by
// ClockTimers, FocusTimer, Control Center, and the Node unit tests.

function pad2(value) { return String(Math.max(0, Math.floor(value))).padStart(2, "0"); }

function clampInt(value) {
    const number = Math.floor(Number(value));
    return Number.isFinite(number) && number > 0 ? number : 0;
}

function parseCustomDurationMs(hours, minutes, seconds) {
    return (clampInt(hours) * 3600 + clampInt(minutes) * 60 + clampInt(seconds)) * 1000;
}

// Formats a countdown or focus duration: "1:05:09", "25:00", or "0:42".
function formatClock(milliseconds) {
    const raw = Math.max(0, Number(milliseconds) || 0);
    const totalSeconds = Math.max(0, Math.ceil(raw / 1000 - 0.001));
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor(totalSeconds / 60) % 60;
    const seconds = totalSeconds % 60;
    return (hours > 0 ? hours + ":" + pad2(minutes) : String(minutes)) + ":" + pad2(seconds);
}

// Formats stopwatch elapsed time with tenths: "0:00.0", "12:34.5", or "1:02:03.4".
function formatStopwatch(milliseconds) {
    const totalTenths = Math.max(0, Math.floor((Number(milliseconds) || 0) / 100));
    const tenths = totalTenths % 10;
    const totalSeconds = Math.floor(totalTenths / 10);
    const seconds = totalSeconds % 60;
    const minutes = Math.floor(totalSeconds / 60) % 60;
    const hours = Math.floor(totalSeconds / 3600);
    return (hours > 0 ? hours + ":" + pad2(minutes) : String(minutes)) + ":" + pad2(seconds) + "." + tenths;
}

function formatDeltaTenths(deltaTenths) {
    if (deltaTenths === null || deltaTenths === undefined || !Number.isFinite(deltaTenths)) return "";
    const rounded = Math.round(deltaTenths);
    const sign = rounded < 0 ? "-" : "+";
    const absTenths = Math.abs(rounded);
    if (absTenths < 600) return sign + Math.floor(absTenths / 10) + "." + (absTenths % 10) + "s";
    return sign + formatStopwatch(absTenths * 100);
}

function createTimer(id, durationMs, name, nowMs, startRunning) {
    const now = Number.isFinite(Number(nowMs)) ? Number(nowMs) : Date.now();
    const length = Math.max(1000, Math.round(Number(durationMs) || 0));
    const running = startRunning !== false;
    return {
        id: String(id),
        name: typeof name === "string" ? name.trim() : "",
        durationMs: length,
        running: running,
        ended: false,
        alerted: false,
        endAtMs: running ? now + length : 0,
        remainingMs: length,
        createdAtMs: now
    };
}

function timerRemainingMs(item, nowMs) {
    if (!item || item.ended) return 0;
    if (item.running) return Math.max(0, Number(item.endAtMs || 0) - nowMs);
    return Math.max(0, Number(item.remainingMs || 0));
}

function timerProgress(item, nowMs) {
    if (!item) return 0;
    if (item.ended) return 1;
    if (!(item.durationMs > 0)) return 0;
    return Math.max(0, Math.min(1, 1 - timerRemainingMs(item, nowMs) / item.durationMs));
}

// Running timers sort first by shortest remaining time, then paused timers by
// shortest remaining time, then ended timers (most recently ended first).
function sortTimers(list, nowMs) {
    const items = Array.isArray(list) ? list.slice() : [];
    items.sort(function(first, second) {
        const groupA = first.ended ? 2 : (first.running ? 0 : 1);
        const groupB = second.ended ? 2 : (second.running ? 0 : 1);
        if (groupA !== groupB) return groupA - groupB;
        if (groupA < 2) {
            const diff = timerRemainingMs(first, nowMs) - timerRemainingMs(second, nowMs);
            if (Math.abs(diff) > 0.5) return diff;
            if ((first.createdAtMs || 0) !== (second.createdAtMs || 0)) return (first.createdAtMs || 0) - (second.createdAtMs || 0);
            return String(first.id).localeCompare(String(second.id));
        }
        const endedDiff = (second.endAtMs || second.createdAtMs || 0) - (first.endAtMs || first.createdAtMs || 0);
        return Math.abs(endedDiff) > 0.5 ? endedDiff : String(first.id).localeCompare(String(second.id));
    });
    return items;
}

function advanceTimers(list, nowMs) {
    const next = [], newlyEnded = [];
    let changed = false;
    const items = Array.isArray(list) ? list : [];
    for (let index = 0; index < items.length; index += 1) {
        const entry = items[index];
        if (!entry) continue;
        if (entry.running && !entry.ended && timerRemainingMs(entry, nowMs) <= 0) {
            const updated = Object.assign({}, entry, {running: false, ended: true, remainingMs: 0, alerted: true});
            next.push(updated);
            if (!entry.alerted) newlyEnded.push(updated);
            changed = true;
        } else {
            next.push(entry);
        }
    }
    return {timers: sortTimers(next, nowMs), newlyEnded: newlyEnded, changed: changed};
}

function emptyStopwatch() {
    return {running: false, paused: false, startedAtMs: 0, bankedMs: 0, laps: []};
}

function stopwatchElapsedMs(stopwatch, nowMs) {
    if (!stopwatch) return 0;
    const banked = Math.max(0, Number(stopwatch.bankedMs || 0));
    return !stopwatch.running ? banked : banked + Math.max(0, nowMs - Number(stopwatch.startedAtMs || nowMs));
}

function stopwatchProgress(stopwatch, nowMs) {
    return (stopwatchElapsedMs(stopwatch, nowMs) % 60000) / 60000;
}

// Laps newest first, each with split, total, and difference vs the previous lap.
function computeLapRows(stopwatch) {
    const source = stopwatch && Array.isArray(stopwatch.laps) ? stopwatch.laps : [];
    const rows = [];
    let previousTenths = null;
    for (let index = 0; index < source.length; index += 1) {
        const lap = source[index];
        const splitMs = Math.max(0, Number(lap && lap.splitMs || 0));
        const totalMs = Math.max(0, Number(lap && lap.totalMs || 0));
        const splitTenths = Math.floor(splitMs / 100);
        const deltaTenths = previousTenths === null ? null : splitTenths - previousTenths;
        const trend = deltaTenths === null ? "first" : (deltaTenths < 0 ? "faster" : (deltaTenths > 0 ? "slower" : "same"));
        rows.push({
            number: index + 1, splitMs: splitMs, totalMs: totalMs,
            deltaTenths: deltaTenths, deltaText: formatDeltaTenths(deltaTenths), trend: trend
        });
        previousTenths = splitTenths;
    }
    rows.reverse();
    return rows;
}

function emptyFocus() {
    return {active: false, running: false, paused: false, phase: "focus", rounds: 0, durationMs: 0, bankedMs: 0, startedAtMs: 0};
}

function focusElapsedMs(focus, nowMs) {
    if (!focus || !focus.active) return 0;
    const banked = Math.max(0, Number(focus.bankedMs || 0));
    return !focus.running ? banked : banked + Math.max(0, nowMs - Number(focus.startedAtMs || nowMs));
}

function focusRemainingMs(focus, nowMs) {
    return !focus || !focus.active ? 0 : Math.max(0, Number(focus.durationMs || 0) - focusElapsedMs(focus, nowMs));
}

function focusProgress(focus, nowMs) {
    return !focus || !focus.active || !(focus.durationMs > 0) ? 0 : Math.max(0, Math.min(1, focusElapsedMs(focus, nowMs) / focus.durationMs));
}

function timerActivity(entry, nowMs) {
    const left = timerRemainingMs(entry, nowMs);
    return {
        active: true, running: entry.running, paused: !entry.running,
        kind: "timer", page: "timers", timerId: entry.id, name: entry.name,
        durationMs: entry.durationMs, remainingMs: left,
        timeText: formatClock(left), progress: timerProgress(entry, nowMs), isBreak: false
    };
}

function focusActivity(focus, nowMs) {
    const left = focusRemainingMs(focus, nowMs);
    return {
        active: true, running: focus.running, paused: focus.paused,
        kind: "focus", page: "focus", timerId: "", name: "",
        durationMs: focus.durationMs || 0, remainingMs: left,
        timeText: formatClock(left), progress: focusProgress(focus, nowMs),
        isBreak: focus.phase === "break", rounds: focus.rounds || 0
    };
}

// Activity priority for the bar ring: countdown ending first, else a focus
// phase, else a running stopwatch (running activities beat paused ones).
function computeActivity(timers, focus, stopwatch, nowMs) {
    const sorted = sortTimers(timers, nowMs);
    let runningCountdown = null, pausedCountdown = null;
    for (let index = 0; index < sorted.length; index += 1) {
        const entry = sorted[index];
        if (entry.ended) continue;
        if (entry.running && !runningCountdown) { runningCountdown = entry; break; }
        if (!entry.running && !pausedCountdown) pausedCountdown = entry;
    }
    if (runningCountdown) return timerActivity(runningCountdown, nowMs);
    if (focus && focus.active && focus.running) return focusActivity(focus, nowMs);
    if (stopwatch && stopwatch.running) {
        const elapsed = stopwatchElapsedMs(stopwatch, nowMs);
        return {
            active: true, running: true, paused: false, kind: "stopwatch", page: "stopwatch",
            timerId: "", name: "", durationMs: 0, remainingMs: elapsed,
            timeText: formatStopwatch(elapsed), progress: stopwatchProgress(stopwatch, nowMs), isBreak: false
        };
    }
    if (pausedCountdown) return timerActivity(pausedCountdown, nowMs);
    if (focus && focus.active && focus.paused) return focusActivity(focus, nowMs);
    return {
        active: false, running: false, paused: false, kind: "", page: "timers",
        timerId: "", name: "", durationMs: 0, remainingMs: 0, timeText: "", progress: 0, isBreak: false
    };
}

function sanitizeTimer(entry, nowMs) {
    if (!entry || typeof entry !== "object") return null;
    const id = typeof entry.id === "string" && entry.id.length > 0 ? entry.id : "";
    const durationMs = Math.max(1000, Math.round(Number(entry.durationMs) || 0));
    if (!id || !(Number(entry.durationMs) > 0)) return null;
    const ended = entry.ended === true;
    const running = !ended && entry.running === true;
    return {
        id: id,
        name: typeof entry.name === "string" ? entry.name.trim() : "",
        durationMs: durationMs,
        running: running,
        ended: ended,
        alerted: entry.alerted === true || ended,
        endAtMs: running ? (Number(entry.endAtMs) || nowMs) : (Number(entry.endAtMs) || 0),
        remainingMs: ended ? 0 : Math.max(0, Math.min(durationMs, Number(entry.remainingMs) || durationMs)),
        createdAtMs: Number.isFinite(Number(entry.createdAtMs)) ? Number(entry.createdAtMs) : nowMs
    };
}

function sanitizeStopwatch(entry) {
    if (!entry || typeof entry !== "object") return emptyStopwatch();
    const running = entry.running === true;
    const paused = !running && entry.paused === true;
    const rawLaps = Array.isArray(entry.laps) ? entry.laps : [];
    const laps = [];
    for (let index = 0; index < rawLaps.length; index += 1) {
        const lap = rawLaps[index];
        if (lap && typeof lap === "object") {
            laps.push({splitMs: Math.max(0, Number(lap.splitMs) || 0), totalMs: Math.max(0, Number(lap.totalMs) || 0)});
        }
    }
    return {
        running: running, paused: paused,
        startedAtMs: running ? (Number(entry.startedAtMs) || 0) : 0,
        bankedMs: Math.max(0, Number(entry.bankedMs) || 0),
        laps: laps
    };
}

function sanitizeFocus(entry) {
    if (!entry || typeof entry !== "object" || entry.active !== true) return emptyFocus();
    const running = entry.running === true;
    const paused = !running && entry.paused === true;
    if (!running && !paused) return emptyFocus();
    return {
        active: true, running: running, paused: paused,
        phase: entry.phase === "break" ? "break" : "focus",
        rounds: clampInt(entry.rounds),
        breakMinutes: clampInt(entry.breakMinutes),
        durationMs: Math.max(1000, Math.round(Number(entry.durationMs) || 0)),
        bankedMs: Math.max(0, Number(entry.bankedMs) || 0),
        startedAtMs: running ? (Number(entry.startedAtMs) || 0) : 0
    };
}

function serializeState(timers, stopwatch, focus) {
    return {
        version: 1,
        timers: Array.isArray(timers) ? timers : [],
        stopwatch: stopwatch || emptyStopwatch(),
        focus: focus || emptyFocus()
    };
}

function restoreState(rawText, nowMs, breakMinutes) {
    const now = Number.isFinite(Number(nowMs)) ? Number(nowMs) : Date.now();
    let parsed = {};
    if (typeof rawText === "string" && rawText.trim().length > 0) {
        try {
            const candidate = JSON.parse(rawText);
            if (candidate && typeof candidate === "object") parsed = candidate;
        } catch (_ignored) {
            parsed = {};
        }
    }
    const configuredBreak = parsed.focus && Number(parsed.focus.breakMinutes) >= 1
        ? Number(parsed.focus.breakMinutes) : (Number(breakMinutes) || 5);
    const restMs = Math.max(1, configuredBreak) * 60000;
    const rawTimers = Array.isArray(parsed.timers) ? parsed.timers : [];
    const cleanedTimers = [];
    for (let index = 0; index < rawTimers.length; index += 1) {
        const sanitized = sanitizeTimer(rawTimers[index], now);
        if (sanitized) cleanedTimers.push(sanitized);
    }
    const timerStep = advanceTimers(cleanedTimers, now);
    const stopwatch = sanitizeStopwatch(parsed.stopwatch);
    let focus = sanitizeFocus(parsed.focus);
    let focusEvent = "";
    if (focus.active && focus.running) {
        const elapsed = focusElapsedMs(focus, now);
        if (elapsed >= focus.durationMs) {
            if (focus.phase === "focus") {
                const overshoot = elapsed - focus.durationMs;
                const nextRounds = focus.rounds + 1;
                if (overshoot < restMs) {
                    focus = {active: true, running: true, paused: false, phase: "break", rounds: nextRounds, durationMs: restMs, bankedMs: 0, startedAtMs: now - overshoot};
                    focusEvent = "break-started";
                } else {
                    focus = Object.assign(emptyFocus(), {rounds: nextRounds});
                    focusEvent = "break-finished";
                }
            } else {
                focus = Object.assign(emptyFocus(), {rounds: focus.rounds});
                focusEvent = "break-finished";
            }
        }
    }
    return {
        timers: timerStep.timers,
        newlyEndedTimers: timerStep.newlyEnded,
        stopwatch: stopwatch,
        focus: focus,
        focusEvent: focusEvent,
        needsSave: timerStep.changed || focusEvent !== ""
    };
}
