.pragma library

function desktopId(value) {
    return String(value || "").replace(/\.desktop$/i, "").toLowerCase();
}

// Eitr's own task and menu terminals (classes from hyprland.lua and
// walker/bin/menu-path/kitty) have no desktop entry; they share one Eitr icon.
var eitrTerminalClass = /^(eitr-.+|(fifs?|cloud|about)-terminal|system-cleanup)$/;

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
