.pragma library

function ceiling(workspaces, focusedId) {
    var highest = Math.max(5, Number(focusedId) || 0);
    for (var workspace of workspaces) highest = Math.max(highest, Number(workspace.id) || 0);
    return Math.min(10, highest);
}

function occupied(toplevels) {
    var groups = {};
    for (var window of toplevels) {
        var id = window.workspace ? window.workspace.id : 0;
        var info = window.lastIpcObject || {};
        if (!Number.isInteger(id) || id < 1 || id > 10 || info.mapped === false || info.hidden === true) continue;
        if (!groups[id]) groups[id] = {id: id, windows: [], monitorName: window.monitor ? window.monitor.name : ""};
        groups[id].windows.push(window);
    }
    return Object.keys(groups).map(key => groups[key]).sort((a, b) => a.id - b.id);
}

// Normalize each workspace's window geometry without changing compositor state.
function bounds(windows) {
    var minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    for (var window of windows) {
        var info = window.lastIpcObject || {};
        var at = info.at || [0, 0], size = info.size || [800, 600];
        minX = Math.min(minX, at[0]); minY = Math.min(minY, at[1]);
        maxX = Math.max(maxX, at[0] + Math.max(1, size[0]));
        maxY = Math.max(maxY, at[1] + Math.max(1, size[1]));
    }
    return {x: isFinite(minX) ? minX : 0, y: isFinite(minY) ? minY : 0,
        width: Math.max(1, isFinite(maxX - minX) ? maxX - minX : 1),
        height: Math.max(1, isFinite(maxY - minY) ? maxY - minY : 1)};
}

function frame(workspace) {
    var monitor = workspace.windows.length ? workspace.windows[0].monitor : null;
    var info = monitor ? monitor.lastIpcObject || {} : {};
    var scale = Number(info.scale || (monitor && monitor.scale)) || 1;
    var width = Number(info.width || (monitor && monitor.width)) || 0;
    var height = Number(info.height || (monitor && monitor.height)) || 0;
    if (width > 0 && height > 0) {
        if ((Number(info.transform) || 0) % 2) { var swap = width; width = height; height = swap; }
        return {x: Number(info.x) || 0, y: Number(info.y) || 0, width: width / scale, height: height / scale};
    }
    return bounds(workspace.windows);
}

function selection(index, direction, columns, count) {
    if (!count) return -1;
    var delta = direction === "left" ? -1 : direction === "right" ? 1 : direction === "up" ? -columns : columns;
    return Math.max(0, Math.min(count - 1, index + delta));
}

// argv for focusing a numbered workspace; shared by bar markers and Overview.
function focusCommand(id) {
    var number = Number(id);
    if (!Number.isInteger(number) || number < 1 || number > 10) return [];
    return ["hyprctl", "dispatch", "hl.dsp.focus({ workspace = " + number + " })"];
}
