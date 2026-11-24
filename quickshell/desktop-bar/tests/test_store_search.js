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
const unsorted = [{id: 'b', name: 'nord'}, {id: 'c', name: 'Afterglow'}, {id: 'd', name: 'Theme 10'}, {id: 'e', name: 'Theme 9'}];
assert.deepEqual(Array.from(context.sorted(unsorted, 'name'), item => item.id), ['c', 'b', 'e', 'd']);
assert.deepEqual(Array.from(context.sorted(unsorted, 'name-descending'), item => item.id), ['d', 'e', 'b', 'c']);
assert.deepEqual(Array.from(context.sorted(unsorted), item => item.id), ['c', 'b', 'e', 'd']);
const dated = [
    {id: 'z', name: 'Zulu', createdAt: 100},
    {id: 'c', name: 'Charlie', createdAt: 200},
    {id: 'b', name: 'Bravo', createdAt: 200},
    {id: 'x', name: 'X-ray', createdAt: null},
    {id: 'a', name: 'Alpha'},
    {id: 'd', name: 'Delta', createdAt: '300'}
];
assert.deepEqual(Array.from(context.sorted(dated, 'creation-date'), item => item.id), ['b', 'c', 'z', 'a', 'd', 'x']);
assert.deepEqual(Array.from(unsorted, item => item.id), ['b', 'c', 'd', 'e']);
console.log('Store: capability intersection and unknown metadata passed');

const updates = {};
vm.createContext(updates);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../store/StoreUpdates.js'), 'utf8').replace('.pragma library', ''), updates);
const actions = [];
const catalog = {
    updateQueue: [{id: 'theme', storeKind: 'themes'}, {id: 'plugin', storeKind: 'plugins'}, {id: 'other-plugin', storeKind: 'plugins'}],
    get capabilities() { return {useOnClick: this.kind === 'themes'}; },
    act(name, args, done) { actions.push([this.kind, name, args.id]); done(); },
    prepareReview(args, queued) { actions.push([this.kind, 'review', args.id, queued]); }
};
updates.next(catalog);
assert.deepEqual(actions, [['themes', 'update', 'theme'], ['plugins', 'review', 'plugin', true]]);
assert.equal(catalog.updateQueue.length, 1);
// The same continuation used by StoreState after the first native confirmation.
updates.next(catalog);
assert.deepEqual(actions[2], ['plugins', 'review', 'other-plugin', true]);
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

const replies = {};
const checkingCatalog = {
    kinds: definitions, opened: true, opening: 1,
    updateCheck: {pending: 0, date: null, error: ''},
    updateCache: {plugins: {stale: 2}},
    transport(name, args, callback) {
        assert.equal(name, 'check');
        replies[args.kind] = callback;
    }
};
updates.check(checkingCatalog);
assert.equal(checkingCatalog.updateCheck.pending, 2);
assert.equal(checkingCatalog.updateCheck.date, null);
assert.equal(Object.keys(checkingCatalog.updateCache).length, 0);
replies.themes('', {updates: {theme: 1}});
assert.equal(checkingCatalog.updateCheck.pending, 1);
assert.equal(checkingCatalog.updateCheck.date, null);
replies.plugins('Offline', {});
assert.equal(checkingCatalog.updateCheck.pending, 0);
assert.ok(checkingCatalog.updateCheck.date);
assert.equal(checkingCatalog.updateCheck.error, 'Offline');
assert.equal(checkingCatalog.updateCache.themes.theme, 1);
assert.equal(updates.waitingForInstalled({}, checkingCatalog.updateCache), true);
assert.equal(updates.waitingForInstalled({'themes:installed': {pending: true}}, checkingCatalog.updateCache), true);
assert.equal(updates.waitingForInstalled({'themes:installed': {items: []}}, checkingCatalog.updateCache), false);
assert.equal(updates.installedLookupFailed({'themes:installed': {error: 'Lookup failed'}}, checkingCatalog.updateCache), true);

updates.check(checkingCatalog);
replies.plugins('', {updates: {}, incomplete: true});
replies.themes('', {updates: {}});
assert.equal(checkingCatalog.updateCheck.pending, 0);
assert.equal(checkingCatalog.updateCheck.incomplete, true);
assert.equal(updates.waitingForInstalled({}, checkingCatalog.updateCache), false);

updates.check(checkingCatalog);
const staleReply = replies.themes;
checkingCatalog.opening++;
staleReply('', {updates: {stale: 2}});
assert.equal(checkingCatalog.updateCheck.pending, 2);
assert.equal(Object.keys(checkingCatalog.updateCache).length, 0);
