.pragma library

function reconcile(available, selected) {
    var enabled = Array.isArray(selected) ? selected : [];
    var result = available.filter(function(name) { return enabled.indexOf(name) !== -1; });
    return result.length || !available.length ? result : [available[0]];
}

function toggle(available, selected, name) {
    var current = reconcile(available, selected);
    if (available.indexOf(name) === -1) return current;
    if (current.indexOf(name) === -1) return reconcile(available, current.concat([name]));
    return current.length === 1 ? current : current.filter(function(providerName) { return providerName !== name; });
}
