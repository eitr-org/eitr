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
    'panels/AiUsageMenu.qml': ['usage'],
    'panels/SystemMonitorMenu.qml': ['sections'],
    'panels/WifiMenu.qml': ['devices'],
    'panels/KeyboardLayoutMenu.qml': ['layouts'],
    'panels/ObsMenu.qml': ['captureOptions', 'obsState'],
    'panels/RecordingMenu.qml': ['details'],
    'panels/WeatherMenu.qml': ['weatherData'],
    'panels/CalendarMenu.qml': ['reminders', 'events'],
})) {
    const source = fs.readFileSync(path.join(__dirname, '..', filename), 'utf8');
    for (const property of properties) {
        assert.ok(source.includes(`applySnapshot("${property}",`), `${filename}: ${property} must use JsonState without resetting equal models`);
        assert.ok(!source.includes(`menu.${property} = JSON.parse(`), `${filename}: unguarded JSON replacement`);
    }
    assert.ok(!source.includes('afterReveal('), `${filename}: results must not wait for reveal`);
}

const validStyle = state.parse('{"choices":[],"current":"kitty","available":true}', 0,
    {choices: 'array', current: 'string', available: 'boolean'});
assert.equal(validStyle.ok, true);
assert.equal(validStyle.data.current, 'kitty');
for (const [text, code] of [['{', 0], ['', 0], ['null', 0], ['[]', 0],
    ['{"error":"unavailable"}', 0], ['{"choices":[]}', 1], ['{"choices":null}', 0]]) {
    const result = state.parse(text, code, {choices: 'array'});
    assert.equal(result.ok, false);
    assert.equal(result.data, null);
    assert.ok(result.error.length > 0);
}
const centerSource = fs.readFileSync(path.join(__dirname, '..', 'panels/ControlCenter.qml'), 'utf8');
assert.ok(!centerSource.includes('@current'));
assert.ok(!centerSource.includes('for group in'));
for (const helper of ['cursor', 'lockscreen', 'terminal', 'effects']) {
    assert.equal(centerSource.split(`center.${helper}Script, "summary"`).length - 1, 1);
    assert.ok(!centerSource.includes(`center.${helper}Script, "get"`));
    assert.ok(!centerSource.includes(`center.${helper}Script, "entries"`));
}
assert.ok(centerSource.includes('property var styleErrors:'));

assert.equal(state.parse('{"choices":{}}', 0, {choices: {family: 'array'}}).ok, false);
assert.equal(state.parse('{"items":[{"name":3}]}', 0, {items: [{name: 'string'}]}).ok, false);
assert.equal(state.parse('{"items":[{"name":"Theme"}]}', 0, {items: [{name: 'string'}]}).ok, true);
