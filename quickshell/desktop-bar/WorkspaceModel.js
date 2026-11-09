.pragma library

function ceiling(workspaces, focusedId) {
    var highest = Math.max(5, Number(focusedId) || 0);
    for (var workspace of workspaces) highest = Math.max(highest, Number(workspace.id) || 0);
    return Math.min(10, highest);
}

function occupied(toplevels, rows) {
    var groups = {};
    for (var window of toplevels) {
        var id = window.workspace ? window.workspace.id : 0;
        var info = window.lastIpcObject || {};
        if (!Number.isInteger(id) || id < 1 || (rows ? !rows.some(row => row.id === id) : id > 10) || info.mapped === false || info.hidden === true) continue;
        if (!groups[id]) groups[id] = {id: id, windows: [], monitorName: window.monitor ? window.monitor.name : "", number: rows ? rows.find(row => row.id === id).number : id};
        groups[id].windows.push(window);
    }
    return Object.keys(groups).map(key => groups[key]).sort((first, second) => first.id - second.id);
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

// Mirrors eitr_workspaces.assignments; exhaustive parity tests cover every count.
function assignments(monitors, primary, mode, count) {
    var ordered = monitors.filter(monitor => !monitor.disabled).slice().sort((first, second) =>
        (first.name !== primary) - (second.name !== primary) || (first.x || 0) - (second.x || 0) || first.name.localeCompare(second.name));
    var rows = [], start = 1;
    ordered.forEach((monitor, slot) => {
        var length = mode === "shared" ? count : Math.floor(count / ordered.length) + (slot < count % ordered.length ? 1 : 0);
        for (var offset = 0; offset < length; offset++) {
            var number = mode === "shared" ? offset + 1 : start + offset;
            rows.push({id: mode === "shared" ? slot * 10 + number : number, number: number, monitor: monitor.name, position: offset + 1});
        }
        start += length;
    });
    return rows;
}

function visibleRows(rows, monitor, shown, occupiedIds, activeId) {
    var local = rows.filter(row => row.monitor === monitor);
    var highest = Math.min(shown, local.length);
    for (var row of local) {
        if (row.id === activeId || occupiedIds.includes(row.id)) highest = Math.max(highest, row.position);
    }
    return local.slice(0, highest);
}

function navigationCommand(number, monitor, script) {
    if (!Number.isInteger(number) || number < 1 || number > 10) return [];
    return ["python3", script, "focus", String(number), monitor || ""];
}
