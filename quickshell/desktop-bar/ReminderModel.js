.pragma library

function parse(text) {
    try {
        const values = JSON.parse(text);
        if (!Array.isArray(values)) return [];
        return values.filter(function(item) {
            return item && typeof item.id === "string" && typeof item.text === "string"
                && typeof item.due === "number" && Number.isFinite(item.due);
        }).sort(function(first, second) { return first.due - second.due; });
    } catch (error) { return []; }
}

function forDay(items, day) {
    return items.filter(function(item) {
        const date = new Date(item.due * 1000);
        return date.getFullYear() === day.getFullYear() && date.getMonth() === day.getMonth()
            && date.getDate() === day.getDate();
    });
}
