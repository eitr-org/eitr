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
const service = fs.readFileSync(path.join(bar, 'services/NetworkService.qml'), 'utf8');
assert.equal((service.match(/Process\s*\{/g) || []).length, 1, 'only QR worker remains');
const facade = fs.readFileSync(path.join(bar, 'services/DesktopData.qml'), 'utf8');
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
for (const filename of ['services/ObsStatus.qml', 'panels/RecordingMenu.qml', 'panels/ObsMenu.qml']) {
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
const displaySource = fs.readFileSync(path.join(bar, 'services/DisplayService.qml'), 'utf8');
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


const hardwareFrames = [];
const hardwareClient = createClient(frame => hardwareFrames.push(frame), () => {});
const hardwareOne = hardwareClient.observe('hardware.details', 'screen-one');
const hardwareTwo = hardwareClient.observe('hardware.details', 'control-center-hardware');
function receiveHardware(frame) { hardwareClient.receive(JSON.stringify({v: 1, ...frame})); }
receiveHardware({op: 'hello', epoch: 'hardware-one'});
assert.equal(hardwareFrames.filter(frame => frame.op === 'subscribe').length, 2);
const hardwareData = {identity: {gpu: {available: false}}, sections: [{title: 'CPU', usage: 75}]};
receiveHardware({op: 'state', topic: 'hardware.details', epoch: 'hardware-one', seq: 1,
    status: 'ready', data: hardwareData, ageMs: 0});
assert.deepEqual(hardwareClient.states['hardware.details'].data, hardwareData);
hardwareClient.died();
assert.equal(hardwareClient.states['hardware.details'].status, 'stale');
hardwareClient.release(hardwareOne);
hardwareFrames.length = 0;
receiveHardware({op: 'hello', epoch: 'hardware-two'});
assert.deepEqual(hardwareFrames.filter(frame => frame.op === 'subscribe').map(frame => frame.token), [hardwareTwo]);
receiveHardware({op: 'state', topic: 'hardware.details', epoch: 'hardware-two', seq: 0,
    status: 'loading', data: {}, ageMs: null});
assert.deepEqual(hardwareClient.states['hardware.details'].data, hardwareData, 'restart preserves sections');
hardwareClient.releaseOwner('control-center-hardware');
assert.equal(hardwareClient.count('hardware.details'), 0);
console.log('hardware snapshots, restart replay and subscriber lifetime passed');

const remoteFrames = [];
const remoteClient = createClient(frame => remoteFrames.push(frame), () => {});
const remoteToken = remoteClient.observe('remote.status', 'remote-panels');
remoteClient.observe('remote.availability', 'remote-service');
function receiveRemote(frame) { remoteClient.receive(JSON.stringify({v: 1, ...frame})); }
receiveRemote({op: 'hello', epoch: 'remote-one'});
const remoteData = {allowed: true, tailscale: {installed: false}, streaming: {installed: false}};
receiveRemote({op: 'state', topic: 'remote.status', epoch: 'remote-one', seq: 1,
    status: 'ready', data: remoteData, ageMs: 0, inFlight: false, pending: false});
receiveRemote({op: 'state', topic: 'remote.status', epoch: 'remote-one', seq: 1,
    status: 'ready', data: remoteData, ageMs: 0, inFlight: true, pending: true});
assert.equal(remoteClient.states['remote.status'].inFlight, true);
assert.equal(remoteClient.states['remote.status'].pending, true);
remoteClient.died();
assert.deepEqual(remoteClient.states['remote.status'].data, remoteData);
remoteClient.release(remoteToken);
remoteFrames.length = 0;
receiveRemote({op: 'hello', epoch: 'remote-two'});
assert.deepEqual(remoteFrames.filter(frame => frame.op === 'subscribe').map(frame => frame.topic), ['remote.availability']);
remoteClient.releaseOwner('remote-service');
assert.equal(remoteClient.count('remote.availability'), 0);
const remoteService = fs.readFileSync(path.join(bar, 'services/RemoteAccessService.qml'), 'utf8');
assert.doesNotMatch(remoteService, /\b(?:Process|Timer)\s*\{/);
assert.match(remoteService, /Component.onDestruction: DesktopData.releaseOwner\(service\)/);
console.log('remote state, read activity, restart and closed-panel replay passed');

const scopedFrames = [];
const scoped = createClient(frame => scopedFrames.push(frame), () => {});
scoped.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'scoped'}));
let cityReply = null;
const cancelledCity = scoped.queryWeather('city', {city: {}}, 'closed', (error, data) => { cityReply = data; });
const retainedCity = scoped.queryWeather('city', {city: {}}, 'open', (error, data) => { cityReply = data; });
scoped.releaseOwner('closed');
assert(scopedFrames.some(frame => frame.op === 'cancel' && frame.id === cancelledCity));
scoped.receive(JSON.stringify({v: 1, op: 'reply', topic: 'weather', epoch: 'scoped', id: cancelledCity, data: {temp: 'old'}}));
assert.equal(cityReply, null);
scoped.receive(JSON.stringify({v: 1, op: 'reply', topic: 'weather', epoch: 'scoped', id: retainedCity, data: {temp: 'new'}}));
assert.equal(cityReply.temp, 'new');
scoped.queryWeather('search', {query: 'city'}, 'open', error => { cityReply = error; });
scoped.died();
assert.equal(cityReply, 'broker-unavailable');
const weatherMenu = fs.readFileSync(path.join(bar, 'panels/WeatherMenu.qml'), 'utf8');
const aiMenu = fs.readFileSync(path.join(bar, 'panels/AiUsageMenu.qml'), 'utf8');
assert.doesNotMatch(weatherMenu, /\bProcess\s*\{/);
assert.doesNotMatch(aiMenu, /\b(?:Process|Timer)\s*\{/);
assert.match(aiMenu, /if \(opened\)[\s\S]*DesktopData.observe\("ai.usage", menu\)/);
console.log('weather request ownership and AI open-only demand passed');

// Exercise the shell-owned notification guard through repeated shared snapshots.
const updateShell = fs.readFileSync(path.join(bar, 'services/UpdatesStatus.qml'), 'utf8');
const announcementBody = updateShell.match(/function announceUpdates\(\) \{([\s\S]*?)\n    \}/)[1];
const announcementContext = {updates: {count: 0}, announcedUpdates: 0, updatesSize: '',
    Quickshell: {shellDir: '/fixture', execDetached: command => announcements.push(command)}};
const announcements = [];
vm.createContext(announcementContext);
for (const count of [3, 3, 3, 5, 5, 0, 0, 2, 2]) {
    announcementContext.updates = {count};
    vm.runInContext('(function() {' + announcementBody + '})()', announcementContext);
}
assert.deepEqual(announcements.map(command => command[2]), ['3', '5', '2']);
const updateClient = createClient(() => {}, () => {});
updateClient.observe('updates.status', 'shell');
updateClient.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'updates'}));
updateClient.receive(JSON.stringify({v: 1, op: 'state', topic: 'updates.status', epoch: 'updates', seq: 1,
    status: 'ready', data: {state: 'ready', count: 0}, ageMs: 0, inFlight: false}));
