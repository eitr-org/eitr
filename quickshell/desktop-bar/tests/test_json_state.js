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
