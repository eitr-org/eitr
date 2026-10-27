.pragma library

function resample(values, count) {
    if (!values.length) return Array(count).fill(0);
    const result = [];
    for (let index = 0; index < count; index++) {
        const start = index * values.length / count;
        const end = (index + 1) * values.length / count;
        let sum = 0;
        for (let source = Math.floor(start); source < Math.ceil(end); source++)
            sum += values[Math.min(source, values.length - 1)] * (Math.min(end, source + 1) - Math.max(start, source));
        result.push(Math.max(0, Math.min(1, sum / (end - start))));
    }
    return result;
}

function frame(line) {
    const fields = String(line).trim().replace(/;$/, "").split(";");
    if (fields.length < 4 || fields.length > 128 || fields.some(field => !/^\d+$/.test(field))) return null;
    return fields.map(field => Math.min(100, Number(field)) / 100);
}

function count(value, minimum, maximum) {
    return Number.isFinite(value) ? Math.max(minimum, Math.min(maximum, Math.round(value))) : minimum;
}

function configuration(consumers) {
    let bars = 4, fps = 1;
    let smoothing = consumers.length > 0;
    for (const consumer of consumers) {
        bars = Math.max(bars, count(consumer.bars, 4, 128));
        fps = Math.max(fps, count(consumer.frameRate, 1, 60));
        smoothing = smoothing && consumer.plugin && consumer.smoothing;
    }
    return {bars: bars, fps: fps, smoothing: !!smoothing};
}

function smooth(values, previous) {
    return values.map((value, index) => previous.length === values.length
        ? previous[index] + (value - previous[index]) * 0.5 : value);
}
