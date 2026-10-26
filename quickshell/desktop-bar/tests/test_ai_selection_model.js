const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const model = {};
vm.createContext(model);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'AiSelectionModel.js'), 'utf8').replace(/^\.pragma library\s*/, ''), model);
const available = ['Claude', 'Codex', 'Grok'];
const plain = value => JSON.parse(JSON.stringify(value));

assert.deepEqual(plain(model.restore({version: 1, providers: ['Codex']})), []);
assert.deepEqual(plain(model.restore({version: 2, foldedProviders: ['Codex']})), []);
assert.deepEqual(plain(model.restore({version: 1, openedProviders: 'Codex'})), []);
assert.deepEqual(plain(model.toggle(available, [], 'Claude')), ['Claude']);
assert.deepEqual(plain(model.toggle(available, ['Claude'], 'Codex')), ['Claude', 'Codex']);
assert.deepEqual(plain(model.toggle(available, ['Claude', 'Codex'], 'Claude')), ['Codex']);
assert.deepEqual(plain(model.toggle(available, ['Codex'], 'Codex')), []);
assert.deepEqual(plain(model.toggle(available, ['Codex'], 'missing')), ['Codex']);
console.log('AI provider folding checks passed');

assert.deepEqual(plain(model.restore({version: 1, openedProviders: ['Codex']})), ['Codex']);
assert.deepEqual(plain(model.restore(null)), []);
assert.deepEqual(plain(model.toggle(['Codex'], ['Claude'], 'Codex')), ['Claude', 'Codex']);
const readable = {label: 'Default', plan: 'Max', windows: [{used: 10}]};
assert.deepEqual(plain(model.shownProviders([
    {name: 'Claude', accounts: [readable, {error: 'Offline', windows: [{used: 5}]}, {windows: []}, {}]},
    {name: 'Empty', accounts: []}, {name: 'Unsupported', accounts: [{windows: []}]}
])), [{name: 'Claude', accounts: [readable]}]);
assert.equal(model.sharedPlan([readable]), 'Max');
assert.equal(model.sharedPlan([readable, {...readable}]), 'Max');
assert.equal(model.sharedPlan([readable, {...readable, plan: 'Pro'}]), '');
assert.equal(model.sharedPlan([readable, {...readable, plan: null}]), '');
assert.equal(model.sharedPlan([{windows: [{used: 0}]}]), '');
assert.equal(model.sharedPlan([]), '');
