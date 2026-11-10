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

// The screen-aligned box a widget rotated about its centre covers, moved inside bounds
// when it would cross them, so its layer surface never clips the rotated content.
function rotatedBox(geometry, degrees, bounds) {
    const radians = (degrees || 0) * Math.PI / 180;
    const cosine = Math.abs(Math.cos(radians)), sine = Math.abs(Math.sin(radians));
    const width = Math.ceil(geometry.width * cosine + geometry.height * sine - 1e-9);
    const height = Math.ceil(geometry.width * sine + geometry.height * cosine - 1e-9);
    const centerX = geometry.x + geometry.width / 2, centerY = geometry.y + geometry.height / 2;
    function inside(start, size, low, room) { return size >= room ? low : Math.max(low, Math.min(low + room - size, start)); }
    return {x: Math.round(inside(centerX - width / 2, width, bounds.x, bounds.width)),
        y: Math.round(inside(centerY - height / 2, height, bounds.y, bounds.height)),
        width: width, height: height};
}

// Whole degrees 0-359; within 3 degrees of a quarter turn the angle snaps to it.
function snapRotation(degrees) {
    const value = ((Math.round(degrees) % 360) + 360) % 360;
    for (const quarter of [0, 90, 180, 270, 360])
        if (Math.abs(value - quarter) <= 3) return quarter % 360;
    return value;
}

// Keeps the size and moves the box inside a screen of the given size (logical pixels).
function clampToScreen(geometry, screenWidth, screenHeight) {
    const width = Math.max(24, Math.min(geometry.width, screenWidth)), height = Math.max(24, Math.min(geometry.height, screenHeight));
    return {x: Math.round(Math.max(0, Math.min(screenWidth - width, geometry.x))),
        y: Math.round(Math.max(0, Math.min(screenHeight - height, geometry.y))),
        width: Math.round(width), height: Math.round(height)};
}
