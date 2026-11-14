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
