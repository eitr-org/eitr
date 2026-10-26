.pragma library

// Panels refresh their data each time they open. Replacing a property with an
// equal but new object makes every list built from it rebuild, which stalls the
// opening animation, so callers only assign values whose content changed.
function changed(current, next) {
    return JSON.stringify(current) !== JSON.stringify(next);
}
