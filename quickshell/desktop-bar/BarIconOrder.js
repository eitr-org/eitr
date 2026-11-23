.pragma library

var ZONES = ["left", "clockStart", "clockEnd", "right"];

var ZONE_TO_SLOT = {
    left: "start",
    clockStart: "clock",
    clockEnd: "clockEnd",
    right: "status"
};

var SLOT_TO_ZONE = {
    start: "left",
    clock: "clockStart",
    clockEnd: "clockEnd",
    status: "right"
};

// Default movable bar icons across the four organizer zones. Fixed chrome
// (Eitr logo, overview, workspaces, clock, media strip, centered pin, capture)
// stays anchored by each bar layout and is never listed here.
var BUILTIN_ICONS = [
    {id: "hardware", defaultZone: "left", title: "Hardware", glyph: "󰍛", iconSize: 18, alwaysOpen: true, command: false, conditional: ""},
    {id: "idleLock", defaultZone: "left", title: "Idle Lock", glyph: "󰌾", iconSize: 17, alwaysOpen: true, command: false, conditional: ""},
    {id: "wifi", defaultZone: "right", title: "WiFi", glyph: "󰤨", iconSize: 16, alwaysOpen: false, command: true, conditional: ""},
    {id: "bluetooth", defaultZone: "right", title: "Bluetooth", glyph: "󰂯", iconSize: 15, alwaysOpen: false, command: false, conditional: ""},
    {id: "display", defaultZone: "right", title: "Display", glyph: "󰍹", iconSize: 15, alwaysOpen: false, command: false, conditional: ""},
    {id: "audio", defaultZone: "right", title: "Audio/Mic", glyph: "\u{F02CE}", iconSize: 15, alwaysOpen: false, command: false, conditional: ""},
    {id: "streaming", defaultZone: "right", title: "Streaming", glyph: "󰢹", iconSize: 15, alwaysOpen: false, command: false, conditional: "streaming"},
    {id: "obs", defaultZone: "right", title: "OBS Studio", glyph: "󰻂", iconSize: 16, alwaysOpen: false, command: false, conditional: ""},
    {id: "keyboard", defaultZone: "right", title: "Keyboard", glyph: "󰌌", iconSize: 14, alwaysOpen: false, command: false, conditional: "keyboard"},
    {id: "updates", defaultZone: "right", title: "System Update", glyph: "󰗡", iconSize: 17, alwaysOpen: false, command: false, conditional: ""},
    {id: "battery", defaultZone: "right", title: "Battery", glyph: "󰁹", iconSize: 15, alwaysOpen: false, command: false, conditional: "battery"},
    {id: "notifications", defaultZone: "right", title: "Notifications", glyph: "󰂜", iconSize: 18, alwaysOpen: true, command: false, conditional: ""}
];

function emptyZones() {
    return {left: [], clockStart: [], clockEnd: [], right: []};
}

function cloneIdsByZone(source) {
    const copy = emptyZones();
    for (const zone of ZONES) copy[zone] = (source && Array.isArray(source[zone])) ? source[zone].slice() : [];
    return copy;
}

function ordersEqual(first, second) {
    if (!first || !second) return false;
    for (const zone of ZONES) {
        const listA = first[zone] || [];
        const listB = second[zone] || [];
        if (listA.length !== listB.length) return false;
        for (let index = 0; index < listA.length; index++) {
            if (listA[index] !== listB[index]) return false;
        }
    }
    return true;
}

function pluginItemId(entry) {
    if (!entry) return "";
    if (entry.bundled && entry.plugin === "ai-usage" && entry.id === "usage") return "ai";
    if (entry.plugin && entry.id) return String(entry.plugin) + ":" + String(entry.id);
    if (entry.id) return "plugin:" + String(entry.id);
    if (entry.title) return "plugin:" + String(entry.title);
    return "";
}

function parseSavedOrder(raw) {
    if (!raw) return null;
    let parsed = raw;
    if (typeof raw === "string") {
        const trimmed = raw.trim();
        if (!trimmed || trimmed === "null") return null;
        try {
            parsed = JSON.parse(trimmed);
        } catch (ignored) {
            return null;
        }
    }
    if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) return null;
    let hasZone = false;
    for (const zone of ZONES) {
        if (Array.isArray(parsed[zone])) hasZone = true;
    }
    if (!hasZone) return null;
    const cleaned = emptyZones();
    const seen = Object.create(null);
    for (const zone of ZONES) {
        const list = parsed[zone];
        if (!Array.isArray(list)) continue;
        for (const item of list) {
            if (typeof item !== "string" || !item || seen[item]) continue;
            seen[item] = true;
            cleaned[zone].push(item);
        }
    }
    return cleaned;
}

function serializeOrder(idsByZone) {
    const cleaned = cloneIdsByZone(idsByZone);
    return JSON.stringify({
        left: cleaned.left,
        clockStart: cleaned.clockStart,
        clockEnd: cleaned.clockEnd,
        right: cleaned.right
    });
}

