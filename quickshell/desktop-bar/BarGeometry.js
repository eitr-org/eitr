.pragma library

function screenPoint(point, edge, screenWidth, screenHeight, windowWidth, windowHeight) {
    return {
        x: point.x + (edge === "right" ? screenWidth - windowWidth : 0),
        y: point.y + (edge === "bottom" ? screenHeight - windowHeight : 0)
    };
}

function nearestEdge(point, width, height) {
    var x = Math.max(0, Math.min(1, point.x / Math.max(1, width)));
    var y = Math.max(0, Math.min(1, point.y / Math.max(1, height)));
    var distances = {top: y, bottom: 1 - y, left: x, right: 1 - x};
    return Object.keys(distances).reduce((best, edge) => distances[edge] < distances[best] ? edge : best);
}