assert.equal(updateClient.states['updates.status'].data.count, 0);
updateClient.receive(JSON.stringify({v: 1, op: 'state', topic: 'updates.status', epoch: 'updates', seq: 2,
    status: 'stale', error: 'offline', data: {state: 'ready', count: 0}, ageMs: 1, inFlight: false}));
assert.equal(updateClient.states['updates.status'].error, 'offline');
assert.equal(updateClient.states['updates.status'].status, 'stale');

// Execute production lifetime handlers with view-only dependencies replaced.
// QML Loader destruction is exercised separately by the offscreen harness.
function lifetimeBody(source, marker) {
    const start = source.indexOf(marker);
    assert.notEqual(start, -1, marker);
    const tail = source.slice(start + marker.length).trimStart();
    if (!tail.startsWith('{')) return tail.split('\n')[0];
    let depth = 0;
    for (let cursor = 0; cursor < tail.length; cursor++) {
        if (tail[cursor] === '{') depth++;
        if (tail[cursor] === '}' && --depth === 0) return tail.slice(1, cursor);
    }
    assert.fail('unclosed handler ' + marker);
}
function lifetimeContext(relative, values, functions = []) {
    const source = fs.readFileSync(path.join(bar, relative), 'utf8');
    const context = vm.createContext(values);
    for (const name of functions) {
        const signature = source.match(new RegExp('function ' + name + '\\(([^)]*)\\)'));
        assert.ok(signature, name);
        vm.runInContext('function ' + name + '(' + signature[1] + ') {' +
            lifetimeBody(source, signature[0]) + '}', context);
    }
    return {context, source, run(marker) { vm.runInContext(lifetimeBody(source, marker), context); }};
}
{
    let epoch = 0;
    const wire = new Map();
    const frames = [];
    const data = createClient(frame => {
        frames.push(frame);
        if (frame.op === 'subscribe') {
            assert.equal(wire.has(frame.token), false, 'subscribe exactly once per epoch');
            wire.set(frame.token, frame.topic);
        }
        if (frame.op === 'unsubscribe') assert.equal(wire.delete(frame.token), true, 'unsubscribe exactly once');
    }, () => {});
    const facade = {...data, client: data};
    function hello() {
        data.receive(JSON.stringify({v: 1, op: 'hello', epoch: String(++epoch)}));
        assert.equal(wire.size, Object.keys(data.tokens).length, 'replay has no duplicates');
    }
    function restart() { data.died(); wire.clear(); hello(); hello(); }
    hello();
    const noop = () => {};
    const display = lifetimeContext('services/DisplayService.qml', {
        DesktopData: facade, observers: [], readInterval: 3, brightnessToken: '', nightToken: '', settingsToken: '',
        brightnessPaused: false, nightPaused: false, brightnessWriters: [], nightWriters: [], warmTokens: {},
    }, ['open', 'close', 'updateDemand', 'resumeBrightness', 'resumeNightlight', 'refreshBrightness']);
    display.context.service = display.context;
    const power = lifetimeContext('services/PowerService.qml', {DesktopData: facade}, ['observe', 'release']).context;
    const network = lifetimeContext('services/NetworkService.qml', {
        DesktopData: facade, observers: {}, actionOwner: null, qrOwner: null,
    }, ['observe', 'release', 'updateObservers', 'detach']).context;
    const baseline = data.observe('network.summary', 'shell');
    for (const name of ['BatteryMenu', 'BrightnessMenu', 'ControlCenter', 'WifiMenu', 'WeatherMenu', 'SystemMonitorMenu', 'AiUsageMenu', 'ObsMenu']) {
        const owner = {};
        const panel = lifetimeContext('panels/' + name + '.qml', {
            DesktopData: facade, PowerService: power, DisplayService: display.context,
            menu: owner, center: owner, opened: false, visible: true,
            powerTokens: [], powerActionId: '', networkToken: '', accountToken: '', detailsToken: '', latencyToken: '',
            defaultToken: '', hardwareToken: '', usageToken: '', optionToken: '', actionId: '', optionId: '',
            wifiControl: network, networkService: network, chatOpen: false, chatView: {reset: noop},
            scheduleDirty: false, editingSchedule: false, settingsFor: '',
            defaultWeatherData: {}, city: null, contentViewport: {contentY: 0},
            password: {text: ''}, clearEnterprise: noop, closeShare: noop, cancelSearch: noop,
            refresh: noop, receiveUsage: noop, receiveSnapshot: noop, receiveDetails: noop,
            refreshDisplays: noop, chatStatus: {}, organizationQuery: {}, channelQuery: {}, loadStyle: noop,
            loadOptions() { if (!panel.context.optionToken) panel.context.optionToken = data.observe('capture.options', owner); },
        }, name === 'WifiMenu' ? ['syncDemand'] : []);
        Object.assign(owner, {refresh: noop, loadStyle: noop});
        for (let cycle = 0; cycle < 20; cycle++) {
            panel.context.opened = true;
            panel.run('onOpenedChanged:');
            if (name === 'BrightnessMenu') display.context.open(owner);
            if (name === 'ControlCenter') {
                display.context.open(owner, 5);
                // Switching pages has no handler, so it cannot add data demand.
                assert(!panel.source.includes('onPageChanged:'), 'Control Center page demand');
            }
            restart();
            // Pending replies never arrive before close/destruction.
            const query = data.queryWeather('search', {query: 'fixture'}, owner, error => assert.equal(error, 'broker-unavailable'));
            if (name !== 'WeatherMenu') data.cancelQuery(query);
            if (cycle % 2 === 0) {
                panel.context.opened = false;
                panel.run('onOpenedChanged:');
                assert.equal(Object.keys(data.tokens).length, 1, name + ' closes to baseline');
            } else {
                data.died(); wire.clear();
            }
            panel.run('Component.onDestruction:');
            hello();
            assert.equal(Object.keys(data.tokens).length, 1, name + ' destroys to baseline');
            assert.equal(wire.size, 1, name + ' wire baseline');
            assert.equal(Object.keys(network.observers).length, 0, 'network service releases owner');
            assert.equal(display.context.observers.length, 0, 'display service releases owner');
        }
    }
    data.release(baseline);
    assert.equal(wire.size, 0);
    console.log('production panel and Control Center lifetime handlers: 20 cycles, pending queries, destruction and reconnect passed');
}

{
    const frames = [];
    const data = createClient(frame => frames.push(frame), () => {});
    data.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'catalog-one'}));
    let replies = 0;
    const query = data.queryCatalog('index', {kind: 'themes'}, 'catalog-window', () => replies++);
    data.releaseOwner('catalog-window');
    assert.equal(frames.at(-1).op, 'cancel');
    assert.equal(frames.at(-1).topic, 'catalog');
    data.receive(JSON.stringify({v: 1, op: 'reply', topic: 'catalog', id: query, epoch: 'catalog-one', data: {items: []}}));
    assert.equal(replies, 0);
    data.queryCatalog('install', {kind: 'themes', ids: ['fixture-theme']}, 'catalog-window', error => assert.equal(error, 'broker-unavailable'));
    const count = frames.length;
    data.died();
    data.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'catalog-two'}));
    assert.equal(frames.length, count, 'catalog actions are never replayed after reconnect');
}
