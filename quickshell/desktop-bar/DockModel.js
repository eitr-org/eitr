.pragma library

function desktopId(value) {
    return String(value || "").replace(/\.desktop$/i, "").toLowerCase();
}

// Chromium-family --app windows are named <browser>-<site>-<profile>; web app
// entries record Chrome's spelling, so compare without the browser prefix.
var webAppClass = /^(brave-browser|chromium|chrome|brave|msedge|vivaldi)-(.+_.*-[^-]+)$/i;
function webAppKey(value) {
    var match = webAppClass.exec(String(value || ""));
    return match ? match[2].toLowerCase() : "";
}

// Eitr's own task and menu terminals (classes from hyprland.lua and
// walker/bin/menu-path/kitty) have no desktop entry; they share one Eitr icon.
var eitrTerminalClass = /^(eitr-.+|(fifs?|cloud|about)-terminal|system-(cleanup|check|mirrors))$/;

function eitrTerminal(appClass) {
    return eitrTerminalClass.test(String(appClass || ""));
}

function movePin(pins, id, position, keep) {
    var result = pins.filter(pin => desktopId(pin) !== desktopId(id));
    if (keep && id) result.splice(Math.max(0, Math.min(position, result.length)), 0, id);
    return result;
}

function dragPins(pins, entry, axis) {
    var boundary = pins.length ? pins.length * 42 + 3 : 21;
    var keep = axis < boundary;
    var position = Math.max(0, Math.floor((axis + 3) / 42));
    return movePin(pins, entry.desktopId, position, keep);
}

function orderWithPins(entries, pins) {
    var ordered = pins.map(pin => entries.find(entry => desktopId(entry.desktopId || entry.appClass) === desktopId(pin)))
        .filter(entry => !!entry);
    return ordered.concat(entries.filter(entry => !ordered.some(pin => pin.id === entry.id)));
}

function groups(clients, workspaceId, pinnedEntries, application) {
    var entries = [];
    var byClass = Object.create(null);
    function entryFor(appClass, pinned) {
        var app = application ? application(appClass) : null;
        var key = desktopId(app ? app.id : eitrTerminal(appClass) ? "eitr-terminal" : appClass);
        if (!byClass[key]) {
            byClass[key] = {id: key, desktopId: app ? app.id : "", appClass: appClass, pinned: !!pinned,
                windows: [], recent: null, onCurrentWorkspace: false};
            entries.push(byClass[key]);
        }
        return byClass[key];
    }
    for (var pinned of pinnedEntries || []) entryFor(typeof pinned === "string" ? pinned : pinned.appClass, true);
    // Preserve Hyprland's client order; focus history selects the activation target only.
    for (var client of clients) {
        if (client.mapped === false || !client.address) continue;
        var entry = entryFor(client.class || client.initialClass || client.address, false);
        entry.windows.push(client);
        if (client.workspace && client.workspace.id === workspaceId) entry.onCurrentWorkspace = true;
        var rank = client.focusHistoryID >= 0 ? client.focusHistoryID : Infinity;
        var previous = entry.recent && entry.recent.focusHistoryID >= 0 ? entry.recent.focusHistoryID : Infinity;
        if (!entry.recent || rank < previous) entry.recent = client;
    }
    return entries;
}

// Clicking an app focuses its most recent window; when that window already has
// focus, the click moves on to the app's next window, in Hyprland's order.
function activationTarget(entry) {
    if (!entry.recent) return null;
    if (entry.recent.focusHistoryID !== 0 || entry.windows.length < 2) return entry.recent;
    return entry.windows[(entry.windows.indexOf(entry.recent) + 1) % entry.windows.length];
}

// The hyprctl call that focuses or closes one window. Hyprland's Lua config only
// accepts hl.dsp calls; the old "focuswindow address:" form is silently ignored.
function windowCommand(action, address) {
    if (!/^0x[0-9a-fA-F]+$/.test(String(address))) return [];
    var call = action === "close" ? "hl.dsp.window.close" : "hl.dsp.focus";
    return ["hyprctl", "dispatch", call + '({ window = "address:' + address + '" })'];
}

function opposite(edge) {
    return {top: "bottom", bottom: "top", left: "right", right: "left"}[edge] || "bottom";
}

function normalizeAddress(address) {
    return String(address || "").trim().toLowerCase().replace(/^0x/, "");
}

