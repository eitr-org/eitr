.pragma library

function restore(settings) {
    return settings && settings.version === 2 && Array.isArray(settings.foldedProviders)
        ? settings.foldedProviders : [];
}

function reconcile(available, folded) {
    var collapsed = Array.isArray(folded) ? folded : [];
    return available.filter(function(name) { return collapsed.indexOf(name) !== -1; });
}

function toggle(available, folded, name) {
    var current = reconcile(available, folded);
    if (available.indexOf(name) === -1) return current;
    return current.indexOf(name) === -1
        ? reconcile(available, current.concat([name]))
        : current.filter(function(providerName) { return providerName !== name; });
}
