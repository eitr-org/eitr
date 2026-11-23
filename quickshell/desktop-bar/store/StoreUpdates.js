.pragma library

function next(catalog) {
    if (!catalog.updateQueue.length) return;
    const item = catalog.updateQueue[0];
    catalog.updateQueue = catalog.updateQueue.slice(1);
    catalog.kind = item.storeKind;
    if (catalog.capabilities.useOnClick)
        catalog.act("update", {id: item.id}, () => next(catalog));
    else
        catalog.prepareReview({id: item.id, updating: true}, true);
}

function items(store, kinds, cache) {
    const result = [];
    for (const kind of kinds) {
        for (const item of (store[kind.id + ":installed"] || {}).items || []) {
            if (((cache[kind.id] || {})[item.id] || 0) > 0)
                result.push(Object.assign({}, item, {storeKind: kind.id}));
        }
    }
    return result;
}

function check(catalog, owner) {
    if (catalog.updateCheck.pending || catalog.busy || catalog.nativeReviewing) return;
    const opening = catalog.opening;
    const kinds = catalog.kinds.filter(entry => entry.capabilities.update);
    catalog.updateCheck = {pending: kinds.length, date: catalog.updateCheck.date, error: ""};
    for (const kind of kinds) {
        catalog.transport("check", {kind: kind.id}, function(failure, data) {
            if (!catalog.opened || catalog.opening !== opening) return;
            const error = failure || data.error || catalog.updateCheck.error;
            if (!failure && !data.error) {
                catalog.updateCache = Object.assign({}, catalog.updateCache, {[kind.id]: data.updates || {}});
                if (catalog.kind === kind.id) catalog.updates = catalog.updateCache[kind.id];
            }
            const pending = catalog.updateCheck.pending - 1;
            catalog.updateCheck = {pending: pending, date: pending ? catalog.updateCheck.date : new Date(), error: error};
        }, owner);
    }
}
