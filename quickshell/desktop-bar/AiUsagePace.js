.pragma library

function durationSeconds(window) {
    if (Number.isFinite(window.durationSeconds) && window.durationSeconds > 0)
        return window.durationSeconds;

    // Older snapshots and providers without duration metadata use these known buckets.
    const label = String(window.label || "").toLowerCase().trim();
    if (/(^|\s)weekly$/.test(label)) return 7 * 24 * 3600;
    if (/(^|\s)(5h window|session)$/.test(label)) return 5 * 3600;
    return 0;
}

function estimate(window, now) {
    const duration = durationSeconds(window);
    const remaining = window.reset - now;
    if (!duration || !Number.isFinite(now) || !Number.isFinite(window.reset)
        || remaining <= 0 || !Number.isFinite(window.used) || window.used < 0) return null;

    const elapsed = duration - remaining;
    if (elapsed < duration * 0.05) return null;

    const used = Math.min(window.used, 100);
    const difference = used - 100 * elapsed / duration;
    const trend = difference > 5 ? "ahead" : difference < -5 ? "behind" : "even";
    const secondsToFull = trend === "ahead" && used < 100 ? elapsed * (100 - used) / used : 0;
    return {
        trend: trend,
        minutesToFull: secondsToFull > 0 && secondsToFull < remaining
            ? Math.max(1, Math.round(secondsToFull / 60)) : null
    };
}
