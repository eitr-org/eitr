const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createClient, restartDelay} = require('../DesktopDataProtocol.js');
const sent = [];
const client = createClient(frame => sent.push(frame), () => {});
const receive = frame => client.receive(JSON.stringify(Object.assign({v: 1}, frame)));
const first = client.observe('network.details', 'screen-one');
const second = client.observe('network.details', 'screen-two');
receive({op: 'hello', epoch: 'one'});
assert.deepEqual(sent.map(frame => frame.token), [first, second]);
receive({op: 'state', epoch: 'one', topic: 'network.details', seq: 2, status: 'ready', data: {devices: []}, ageMs: 0});
receive({op: 'state', epoch: 'one', topic: 'network.details', seq: 1, status: 'ready', data: {bad: true}, ageMs: 0});
assert.deepEqual(client.states['network.details'].data, {devices: []});
client.died();
assert.equal(client.states['network.details'].status, 'stale');
client.release(first);
sent.length = 0;
receive({op: 'hello', epoch: 'two'});
assert.deepEqual(sent.map(frame => frame.token), [second]);
receive({op: 'state', epoch: 'one', topic: 'network.details', seq: 99, status: 'ready', data: {bad: true}, ageMs: 0});
receive({op: 'state', epoch: 'two', topic: 'network.details', seq: 0, status: 'loading', data: {}, ageMs: null});
assert.equal(client.states['network.details'].status, 'stale');
receive({op: 'state', epoch: 'two', topic: 'network.details', seq: 1, status: 'ready', data: {devices: ['new']}, ageMs: 0});
assert.deepEqual(client.states['network.details'].data, {devices: ['new']});
client.receive('broken');
client.releaseOwner('screen-two');
assert.equal(client.count('network.details'), 0);
const bar = path.resolve(__dirname, '..');
const service = fs.readFileSync(path.join(bar, 'NetworkService.qml'), 'utf8');
assert.equal((service.match(/Process\s*\{/g) || []).length, 1, 'only QR worker remains');
const facade = fs.readFileSync(path.join(bar, 'DesktopData.qml'), 'utf8');
assert.ok(facade.startsWith('pragma Singleton'));
assert.equal((facade.match(/Process\s*\{/g) || []).length, 1);
console.log('broker epoch, crash, token replay and single reader wiring passed');

assert.equal(restartDelay(1, 0.5), 500);
assert.equal(restartDelay(2, 0.5), 1000);
assert.equal(restartDelay(20, 1), 30000);
assert.equal(restartDelay(1, 0), 400);
assert.equal(restartDelay(1, 1), 600);

assert.ok(!facade.includes('diagnosticTimer'));
assert.ok(!/repeat:\s*true/.test(facade), 'no periodic diagnostics');
const statusBody = facade.slice(facade.indexOf('function status()'), facade.indexOf('Component.onCompleted'));
assert.equal((statusBody.match(/op: "status"/g) || []).length, 1);

receive({op: 'state', epoch: 'two', topic: 'network.summary', seq: 1, status: 'ready', data: {devices: []}, ageMs: 0});
const results = [];
const actionId = client.act('connect', {input: {password: 'secret'}}, code => results.push(code));
assert.ok(actionId);
assert.equal(client.domain.busy, true);
receive({op: 'domain', epoch: 'two', topic: 'network', busy: false, name: ''});
assert.equal(client.domain.busy, true, 'older idle event cannot unlock a submitted action');
assert.equal(client.act('forget', {}, () => {}), '');
client.died();
assert.deepEqual(results, ['outcome-unknown']);
sent.length = 0;
receive({op: 'hello', epoch: 'three'});
assert.ok(!sent.some(frame => frame.op === 'action'), 'writes never replay');
receive({op: 'result', epoch: 'two', topic: 'network', id: actionId, error: ''});
assert.equal(results.length, 1, 'late result ignored');
assert.equal(client.act('connect', {}, () => {}), '', 'reconcile before writes');

receive({op: 'state', epoch: 'three', topic: 'network.summary', seq: 1, status: 'ready', data: {devices: []}, ageMs: 0});
const retryId = client.act('connect', {}, code => results.push(code));
receive({op: 'result', epoch: 'three', topic: 'network', id: retryId, error: 'outcome-unknown', busy: false});
assert.equal(client.act('connect', {}, () => {}), '', 'timeout requires reconciliation');
receive({op: 'state', epoch: 'three', topic: 'network.summary', seq: 1, status: 'ready', data: {devices: []}, ageMs: 0});
assert.equal(client.act('connect', {}, () => {}), '', 'cached subscribe snapshot is not reconciliation');
receive({op: 'state', epoch: 'three', topic: 'network.summary', seq: 2, status: 'ready', data: {devices: []}, ageMs: 0});
const detachedId = client.act('connect', {}, () => { throw new Error('closed panel callback'); });
assert.ok(detachedId, 'explicit retry after fresh state');
client.detachAction(detachedId);
client.died();

receive({op: 'hello', epoch: 'capture-test'});
const captureResults = [];
const captureToken = client.observe('capture.summary', 'bar');
receive({op: 'state', epoch: 'capture-test', topic: 'capture.summary', seq: 1, status: 'ready',
    data: {running: true, ready: true, recording: true, paused: true, streaming: false}, ageMs: 0});
const captureId = client.actCapture('pause', {}, code => captureResults.push(code));
assert.ok(captureId);
assert.equal(client.actCapture('stop', {}, () => {}), '', 'shared capture conflict guard');
receive({op: 'domain', epoch: 'capture-test', topic: 'capture', busy: false});
assert.equal(client.captureDomain.busy, true, 'old idle event cannot unlock capture');
client.died();
assert.deepEqual(captureResults, ['outcome-unknown']);
sent.length = 0;
receive({op: 'hello', epoch: 'capture-restart'});
assert.ok(sent.some(frame => frame.token === captureToken), 'capture demand replays');
assert.ok(!sent.some(frame => frame.op === 'action'), 'capture writes never replay');
assert.equal(client.states['capture.summary'].status, 'stale');
assert.equal(client.states['capture.summary'].data.recording, true);
assert.equal(client.actCapture('stop', {}, () => {}), '', 'capture must reconcile');
for (const filename of ['ObsStatus.qml', 'RecordingMenu.qml', 'ObsMenu.qml']) {
    assert.ok(!/Process\s*\{/.test(fs.readFileSync(path.join(bar, filename), 'utf8')), filename + ' has no per-panel readers or actions');
}
receive({op: 'state', epoch: 'capture-restart', topic: 'capture.summary', seq: 1, status: 'ready',
    data: {running: false, ready: true, recording: false, paused: false, streaming: false}, ageMs: 0});
const timeoutId = client.actCapture('record', {}, code => captureResults.push(code));
receive({op: 'domain', epoch: 'capture-restart', topic: 'network', busy: false});
assert.equal(client.domain.busy, false, 'capture never holds the network domain busy');
receive({op: 'result', epoch: 'capture-restart', topic: 'capture', id: timeoutId, error: 'outcome-unknown'});
receive({op: 'domain', epoch: 'capture-restart', topic: 'capture', busy: false});
assert.equal(client.actCapture('record', {}, () => {}), '', 'unknown capture outcome requires reconciliation');
receive({op: 'state', epoch: 'capture-restart', topic: 'capture.summary', seq: 1, status: 'ready',
    data: {running: false, ready: true, recording: false, paused: false, streaming: false}, ageMs: 0});
assert.equal(client.actCapture('record', {}, () => {}), '', 'cached capture result is not reconciliation');
receive({op: 'state', epoch: 'capture-restart', topic: 'capture.summary', seq: 2, status: 'ready',
    data: {running: true, ready: true, recording: true, paused: false, streaming: false}, ageMs: 0});
const captureRetry = client.actCapture('stop', {}, () => { throw new Error('destroyed controller callback'); });
assert.ok(captureRetry, 'explicit capture retry only after fresh state');
client.detachAction(captureRetry);
client.died();

const powerSent = [], powerResults = [];
const powerClient = createClient(frame => powerSent.push(frame), () => {});
const powerReceive = frame => powerClient.receive(JSON.stringify(Object.assign({v: 1, epoch: 'power'}, frame)));
powerClient.observe('power.profile', 'brightness', 3);
powerClient.observe('power.profile', 'battery', 5);
powerReceive({op: 'hello'});
assert.deepEqual(powerSent.map(frame => frame.interval), [3, 5]);
assert.equal(powerClient.actPower('profile', {path: 'balanced'}, () => {}), '');
powerReceive({op: 'state', topic: 'power.profile', seq: 1, status: 'ready', data: {available: true, active: 'balanced', profiles: []}, ageMs: 0});
const powerId = powerClient.actPower('profile', {path: 'power-saver'}, code => powerResults.push(code));
assert.ok(powerId);
powerReceive({op: 'domain', topic: 'network', busy: false});
assert.equal(powerClient.domain.busy, false, 'power callbacks must not masquerade as network callbacks');
powerReceive({op: 'result', topic: 'power', id: powerId, error: 'outcome-unknown'});
powerReceive({op: 'domain', topic: 'power', busy: false});
assert.deepEqual(powerResults, ['outcome-unknown']);
assert.equal(powerClient.actPower('profile', {path: 'balanced'}, () => {}), '');
powerReceive({op: 'state', topic: 'power.profile', seq: 1, status: 'ready', data: {}, ageMs: 0});
assert.equal(powerClient.actPower('profile', {path: 'balanced'}, () => {}), '');
powerReceive({op: 'state', topic: 'power.profile', seq: 2, status: 'ready', data: {}, ageMs: 0});
const powerRetry = powerClient.actPower('profile', {path: 'balanced'}, code => powerResults.push(code));
assert.ok(powerRetry);
powerClient.died();
assert.deepEqual(powerResults, ['outcome-unknown', 'outcome-unknown']);
powerClient.releaseOwner('brightness'); powerClient.releaseOwner('battery');
assert.equal(powerClient.count('power.profile'), 0);

// Exercise demand transitions with two screens and overlapping slider writes.
const vm = require('node:vm');
const displaySource = fs.readFileSync(path.join(bar, 'DisplayService.qml'), 'utf8');
function displayFunction(name) {
    const start = displaySource.indexOf('function ' + name + '(');
    assert.ok(start >= 0, name);
    let cursor = displaySource.indexOf('{', start), depth = 1;
    while (depth && ++cursor < displaySource.length) {
        if (displaySource[cursor] === '{') depth++;
        if (displaySource[cursor] === '}') depth--;
    }
    return displaySource.slice(start, cursor + 1);
}
const displayTokens = new Map();
let displaySequence = 0;
const displayContext = {
    observers: [], readInterval: 3, brightnessWriters: [], nightWriters: [],
    brightnessToken: '', nightToken: '', settingsToken: '', warmTokens: {},
    DesktopData: {
        observe(topic, owner, interval) {
            const token = String(++displaySequence);
            displayTokens.set(token, {topic, interval});
            return token;
        },
        release(token) { assert.ok(displayTokens.delete(token), 'release once'); },
        refresh() {}
    }
};
Object.defineProperty(displayContext, 'brightnessPaused', {get: () => displayContext.brightnessWriters.length > 0});
Object.defineProperty(displayContext, 'nightPaused', {get: () => displayContext.nightWriters.length > 0});
displayContext.service = displayContext;
vm.createContext(displayContext);
vm.runInContext(['open', 'close', 'updateDemand', 'pauseBrightness', 'resumeBrightness',
    'refreshBrightness', 'pauseNightlight', 'resumeNightlight', 'releaseWarm'].map(displayFunction).join('\n'), displayContext);
displayContext.open('control-center', 5);
assert.equal(displayTokens.size, 3);
assert.equal(displayContext.readInterval, 5);
displayContext.open('display-one', 3);
displayContext.open('display-two', 3);
assert.equal(displayTokens.size, 3, 'screens share one set of reads');
assert.equal(displayContext.readInterval, 3);
displayContext.pauseBrightness('display-one');
displayContext.pauseBrightness('display-two');
assert.equal(displayTokens.size, 2);
displayContext.resumeBrightness('display-one');
assert.equal(displayTokens.size, 2, 'second writer still excludes reads');
displayContext.close('display-one');
displayContext.resumeBrightness('display-two');
assert.equal(displayTokens.size, 3);
displayContext.close('display-two');
assert.equal(displayContext.readInterval, 5);
displayContext.pauseNightlight('control-center');
assert.equal(displayTokens.size, 2);
displayContext.close('control-center');
displayContext.resumeNightlight('control-center');
assert.equal(displayTokens.size, 0, 'closed and destroyed observers leave no reads');
console.log('display shared demand, intervals and write exclusion passed');
