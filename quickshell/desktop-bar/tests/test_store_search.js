const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../store/StoreSearch.js'), 'utf8').replace('.pragma library', ''), context);
assert.equal(context.matches({name: 'Northern sky', maintainer: 'Example'}, 'sky example'), true);
assert.equal(context.matches({name: 'Northern sky'}, 'forest'), false);

const definitions = JSON.parse(fs.readFileSync(path.join(__dirname, "../../../distro/store-kinds.json"), "utf8"));
const definition = identifier => definitions.find(entry => entry.id === identifier);
const plugin = {kind: 'community', components: {ui: {widgets: [{}], barItems: [{}]}, rows: [{}], service: {run: 'main.py'}, packages: ['example']}};
const filter = selected => context.filters(plugin, definition('plugins'), 'all', 'all', {'plugins:adds': selected});
assert.equal(filter(['widgets', 'barItems', 'rows', 'service', 'packages']), true);
assert.equal(filter(['widgets', 'tiles']), false);
assert.equal(context.filters({kind: 'official'}, definition('plugins'), 'all', 'all', {'plugins:adds': ['service']}), false);
assert.equal(context.filters(plugin, definition('plugins'), 'official', 'all', {}), false);
assert.equal(context.filters({kind: 'official', light: true}, definition('themes'), 'all', 'dark', {}), false);
console.log('Store: capability intersection and unknown metadata passed');

const updates = {};
vm.createContext(updates);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../store/StoreUpdates.js'), 'utf8').replace('.pragma library', ''), updates);
const actions = [];
const catalog = {
    updateQueue: [{id: 'theme', storeKind: 'themes'}, {id: 'plugin', storeKind: 'plugins'}],
    get capabilities() { return {useOnClick: this.kind === 'themes'}; },
    act(name, args, done) { actions.push([this.kind, name, args.id]); done(); },
    prepareReview(args, queued) { actions.push([this.kind, 'review', args.id, queued]); }
};
updates.next(catalog);
assert.deepEqual(actions, [['themes', 'update', 'theme'], ['plugins', 'review', 'plugin', true]]);
assert.equal(catalog.updateQueue.length, 0);

const futureKind = {id: 'future', filters: [{id: 'feature', multiple: false, options: [{id: 'all'}, {id: 'enabled', path: 'metadata.enabled', equals: true}]}]};
assert.equal(context.filters({metadata: {enabled: true}}, futureKind, 'all', 'all', {'future:feature': 'enabled'}), true);
assert.equal(context.filters({metadata: {enabled: false}}, futureKind, 'all', 'all', {'future:feature': 'enabled'}), false);

const pending = updates.items({'themes:installed': {items: [{id: 'same'}, {id: 'none'}]}, 'plugins:installed': {items: [{id: 'same'}]}}, definitions, {themes: {same: 2}, plugins: {same: 1, absent: 3}});
assert.equal(pending.length, 2);
assert.equal(pending[0].storeKind, 'themes');
assert.equal(pending[1].storeKind, 'plugins');

assert.equal(context.filters({kind: 'own'}, definition('themes'), 'community', 'all', {}), false);
assert.equal(context.filters({kind: 'own'}, definition('themes'), 'all', 'all', {}), true);
