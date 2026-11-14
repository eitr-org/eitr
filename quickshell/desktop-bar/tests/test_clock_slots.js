const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const registry = fs.readFileSync(path.join(__dirname, "../plugins/PluginRegistry.qml"), "utf8");
function expression(name, context) {
    const match = registry.match(new RegExp("readonly property var " + name + ": (.+)"));
    return vm.runInNewContext(match[1], context);
}
const placedBarItems = [
    {plugin: "status"},
    {plugin: "first", slot: "clock"},
    {plugin: "second", slot: "clock"},
    {plugin: "overflow", slot: "clock"},
    {plugin: "legacy"}
];
const clockBarItems = expression("clockBarItems", {placedBarItems});
assert.deepEqual(Array.from(clockBarItems, entry => entry.plugin), ["first", "second"]);
const status = expression("barItems", {placedBarItems, clockBarItems});
assert.deepEqual(Array.from(status, entry => entry.plugin), ["status", "overflow", "legacy"]);
assert.equal(new Set([...clockBarItems, ...status]).size, placedBarItems.length);
console.log("Clock slots preserve placement order, cap at two, and overflow to status");
