.pragma library

// Pure helpers for ObsMenu's serialized recording-option writes.

function withOption(options, key, enabled) {
    var next = Object.assign({}, options);
    next[key] = Object.assign({}, next[key], {enabled: enabled});
    return next;
}

// Later changes to the same option replace earlier unsent ones.
function enqueue(pending, key, enabled) {
    var next = Object.assign({}, pending);
    next[key] = enabled;
    return next;
}

// Returns {key, enabled, remaining} for the oldest pending change, or null.
function takeNext(pending) {
    var keys = Object.keys(pending || {});
    if (!keys.length) return null;
    var key = keys[0];
    var remaining = Object.assign({}, pending);
    delete remaining[key];
    return {key: key, enabled: pending[key], remaining: remaining};
}

function optionArguments(key, enabled) {
    return ["set-option", key, enabled ? "true" : "false"];
}
