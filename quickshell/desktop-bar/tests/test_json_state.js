const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const state = {};
vm.createContext(state);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'JsonState.js'), 'utf8').replace(/^\.pragma library\s*/, ''), state);

assert.equal(state.changed({a: 1, b: [1, 2]}, {a: 1, b: [1, 2]}), false);
assert.equal(state.changed([], []), false);
assert.equal(state.changed({available: false}, {available: true}), true);
assert.equal(state.changed([{name: 'DP-3'}], [{name: 'DP-3'}, {name: 'HDMI-A-1'}]), true);

// Refresh-driven list owners must use the shared guarded snapshot path.
for (const [filename, properties] of Object.entries({
    'AiUsageMenu.qml': ['usage'],
    'SystemMonitorMenu.qml': ['sections'],
    'WifiMenu.qml': ['devices'],
    'KeyboardLayoutMenu.qml': ['layouts'],
    'ObsMenu.qml': ['captureOptions', 'obsState'],
    'RecordingMenu.qml': ['details'],
    'WeatherMenu.qml': ['weatherData'],
    'CalendarMenu.qml': ['reminders', 'events'],
})) {
    const source = fs.readFileSync(path.join(__dirname, '..', filename), 'utf8');
    for (const property of properties) {
        assert.ok(source.includes(`applySnapshot("${property}",`), `${filename}: ${property} must use JsonState without resetting equal models`);
        assert.ok(!source.includes(`menu.${property} = JSON.parse(`), `${filename}: unguarded JSON replacement`);
    }
    assert.ok(!source.includes('afterReveal('), `${filename}: results must not wait for reveal`);
}
