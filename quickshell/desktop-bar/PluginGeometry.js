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

// A turned widget's clickable area as horizontal strips inside its box (box coordinates):
// input regions are straight rectangles, so strips follow the turned shape and leave the
// box's empty corners to the desktop underneath. Unturned widgets get one rectangle.
function rotatedStrips(width, height, degrees, boxWidth, boxHeight, count) {
    if (!((degrees || 0) % 180)) return [{x: Math.round((boxWidth - width) / 2), y: Math.round((boxHeight - height) / 2),
        width: Math.round(width), height: Math.round(height)}];
    const radians = degrees * Math.PI / 180, cosine = Math.cos(radians), sine = Math.sin(radians);
    const centerX = boxWidth / 2, centerY = boxHeight / 2;
    const corners = [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(corner => {
        const x = corner[0] * width / 2, y = corner[1] * height / 2;
        return {x: centerX + x * cosine - y * sine, y: centerY + x * sine + y * cosine};
    });
    // Where a horizontal line crosses the turned rectangle's edges.
    function span(lineY) {
        const crossings = [];
        for (let index = 0; index < 4; index++) {
            const start = corners[index], end = corners[(index + 1) % 4];
            if ((start.y <= lineY && end.y >= lineY) || (end.y <= lineY && start.y >= lineY)) {
                const share = end.y === start.y ? 0 : (lineY - start.y) / (end.y - start.y);
                crossings.push(start.x + share * (end.x - start.x));
            }
        }
        return crossings.length ? [Math.min(...crossings), Math.max(...crossings)] : null;
    }
    const strips = [];
    const step = boxHeight / count;
    for (let row = 0; row < count; row++) {
        const top = row * step, bottom = top + step;
        const spans = [span(top), span(bottom), span((top + bottom) / 2)].filter(found => found !== null);
        if (!spans.length) continue;
        const left = Math.max(0, Math.floor(Math.min(...spans.map(found => found[0]))));
        const right = Math.min(boxWidth, Math.ceil(Math.max(...spans.map(found => found[1]))));
        strips.push({x: left, y: Math.floor(top), width: Math.max(1, right - left), height: Math.ceil(bottom) - Math.floor(top)});
    }
    return strips;
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
