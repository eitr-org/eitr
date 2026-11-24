.pragma library

function matches(item, query) {
    const words = query.trim().toLowerCase().split(/\s+/).filter(word => word);
    const text = [item.name, item.id, item.description, item.author, item.maintainer].filter(value => value).join(" ").toLowerCase();
    return words.every(word => text.includes(word));
}

function filters(item, definition, source, tone, values) {
    const official = ["builtin", "official"].includes(item.kind);
    if (source === "official" && !official) return false;
    if (source === "community" && item.kind !== "community") return false;
    return definition.filters.every(group => {
        const selection = group.id === "tone" ? tone : values[definition.id + ":" + group.id] || (group.multiple ? [] : "all");
        const selected = group.multiple ? selection : [selection];
        return selected.every(identifier => {
            const option = group.options.find(entry => entry.id === identifier);
            if (!option) return false;
            if (!option.path) return true;
            const value = option.path.split(".").reduce((current, field) => current && typeof current === "object" ? current[field] : undefined, item);
            if (option.equals !== undefined) return value === option.equals;
            return Array.isArray(value) ? value.length > 0 : !!value;
        });
    });
}

function sorted(items, order) {
    const direction = order === "name-descending" ? -1 : 1;
    return items.slice().sort((first, second) => {
        if (order === "creation-date") {
            const firstDate = Number.isFinite(first.createdAt) && first.createdAt > 0 ? first.createdAt : -Infinity;
            const secondDate = Number.isFinite(second.createdAt) && second.createdAt > 0 ? second.createdAt : -Infinity;
            if (firstDate !== secondDate) return secondDate - firstDate;
        }
        return direction * String(first.name || first.id || "").localeCompare(
            String(second.name || second.id || ""), undefined, {sensitivity: "base", numeric: true});
    });
}
