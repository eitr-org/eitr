const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const queue = {};
vm.createContext(queue);
vm.runInContext(fs.readFileSync(path.join(root, 'ObsQueue.js'), 'utf8').replace(/^\.pragma library\s*/, ''), queue);
const plain = value => JSON.parse(JSON.stringify(value));

// Toggling updates the displayed option without mutating the previous object.
const before = {audio: {enabled: true, available: true}, mic: {enabled: true}};
const after = queue.withOption(before, 'audio', false);
assert.equal(after.audio.enabled, false);
assert.equal(after.audio.available, true);
assert.equal(before.audio.enabled, true);

// Repeated changes to one option collapse into the latest value, in order.
let pending = {};
pending = queue.enqueue(pending, 'audio', false);
pending = queue.enqueue(pending, 'mic', false);
pending = queue.enqueue(pending, 'mic', true);
assert.deepEqual(plain(pending), {audio: false, mic: true});

let next = queue.takeNext(pending);
assert.deepEqual(plain(next), {key: 'audio', enabled: false, remaining: {mic: true}});
assert.deepEqual(plain(pending), {audio: false, mic: true}, 'takeNext does not mutate the queue');
assert.deepEqual(plain(queue.optionArguments(next.key, next.enabled)), ['set-option', 'audio', 'false']);
next = queue.takeNext(next.remaining);
assert.deepEqual(plain(queue.optionArguments(next.key, next.enabled)), ['set-option', 'mic', 'true']);
assert.equal(queue.takeNext(next.remaining), null);
assert.equal(queue.takeNext({}), null);
assert.equal(queue.takeNext(undefined), null);

// ObsMenu keeps using the library and serializes writes behind optionWriter.
const menu = fs.readFileSync(path.join(root, 'ObsMenu.qml'), 'utf8');
assert.ok(menu.includes('import "ObsQueue.js" as ObsQueue'));
assert.ok(menu.includes('ObsQueue.takeNext(pendingOptionChanges)'));
assert.ok(menu.includes('if (optionWriter.running) return;'));
assert.ok(menu.includes('if (!optionWriter.running) beginAction();'));
assert.ok(menu.includes('readonly property bool controlsReady: obsState.ready && !busy'));
console.log('OBS option queue tests passed');
