const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const context = vm.createContext({});
const source = fs.readFileSync(path.join(root, 'BarIconOrder.js'), 'utf8').replace('.pragma library', '');
vm.runInContext(source, context);
const plain = value => JSON.parse(JSON.stringify(value));

const weatherPlugin = {plugin: 'weather', id: 'weather', title: 'Weather', icon: '󰖐', slot: 'clockEnd', panel: 'forecast', capabilities: ['weather']};
const worldClockPlugin = {plugin: 'worldclock', id: 'clock', title: 'World clock', icon: '󰥔', slot: 'clock', panel: 'list', capabilities: []};
const extraStatusPlugin = {plugin: 'notes', id: 'quick', title: 'Quick note', icon: '󰎞', slot: 'status', panel: 'pad', capabilities: []};
const startPlugin = {plugin: 'focus', id: 'streak', title: 'Streak', icon: '󰈸', slot: 'start', panel: 'stats', capabilities: []};

// Default order keeps all 13 built-ins and places active plugins in their manifest slots.
const aiUsage = {plugin: 'ai-usage', id: 'usage', title: 'AI Usage', bundled: true, slot: 'start', panel: 'limits'};
assert.deepEqual(plain(context.resolve('', []).idsByZone.left), ['hardware', 'idleLock']);
assert.deepEqual(plain(context.resolve({clockStart: ['ai']}, [aiUsage]).idsByZone.clockStart), ['ai']);
assert.deepEqual(plain(context.resolve({clockStart: ['ai']}, []).idsByZone.clockStart), []);

const defaultResolved = plain(context.resolve('', [aiUsage, weatherPlugin, extraStatusPlugin]));
assert.deepEqual(defaultResolved.idsByZone.left, ['ai', 'hardware', 'idleLock']);
assert.deepEqual(defaultResolved.idsByZone.clockStart, []);
assert.deepEqual(defaultResolved.idsByZone.clockEnd, ['weather:weather']);
assert.deepEqual(defaultResolved.idsByZone.right, [
    'wifi', 'bluetooth', 'display', 'audio', 'streaming', 'obs', 'keyboard',
    'updates', 'battery', 'notes:quick', 'notifications'
]);
assert.equal(defaultResolved.customized, false);

// Unknown IDs and duplicates across zones are ignored without dropping built-ins.
const savedWithUnknown = JSON.stringify({
    left: ['updates', 'ghost:item', 'ai', 'updates'],
    clockStart: ['ai', 'hardware'],
    clockEnd: ['weather:weather', 'unknown-builtin'],
    right: ['notifications', 'wifi', 'bluetooth', 'display', 'audio', 'streaming', 'obs', 'keyboard', 'idleLock', 'battery']
});
const cleaned = plain(context.resolve(savedWithUnknown, [aiUsage, weatherPlugin]));
assert.equal(cleaned.customized, true);
assert.deepEqual(cleaned.idsByZone.left, ['updates', 'ai']);
assert.deepEqual(cleaned.idsByZone.clockStart, ['hardware']);
assert.deepEqual(cleaned.idsByZone.clockEnd, ['weather:weather']);
assert.deepEqual(cleaned.idsByZone.right, ['notifications', 'wifi', 'bluetooth', 'display', 'audio', 'streaming', 'obs', 'keyboard', 'idleLock', 'battery']);
assert.equal(cleaned.zoneOf['updates'], 'left');
assert.equal(cleaned.zoneOf['ghost:item'], undefined);

// Newly added built-in or plugin icons insert into their default zone at their default relative position.
const partialSaved = JSON.stringify({
    left: ['idleLock'],
    clockStart: [],
    clockEnd: ['weather:weather'],
    right: ['wifi', 'bluetooth', 'display', 'audio', 'streaming', 'obs', 'keyboard', 'updates', 'battery', 'notifications']
});
const withNewIcons = plain(context.resolve(partialSaved, [aiUsage, weatherPlugin, extraStatusPlugin, worldClockPlugin, startPlugin]));
assert.deepEqual(withNewIcons.idsByZone.left, ['ai', 'hardware', 'idleLock', 'focus:streak']);
assert.deepEqual(withNewIcons.idsByZone.clockStart, ['worldclock:clock']);
assert.equal(withNewIcons.idsByZone.right.indexOf('notes:quick'), withNewIcons.idsByZone.right.indexOf('notifications') - 1);

// Moving within and between zones (including with hidden battery preserved in-place).
const hiddenBattery = {battery: true};
const movedRight = plain(context.moveItem(defaultResolved.idsByZone, 'updates', 'right', 9, hiddenBattery));
assert.equal(movedRight.right.indexOf('updates'), movedRight.right.length - 1);
assert.ok(movedRight.right.includes('battery'));

const movedToClockStart = plain(context.moveItem(defaultResolved.idsByZone, 'wifi', 'clockStart', 0, hiddenBattery));
assert.deepEqual(movedToClockStart.clockStart, ['wifi']);
assert.equal(movedToClockStart.right.includes('wifi'), false);

// Keyboard step movement wraps across adjacent zones cleanly.
let stepped = plain(context.moveStep(defaultResolved.idsByZone, 'idleLock', 'right', hiddenBattery));
assert.deepEqual(stepped.left, ['ai', 'hardware']);
assert.deepEqual(stepped.clockStart, ['idleLock']);
stepped = plain(context.moveStep(stepped, 'idleLock', 'left', hiddenBattery));
assert.deepEqual(stepped.left, ['ai', 'hardware', 'idleLock']);
stepped = plain(context.moveStep(defaultResolved.idsByZone, 'ai', 'down', hiddenBattery));
assert.deepEqual(stepped.clockStart, ['ai']);

// Drop dashboard rail plugin order follows BarIconOrder zone progression (left -> clockStart -> clockEnd -> right).
const customPluginOrder = JSON.stringify({
    left: ['ai', 'hardware', 'idleLock', 'notes:quick'],
    clockStart: ['worldclock:clock'],
    clockEnd: ['weather:weather'],
    right: ['wifi', 'bluetooth', 'display', 'audio', 'streaming', 'obs', 'keyboard', 'updates', 'battery', 'focus:streak', 'notifications']
});
const pluginResolved = plain(context.resolve(customPluginOrder, [aiUsage, weatherPlugin, extraStatusPlugin, worldClockPlugin, startPlugin]));
assert.deepEqual(
    pluginResolved.plugins.map(entry => entry.resolvedId),
    ['ai', 'notes:quick', 'worldclock:clock', 'weather:weather', 'focus:streak']
);

console.log('Bar icon order checks passed');