function mergeIcons(pluginItems, translate) {
    const tr = typeof translate === "function" ? translate : (text => text);
    const byId = Object.create(null);
    const defaultIdsByZone = emptyZones();

    for (const builtin of BUILTIN_ICONS) {
        if (builtin.id === "notifications") continue;
        const item = {
            id: builtin.id,
            kind: "builtin",
            plugin: "",
            itemId: "",
            panel: "",
            capabilities: [],
            defaultZone: builtin.defaultZone,
            slot: ZONE_TO_SLOT[builtin.defaultZone],
            title: tr(builtin.title),
            glyph: builtin.glyph,
            iconSize: builtin.iconSize,
            alwaysOpen: builtin.alwaysOpen,
            command: builtin.command,
            conditional: builtin.conditional,
            entry: null
        };
        byId[item.id] = item;
        defaultIdsByZone[item.defaultZone].push(item.id);
    }

    for (const entry of (pluginItems || [])) {
        const id = pluginItemId(entry);
        if (!id || byId[id]) continue;
        const slot = entry.slot || "status";
        const defaultZone = SLOT_TO_ZONE[slot] || "right";
        const glyph = entry.icon || "󰐱";
        const item = {
            id: id,
            kind: "plugin",
            plugin: entry.plugin ? String(entry.plugin) : "",
            itemId: entry.id ? String(entry.id) : String(entry.title || ""),
            panel: entry.panel ? String(entry.panel) : "",
            capabilities: Array.isArray(entry.capabilities) ? entry.capabilities.slice() : [],
            defaultZone: defaultZone,
            slot: ZONE_TO_SLOT[defaultZone],
            title: entry.bundled ? tr(String(entry.title || entry.id)) : String(entry.title || entry.id),
            glyph: glyph,
            iconSize: id === "ai" ? 16 : 15,
            alwaysOpen: defaultZone !== "right",
            command: false,
            conditional: "",
            entry: entry
        };
        byId[id] = item;
        if (id === "ai") defaultIdsByZone[defaultZone].unshift(id);
        else defaultIdsByZone[defaultZone].push(id);
    }

    // Notifications defaults to the end of right so status plugins remain inside the collapsible group.
    const notifyBuiltin = BUILTIN_ICONS.find(entry => entry.id === "notifications");
    if (notifyBuiltin) {
        const notifyItem = {
            id: notifyBuiltin.id,
            kind: "builtin",
            plugin: "",
            itemId: "",
            panel: "",
            capabilities: [],
            defaultZone: notifyBuiltin.defaultZone,
            slot: ZONE_TO_SLOT[notifyBuiltin.defaultZone],
            title: tr(notifyBuiltin.title),
            glyph: notifyBuiltin.glyph,
            iconSize: notifyBuiltin.iconSize,
            alwaysOpen: notifyBuiltin.alwaysOpen,
            command: notifyBuiltin.command,
            conditional: notifyBuiltin.conditional,
            entry: null
        };
        byId[notifyItem.id] = notifyItem;
        defaultIdsByZone[notifyItem.defaultZone].push(notifyItem.id);
    }

    return {byId: byId, defaultIdsByZone: defaultIdsByZone};
}

function insertMissingItem(zoneList, itemId, defaultList) {
    const defaultIndex = defaultList.indexOf(itemId);
    for (let next = defaultIndex + 1; next < defaultList.length; next++) {
        const pos = zoneList.indexOf(defaultList[next]);
        if (pos >= 0) {
            zoneList.splice(pos, 0, itemId);
            return;
        }
    }
    for (let prev = defaultIndex - 1; prev >= 0; prev--) {
        const pos = zoneList.indexOf(defaultList[prev]);
        if (pos >= 0) {
            zoneList.splice(pos + 1, 0, itemId);
            return;
        }
    }
    zoneList.push(itemId);
}

function resolve(savedOrderOrJson, pluginItems, translate) {
    const merged = mergeIcons(pluginItems, translate);
    const saved = parseSavedOrder(savedOrderOrJson);
    const idsByZone = emptyZones();
    const zoneOf = Object.create(null);
    const seen = Object.create(null);

    if (saved) {
        for (const zone of ZONES) {
            for (const id of saved[zone]) {
                if (!merged.byId[id] || seen[id]) continue;
                seen[id] = true;
                zoneOf[id] = zone;
                idsByZone[zone].push(id);
            }
        }
        for (const zone of ZONES) {
            const defaultList = merged.defaultIdsByZone[zone];
            for (const id of defaultList) {
                if (seen[id]) continue;
                seen[id] = true;
                zoneOf[id] = zone;
                insertMissingItem(idsByZone[zone], id, defaultList);
            }
        }
    } else {
        for (const zone of ZONES) {
            idsByZone[zone] = merged.defaultIdsByZone[zone].slice();
            for (const id of idsByZone[zone]) zoneOf[id] = zone;
        }
    }

    const zones = emptyZones();
    const plugins = [];
    for (const zone of ZONES) {
        const slot = ZONE_TO_SLOT[zone];
        for (const id of idsByZone[zone]) {
            const base = merged.byId[id];
            const item = Object.assign({}, base, {
                zone: zone,
                effectiveSlot: slot,
                alwaysOpen: base.alwaysOpen || zone !== "right"
            });
            zones[zone].push(item);
            if (item.kind === "plugin") {
                plugins.push(Object.assign({}, item.entry || {}, {
                    plugin: item.plugin,
                    id: item.itemId,
                    slot: slot,
                    zone: zone,
                    resolvedId: id
                }));
            }
        }
    }

    return {
        zones: zones,
        idsByZone: idsByZone,
        defaultIdsByZone: cloneIdsByZone(merged.defaultIdsByZone),
        zoneOf: zoneOf,
        byId: merged.byId,
        plugins: plugins,
        customized: saved !== null
    };
}

