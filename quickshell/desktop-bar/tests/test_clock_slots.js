const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const registry = fs.readFileSync(path.join(__dirname, "../plugins/PluginRegistry.qml"), "utf8");
const source = registry.match(/function slotItems\(slot\) \{([\s\S]*?)\n    \}/)[1];
const placedBarItems = [{plugin: "legacy"}];
for (const slot of ["start", "clock", "clockEnd", "status"]) {
    for (let index = 0; index < 12; index++) placedBarItems.push({plugin: slot + index, slot});
}
const context = vm.createContext({placedBarItems});
vm.runInContext("function slotItems(slot) {" + source + "}", context);
for (const [slot, limit] of [["start", 4], ["clock", 2], ["clockEnd", 2], ["status", 8]]) {
    const entries = context.slotItems(slot);
    assert.equal(entries.length, limit);
    assert.equal(entries[0].plugin, slot === "status" ? "legacy" : slot + "0");
    assert(entries.every(entry => (entry.slot || "status") === slot));
}
console.log("All four slots preserve order, legacy status defaults and independent limits");
const placedSource = registry.match(/function placed\(kind, monitor\) \{([\s\S]*?)\n    \}/)[1];
const overrideContext = vm.createContext({
    placements: {barItems: [{plugin: "example", id: "clock", slot: "start"}, {plugin: "legacy", id: "icon"}]},
    entries: [{plugin: "example", id: "clock", kind: "barItems", slot: "clock"}, {plugin: "legacy", id: "icon", kind: "barItems"}]
});
vm.runInContext("function placed(kind, monitor) {" + placedSource + "}", overrideContext);
const resolved = overrideContext.placed("barItems", "");
assert.equal(resolved[0].slot, "start");
assert.equal(resolved[1].slot, "status");
console.log("Placement overrides beat manifest slots; missing slots remain status");
const panelSource = fs.readFileSync(path.join(__dirname, "../bar/BarPanels.qml"), "utf8");
const showSource = panelSource.match(/function showKind\(kind\) \{([\s\S]*?)\n    \}/)[1];
let openedWeather = false;
const panelContext = vm.createContext({
    PluginRegistry: {weatherEnabled: false},
    barHost: {weatherMenu: {}, showPanel(panel) { openedWeather = true; }},
    notificationCenter: {}, controlCenter: {}, mediaMenu: {}, batteryMenu: {}
});
vm.runInContext("function showKind(kind) {" + showSource + "}", panelContext);
panelContext.showKind("weather");
assert.equal(openedWeather, false);
panelContext.PluginRegistry.weatherEnabled = true;
panelContext.showKind("weather");
assert.equal(openedWeather, true);
console.log("Removing Weather also disables its external panel entry point");
