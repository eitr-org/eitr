.pragma library

function parseFrame(line) {
    var fields = String(line).trim().replace(/;$/, "").split(";");
    if (fields.length !== 4 || fields.some(field => !/^\d+$/.test(field))) return null;
    return fields.map(field => Math.min(100, Number(field)) / 100);
}

function height(level) {
    return 3 + Math.max(0, Math.min(1, level)) * 11;
}
