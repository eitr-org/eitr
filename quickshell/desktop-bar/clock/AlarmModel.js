.pragma library

function splitClock(clock, twelveHour) {
    const [hour, minute] = clock.split(":");
    const numericHour = Number(hour);
    return {text: twelveHour ? (numericHour % 12 || 12) + ":" + minute : clock,
            period: numericHour < 12 ? "am" : "pm"};
}

function parseClock(text, twelveHour, period) {
    const match = /^(\d{1,2}):([0-5]\d)$/.exec(text.trim());
    if (!match) return "";
    let hour = Number(match[1]);
    if (twelveHour) {
        if (hour < 1 || hour > 12) return "";
        hour = hour % 12 + (period === "pm" ? 12 : 0);
    } else if (hour > 23) {
        return "";
    }
    return String(hour).padStart(2, "0") + ":" + match[2];
}

function ring(items, now) {
    return items.filter(item => item.alarm.ringUntil * 1000 > now)
        .sort((first, second) => first.alarm.ringUntil - second.alarm.ringUntil)[0] || null;
}

function displayTime(clock, twelveHour, locale) {
    const time = splitClock(clock, twelveHour);
    if (!twelveHour) return time.text;
    return time.text + " " + (time.period === "am" ? locale.amText : locale.pmText);
}
