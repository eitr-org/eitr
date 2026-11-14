const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../store/StoreSearch.js'), 'utf8').replace('.pragma library', ''), context);
const kinds = [{id: 'themes', sources: ['official', 'community']}, {id: 'wallpapers', sources: ['community']}];
const store = {
    'themes:official': {items: [{id: 'northern', name: 'Northern theme', kind: 'official', channel: 'official'}]},
    'themes:community': {items: [{id: 'night', name: 'Northern night', kind: 'community', channel: 'community'}]},
    'wallpapers:community': {items: [{id: 'northern', name: 'Northern sky', kind: 'community', channel: 'community'}]},
    'wallpapers:installed': {items: [{id: 'local', name: 'Northern picture', kind: 'own'}]}
};
const rows = (tab, filter) => context.rows(store, kinds, tab, 'northern', filter);
assert.equal(rows('discover', 'all').length, 3);
assert.equal(rows('discover', 'official').length, 1);
assert.equal(rows('discover', 'community').length, 2);
assert.equal(rows('installed', 'all')[0].storeKind, 'wallpapers');
assert.equal(rows('discover', 'community')[1].channel, 'community');
assert.equal(context.matches({name: 'Northern sky', maintainer: 'Example'}, 'sky example'), true);
assert.equal(context.matches({name: 'Northern sky'}, 'forest'), false);
console.log('Store: merged discovery, provenance filters and global search passed');