function visibleIndexToRawIndex(list, visibleIndex, hiddenMap) {
    if (!hiddenMap) return Math.max(0, Math.min(list.length, visibleIndex));
    if (visibleIndex <= 0) return 0;
    let visibleSeen = 0;
    for (let index = 0; index < list.length; index++) {
        if (hiddenMap[list[index]]) continue;
        if (visibleSeen === visibleIndex) return index;
        visibleSeen++;
    }
    return list.length;
}

function moveItem(idsByZone, id, targetZone, targetIndex, hiddenMap) {
    if (ZONES.indexOf(targetZone) < 0 || !id) return cloneIdsByZone(idsByZone);
    const next = cloneIdsByZone(idsByZone);
    let found = false;
    for (const zone of ZONES) {
        const pos = next[zone].indexOf(id);
        if (pos >= 0) {
            next[zone].splice(pos, 1);
            found = true;
        }
    }
    if (!found) return next;
    const dest = next[targetZone];
    const insertAt = visibleIndexToRawIndex(dest, targetIndex, hiddenMap);
    dest.splice(insertAt, 0, id);
    return next;
}

function moveStep(idsByZone, id, direction, hiddenMap) {
    if (!id) return cloneIdsByZone(idsByZone);
    let currentZone = "";
    for (const zone of ZONES) {
        if ((idsByZone[zone] || []).indexOf(id) >= 0) {
            currentZone = zone;
            break;
        }
    }
    if (!currentZone) return cloneIdsByZone(idsByZone);
    const zoneIndex = ZONES.indexOf(currentZone);
    const visibleCurrent = (idsByZone[currentZone] || []).filter(itemId => !hiddenMap || !hiddenMap[itemId]);
    const visiblePos = visibleCurrent.indexOf(id);
    if (visiblePos < 0) return cloneIdsByZone(idsByZone);

    if (direction === "left") {
        if (visiblePos > 0) return moveItem(idsByZone, id, currentZone, visiblePos - 1, hiddenMap);
        if (zoneIndex > 0) {
            const prevZone = ZONES[zoneIndex - 1];
            const prevVisible = (idsByZone[prevZone] || []).filter(itemId => !hiddenMap || !hiddenMap[itemId]);
            return moveItem(idsByZone, id, prevZone, prevVisible.length, hiddenMap);
        }
        return cloneIdsByZone(idsByZone);
    }
    if (direction === "right") {
        if (visiblePos + 1 < visibleCurrent.length) return moveItem(idsByZone, id, currentZone, visiblePos + 1, hiddenMap);
        if (zoneIndex + 1 < ZONES.length) return moveItem(idsByZone, id, ZONES[zoneIndex + 1], 0, hiddenMap);
        return cloneIdsByZone(idsByZone);
    }
    if (direction === "up") {
        if (zoneIndex <= 0) return cloneIdsByZone(idsByZone);
        const prevZone = ZONES[zoneIndex - 1];
        const prevVisible = (idsByZone[prevZone] || []).filter(itemId => !hiddenMap || !hiddenMap[itemId]);
        return moveItem(idsByZone, id, prevZone, Math.min(visiblePos, prevVisible.length), hiddenMap);
    }
    if (direction === "down") {
        if (zoneIndex + 1 >= ZONES.length) return cloneIdsByZone(idsByZone);
        const nextZone = ZONES[zoneIndex + 1];
        const nextVisible = (idsByZone[nextZone] || []).filter(itemId => !hiddenMap || !hiddenMap[itemId]);
        return moveItem(idsByZone, id, nextZone, Math.min(visiblePos, nextVisible.length), hiddenMap);
    }
    return cloneIdsByZone(idsByZone);
}

function updateRegistry(current, id, item, expectingMatch) {
    const map = current || Object.create(null);
    const existing = map[id] || null;
    if (expectingMatch ? existing !== expectingMatch : existing === (item || null)) return null;
    const next = Object.assign({}, map);
    if (!expectingMatch && item) next[id] = item;
    else delete next[id];
    return next;
}

function resolveTarget(item, zone, iconsOpen, verticalBar, hiddenFallback, fallback) {
    if (item && (zone !== "right" || iconsOpen || verticalBar || (item.visible && item.width > 0))) return item;
    const collapsedAnchor = zone === "right" && !verticalBar && !iconsOpen ? hiddenFallback : null;
    return collapsedAnchor || item || fallback;
}
