.pragma library

function fit(geometry, bounds, minimumWidth, minimumHeight, grid) {
    const step = Math.max(1, grid);
    function snap(value) { return Math.round(value / step) * step; }
    const width = Math.min(bounds.width, Math.max(minimumWidth, snap(geometry.width)));
    const height = Math.min(bounds.height, Math.max(minimumHeight, snap(geometry.height)));
    return {x: Math.round(Math.max(bounds.x, Math.min(bounds.x + bounds.width - width, snap(geometry.x)))),
        y: Math.round(Math.max(bounds.y, Math.min(bounds.y + bounds.height - height, snap(geometry.y)))),
        width: Math.round(width), height: Math.round(height)};
}