// Pair dock entry windows with live Hyprland toplevels so previews stay in memory.
function previewWindows(entry, toplevels) {
    if (!entry || !Array.isArray(entry.windows) || entry.windows.length === 0) return [];
    var byAddress = Object.create(null);
    for (var toplevel of toplevels || []) {
        if (!toplevel) continue;
        var info = toplevel.lastIpcObject || {};
        var key = normalizeAddress(info.address || toplevel.address);
        if (key) byAddress[key] = toplevel;
    }
    return entry.windows.map(function(client) {
        var key = normalizeAddress(client.address);
        var toplevel = key ? byAddress[key] : null;
        var info = (toplevel && toplevel.lastIpcObject) || {};
        var title = (toplevel && toplevel.title) || info.title || client.title || client.class || client.initialClass || "";
        var size = Array.isArray(info.size) && info.size.length === 2 ? info.size
            : Array.isArray(client.size) && client.size.length === 2 ? client.size : [16, 10];
        return {
            address: client.address,
            title: title,
            active: client.focusHistoryID === 0,
            workspaceId: client.workspace ? client.workspace.id : 0,
            size: size,
            wayland: toplevel ? (toplevel.wayland || null) : null
        };
    });
}

function previewGridLayout(count, previewsEnabled, maxWidth, maxHeight, tileWidth, tileHeight, rowHeight, spacing, padding, headerHeight) {
    if (!count || count <= 0)
        return {columns: 1, rows: 0, rowWidth: 0, contentWidth: 0, contentHeight: 0, viewportHeight: 0, cardWidth: 0, cardHeight: 0, scrollable: false};
    if (previewsEnabled) {
        var innerMaxWidth = Math.max(tileWidth, maxWidth - padding * 2);
        var maxColumns = Math.max(1, Math.floor((innerMaxWidth + spacing) / (tileWidth + spacing)));
        var columns = Math.max(1, Math.min(count, maxColumns));
        var rows = Math.ceil(count / columns);
        var contentWidth = columns * tileWidth + (columns - 1) * spacing;
        var contentHeight = rows * tileHeight + (rows - 1) * spacing;
        var availableHeight = Math.max(tileHeight, maxHeight - padding * 2 - headerHeight);
        return {
            columns: columns,
            rows: rows,
            rowWidth: tileWidth,
            contentWidth: contentWidth,
            contentHeight: contentHeight,
            viewportHeight: Math.min(contentHeight, availableHeight),
            cardWidth: Math.min(maxWidth, contentWidth + padding * 2),
            cardHeight: Math.min(maxHeight, Math.min(contentHeight, availableHeight) + padding * 2 + headerHeight),
            scrollable: contentHeight > availableHeight
        };
    }
    var rowWidth = Math.max(160, Math.min(280, maxWidth - padding * 2));
    var listHeight = count * rowHeight + (count - 1) * spacing;
    var availableListHeight = Math.max(rowHeight, maxHeight - padding * 2 - headerHeight);
    return {
        columns: 1,
        rows: count,
        rowWidth: rowWidth,
        contentWidth: rowWidth,
        contentHeight: listHeight,
        viewportHeight: Math.min(listHeight, availableListHeight),
        cardWidth: Math.min(maxWidth, rowWidth + padding * 2),
        cardHeight: Math.min(maxHeight, Math.min(listHeight, availableListHeight) + padding * 2 + headerHeight),
        scrollable: listHeight > availableListHeight
    };
}

function previewCardGeometry(dockEdge, anchorRect, screenWidth, screenHeight, cardWidth, cardHeight, gap, margin) {
    var anchorX = anchorRect ? Number(anchorRect.x || 0) : 0;
    var anchorY = anchorRect ? Number(anchorRect.y || 0) : 0;
    var anchorW = anchorRect ? Number(anchorRect.width || 0) : 0;
    var anchorH = anchorRect ? Number(anchorRect.height || 0) : 0;
    var centerX = anchorX + anchorW / 2;
    var centerY = anchorY + anchorH / 2;
    function clampX(value) { return Math.max(margin, Math.min(Math.max(margin, screenWidth - cardWidth - margin), value)); }
    function clampY(value) { return Math.max(margin, Math.min(Math.max(margin, screenHeight - cardHeight - margin), value)); }
    var x = 0, y = 0;
    if (dockEdge === "top") {
        x = clampX(centerX - cardWidth / 2);
        y = clampY(anchorY + anchorH + gap);
    } else if (dockEdge === "left") {
        x = clampX(anchorX + anchorW + gap);
        y = clampY(centerY - cardHeight / 2);
    } else if (dockEdge === "right") {
        x = clampX(anchorX - cardWidth - gap);
        y = clampY(centerY - cardHeight / 2);
    } else {
        x = clampX(centerX - cardWidth / 2);
        y = clampY(anchorY - cardHeight - gap);
    }
    return {x: Math.round(x), y: Math.round(y), width: cardWidth, height: cardHeight};
}
