.pragma library

function clamp(width, height, diameter, zoom, offsetX, offsetY) {
    const scale = Math.max(diameter / width, diameter / height) * Math.max(1, Math.min(4, zoom));
    const limitX = Math.max(0, (width * scale - diameter) / 2);
    const limitY = Math.max(0, (height * scale - diameter) / 2);
    return {scale: scale, x: Math.max(-limitX, Math.min(limitX, offsetX)), y: Math.max(-limitY, Math.min(limitY, offsetY))};
}
function square(width, height, diameter, zoom, offsetX, offsetY) {
    const view = clamp(width, height, diameter, zoom, offsetX, offsetY);
    const size = diameter / view.scale;
    return {x: (width - size) / 2 - view.x / view.scale, y: (height - size) / 2 - view.y / view.scale, size: size};
}
