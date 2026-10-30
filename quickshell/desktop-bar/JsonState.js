.pragma library

// Panels refresh their data each time they open. Replacing a property with an
// equal but new object makes every list built from it rebuild, which stalls the
// opening animation, so callers only assign values whose content changed.
function changed(current, next) {
    return JSON.stringify(current) !== JSON.stringify(next);
}

// Schemas describe only fields the consumer needs; helpers may add other fields.
function matches(value, schema) {
    if (Array.isArray(schema))
        return Array.isArray(value) && value.every(item => matches(item, schema[0]));
    if (schema && typeof schema === "object")
        return value !== null && typeof value === "object" && !Array.isArray(value)
            && Object.keys(schema).every(key => matches(value[key], schema[key]));
    if (schema === "array") return Array.isArray(value);
    if (schema === "object") return value !== null && typeof value === "object" && !Array.isArray(value);
    return typeof value === schema;
}

// A failed refresh is a state of its own; callers clear the previous snapshot.
function parse(text, exitCode, fields) {
    try {
        if (exitCode !== 0) throw new Error("Helper failed (" + exitCode + ")");
        const data = JSON.parse(text);
        if (!data || typeof data !== "object" || Array.isArray(data))
            throw new Error("Expected an object");
        if (data.error) throw new Error(String(data.error));
        for (const key of Object.keys(fields)) {
            if (!matches(data[key], fields[key]))
                throw new Error("Invalid field: " + key);
        }
        return {ok: true, data: data, error: ""};
    } catch (error) {
        return {ok: false, data: null, error: String(error)};
    }
}
