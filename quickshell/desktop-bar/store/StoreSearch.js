.pragma library

function matches(item, query) {
    const words = query.trim().toLowerCase().split(/\s+/).filter(word => word);
    const text = [item.name, item.id, item.description, item.author, item.maintainer].filter(value => value).join(" ").toLowerCase();
    return words.every(word => text.includes(word));
}

function rows(store, kinds, tab, query, filter) {
    const result = [];
    for (const kind of kinds) {
        const sources = tab === "installed" ? ["installed"] : kind.sources;
        for (const source of sources) {
            for (const item of (store[kind.id + ":" + source] || {}).items || []) {
                if (!matches(item, query)) continue;
                const official = ["builtin", "official"].includes(item.kind);
                if (tab !== "installed" && filter !== "all" && (filter === "official") !== official) continue;
                if (result.some(row => row.storeKind === kind.id && row.id === item.id)) continue;
                result.push(Object.assign({}, item, {storeKind: kind.id}));
            }
        }
    }
    return result;
}
