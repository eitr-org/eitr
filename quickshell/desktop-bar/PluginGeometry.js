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

function scale(geometry, bounds, minimumWidth, minimumHeight, factor) {
    const ratio = geometry.width / geometry.height;
    const maximum = Math.min(bounds.width, bounds.height * ratio);
    const minimum = Math.min(maximum, Math.max(minimumWidth, minimumHeight * ratio));
    const width = Math.max(minimum, Math.min(maximum, factor === 0 ? maximum : geometry.width * factor));
    return fit({x: geometry.x + (geometry.width - width) / 2,
        y: geometry.y + (geometry.height - width / ratio) / 2,
        width: width, height: width / ratio}, bounds, 1, 1, 1);
}

function delta(geometry, dx, dy, resize) {
    return {x: geometry.x + (resize ? 0 : dx), y: geometry.y + (resize ? 0 : dy),
        width: geometry.width + (resize ? dx : 0), height: geometry.height + (resize ? dy : 0)};
}
