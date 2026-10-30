function glyph(snapshot, blocked) {
    if (blocked) return "󰤮";
    for (const device of snapshot.devices || []) {
        const connected = (device.networks || []).find(network => network.connected);
        if (!connected) continue;
        const strength = Number(connected.strength);
        const thresholds = snapshot.backend === "networkmanager" ? [75, 55, 35, 15] : [100, 80, 60, 40];
        const icons = ["󰤨", "󰤥", "󰤢", "󰤟", "󰤯"];
        const index = thresholds.findIndex(threshold => strength >= threshold);
        return icons[index < 0 ? 4 : index];
    }
    return "";
}

if (typeof module !== "undefined") module.exports = {glyph};
