.pragma library

// Shared screen-edge silhouette for Tabs and Centered, in edge-local coordinates.
function outline(edge, length, depth, strip, bendRound, spans) {
    var slope = depth - strip;
    function point(axis, inward) {
        if (edge === "bottom") return axis + " " + (depth - inward);
        if (edge === "left") return inward + " " + axis;
        if (edge === "right") return (depth - inward) + " " + axis;
        return axis + " " + inward;
    }
    // Unite overlapping slopes on small screens without self intersections.
    var merged = [];
    for (var span of spans) {
        var last = merged[merged.length - 1];
        if (last && span[0] - last[1] <= 2 * slope) last[1] = Math.max(last[1], span[1]);
        else merged.push(span.slice());
    }
    var path = "M " + point(0, 0) + " L " + point(0, merged.length && merged[0][0] === 0 ? depth : strip);
    for (var tab of merged) {
        var start = Math.max(0, tab[0]);
        var end = Math.min(length, tab[1]);
        // Rounded bends keep the 45° trapezoid: the straight edges stop
        // `round` before each bend and a quadratic curve joins them.
        var round = Math.min(bendRound, slope / 2);
        var diagonal = round * 0.7071;
        if (start > 0) {
            path += " L " + point(start - slope - round, strip)
                + " Q " + point(start - slope, strip) + " " + point(start - slope + diagonal, strip + diagonal)
                + " L " + point(start - diagonal, depth - diagonal)
                + " Q " + point(start, depth) + " " + point(start + round, depth);
        }
        if (end < length) {
            path += " L " + point(end - round, depth)
                + " Q " + point(end, depth) + " " + point(end + diagonal, depth - diagonal)
                + " L " + point(end + slope - diagonal, strip + diagonal)
                + " Q " + point(end + slope, strip) + " " + point(end + slope + round, strip);
        } else path += " L " + point(length, depth);
    }
    return path + " L " + point(length, 0) + " Z";
}

// Leading boundary of the rounded slope at a given inward depth.
function boundary(start, depth, bendRound, inward) {
    var round = Math.min(bendRound, depth / 2);
    var diagonal = round * 0.7071;
    if (diagonal > 0 && inward < diagonal) {
        var first = Math.sqrt(Math.max(0, inward) / diagonal);
        return start - depth - round * (1 - first) * (1 - first) + diagonal * first * first;
    }
    if (diagonal > 0 && inward > depth - diagonal) {
        var last = 1 - Math.sqrt(Math.max(0, depth - inward) / diagonal);
        return start - diagonal * (1 - last) * (1 - last) + round * last * last;
    }
    return start - depth + inward;
}
