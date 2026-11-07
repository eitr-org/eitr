// Grouping, glyphs and status lines for Settings > Connections > Bluetooth.
// Devices are Quickshell BluetoothDevice objects (or fixtures with the same fields).

// BlueZ names a device without a broadcast name after its address ("AA-BB-CC-DD-EE-FF").
var addressPattern = /^([0-9A-F]{2}[:-]){5}[0-9A-F]{2}$/i;

function named(device) {
    const name = String(device.name || "").trim();
    return name !== "" && name !== device.address && !addressPattern.test(name);
}

function byName(first, second) {
    return String(first.name || first.address || "").localeCompare(String(second.name || second.address || ""), undefined, {sensitivity: "base"});
}

// Connected, paired and discovered devices; discovered devices without a name are kept
// apart so the list can collapse them.
function groups(devices) {
    const list = (devices || []).slice();
    const other = list.filter(device => !device.connected && !device.paired);
    return {
        connected: list.filter(device => device.connected).sort(byName),
        known: list.filter(device => !device.connected && device.paired).sort(byName),
        other: other.filter(named).sort(byName),
        unnamed: other.filter(device => !named(device)).sort(byName)
    };
}

// Freedesktop icon names that BlueZ reports for a device class.
var glyphs = [
    [/headset|headphone/, "󰋋"],
    [/audio|speaker/, "󰓃"],
    [/keyboard/, "󰌌"],
    [/mouse|tablet/, "󰍽"],
    [/gaming|joystick/, "󰊴"],
    [/phone/, "󰏲"],
    [/computer/, "󰟀"],
    [/display|video/, "󰍹"],
    [/watch/, "󰖉"],
    [/printer/, "󰐪"],
    [/camera/, "󰄀"]
];

function glyph(device) {
    const icon = String(device.icon || "");
    const match = glyphs.find(entry => entry[0].test(icon));
    return match ? match[1] : device.connected ? "󰂱" : "󰂯";
}

function batteryText(device) {
    return device.batteryAvailable ? Math.round(device.battery * 100) + "%" : "";
}

// The row's state for its detail line: pairing, connecting, connected, paired, new or
// unnamed (shown by address). `progress` is "pair" or "connect" while a row click runs.
function state(device, progress) {
    if (progress === "pair" || device.pairing) return "pairing";
    if (progress === "connect") return "connecting";
    if (device.connected) return "connected";
    if (device.paired) return "paired";
    return named(device) ? "new" : "unnamed";
}

// What a row click does: pair (then connect) a new device, connect a paired one.
function rowAction(device) {
    if (device.connected || device.pairing) return "";
    return device.paired ? "connect" : "pair";
}

if (typeof module !== "undefined") module.exports = {named, groups, glyph, batteryText, state, rowAction};
