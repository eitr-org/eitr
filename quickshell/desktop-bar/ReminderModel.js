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
    return forMonth(items, day.getFullYear(), day.getMonth()).filter(function(item) {
        const date = new Date(item.due * 1000);
        return date.getFullYear() === day.getFullYear() && date.getMonth() === day.getMonth()
            && date.getDate() === day.getDate();
    });
}

function occurrence(item, index) {
    const anchor = new Date(item.repeat_anchor);
    const rule = item.repeat;
    const step = rule.interval || 1;
    const date = new Date(anchor.getTime());
    if (rule.frequency === "daily") date.setDate(anchor.getDate() + index * step);
    else if (rule.frequency === "weekly") {
        const weekday = (anchor.getDay() + 6) % 7;
        const days = (rule.weekdays || [weekday]).slice().sort();
        const first = days.filter(function(day) { return day > weekday; });
        let offset = 0;
        if (index > 0 && index <= first.length) offset = first[index - 1] - weekday;
        else if (index > 0) {
            const position = index - first.length - 1;
            offset = (Math.floor(position / days.length) + 1) * step * 7 + days[position % days.length] - weekday;
        }
        date.setDate(anchor.getDate() + offset);
    } else {
        const months = index * step * (rule.frequency === "yearly" ? 12 : 1);
        date.setDate(1);
        date.setMonth(anchor.getMonth() + months);
        const last = new Date(date.getFullYear(), date.getMonth() + 1, 0).getDate();
        date.setDate(Math.min(rule.day_of_month || anchor.getDate(), last));
    }
    return date;
}

function forMonth(items, year, month) {
    const start = new Date(year, month, 1);
    const end = new Date(year, month + 1, 1);
    const result = [];
    items.forEach(function(item) {
        if (!item.repeat || !item.repeat_anchor) {
            if (item.due * 1000 >= start && item.due * 1000 < end) result.push(item);
            return;
        }
        const rule = item.repeat;
        for (let index = item.repeat_index || 0; index < (rule.count || Infinity); index++) {
            const date = occurrence(item, index);
            if (!Number.isFinite(date.getTime()) || date >= end) break;
            const until = rule.until ? new Date(rule.until + "T23:59:59") : null;
            if (until && date > until) break;
            if (date >= start) result.push(Object.assign({}, item, {due: date.getTime() / 1000}));
        }
    });
    return result.sort(function(first, second) { return first.due - second.due; });
}
