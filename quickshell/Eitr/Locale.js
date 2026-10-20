.pragma library

function normalize(value) {
    const clean = String(value || "").trim().split(/[.@]/)[0].replace(/-/g, "_");
    if (!clean || /^(C|POSIX)$/i.test(clean) || !/^[a-z]{2,3}(?:_[a-z]{2}|_[0-9]{3})?$/i.test(clean)) return "en";
    const parts = clean.split("_");
    return parts[0].toLowerCase() + (parts.length > 1 ? "_" + parts[1].toUpperCase() : "");
}

function systemLocale(environment) {
    for (const name of ["LC_ALL", "LC_MESSAGES", "LANG"]) {
        if (String(environment[name] || "").trim()) return normalize(environment[name]);
    }
    return "en";
}

function candidates(locale) {
    const normalized = normalize(locale);
    const base = normalized.split("_")[0];
    return Array.from(new Set([normalized, base === "pt" ? "pt_BR" : base, "en"]));
}

function select(locale, supported) {
    return candidates(locale).find(candidate => Object.prototype.hasOwnProperty.call(supported, candidate)) || "en";
}

function translate(source, regional, base, values) {
    const own = (catalog) => Object.prototype.hasOwnProperty.call(catalog, source) && typeof catalog[source] === "string" && catalog[source].length ? catalog[source] : "";
    let translated = own(regional) || own(base) || source;
    // Replace in one pass so an argument containing %2 is never interpreted again.
    return translated.replace(/\{([a-zA-Z_][a-zA-Z0-9_]*)\}|%([1-9][0-9]*)/g, (placeholder, name, number) => {
        if (name) return Object.prototype.hasOwnProperty.call(values, name) ? String(values[name]) : placeholder;
        const index = Number(number) - 1;
        return index < values.length ? String(values[index]) : placeholder;
    });
}
