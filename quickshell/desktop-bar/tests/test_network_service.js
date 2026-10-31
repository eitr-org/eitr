const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {createOwner, glyph} = require('../NetworkStatus.js');
const fixtures = require('./fixtures/network.json');

function harness() {
    const launches = {summary: 0, details: 0, latency: 0};
    const stops = {summary: 0, details: 0, latency: 0};
    const owner = createOwner(topic => { launches[topic]++; }, topic => { stops[topic]++; }, () => {});
    function complete(topic, result, code = 0) { owner.finish(topic, JSON.stringify(result), code); }
    function screen() {
        const tokens = [];
        return {
            open(topic = 'details') { const token = owner.observe(this, topic); tokens.push(token); return token; },
            destroy() { tokens.forEach(token => owner.release(token)); },
            close() { this.destroy(); }
        };
    }
    return {owner, launches, stops, complete, screen};
}

// Contract snapshots: empty hardware is ready, a missing backend is unavailable.
for (const name of ['noAdapter', 'blocked', 'wired', 'connected', 'networkmanager']) {
    const {owner, complete} = harness();
    owner.observe('fixture');
    complete('details', fixtures[name]);
    assert.equal(owner.topics.details.status, 'ready', name);
    assert.deepEqual(owner.topics.details.data, fixtures[name]);
}
assert.equal(glyph(fixtures.blocked), '󰤮');
assert.equal(glyph(fixtures.connected), '󰤥');
assert.equal(glyph(fixtures.networkmanager), '󰤨');
const networks = fixtures.connected.devices[0].networks;
assert.equal(networks.filter(network => network.connected).length, 1);
assert.equal(networks.filter(network => network.known && !network.connected).length, 1);
assert.equal(networks.filter(network => !network.known && !network.connected).length, 1);
assert.equal(networks[1].strength, null);

{
    const {owner, launches, stops, complete, screen} = harness();
    const first = screen();
    const second = screen();
    const controlCenter = screen();
    const token = first.open();
    second.open(); controlCenter.open();
    assert.equal(owner.count('details'), 3);
    assert.equal(launches.details, 1);
    for (let refresh = 0; refresh < 10; refresh++) owner.refresh('details');
    complete('details', fixtures.connected);
    assert.equal(launches.details, 2, 'one pending refresh across screens');
    complete('details', fixtures.connected);
    first.open('latency'); second.open('latency');
    assert.equal(launches.latency, 1);
    complete('latency', fixtures.latency);
    complete('latency', fixtures.latency);
    first.close(); owner.release(token); first.destroy();
    assert.equal(owner.count('details'), 2, 'release is idempotent');
    second.destroy();
    assert.equal(owner.count('latency'), 0);
    assert.equal(owner.count('details'), 1, 'CC keeps details, never probes');
    controlCenter.destroy();
    assert.equal(owner.count('details'), 0);
    const previous = {...launches};
    for (let tick = 0; tick < 10; tick++) { owner.refresh('details'); owner.refresh('latency'); }
    assert.deepEqual(launches, previous, 'closed panels never poll');
    assert.equal(owner.topics.details.running, false);
    assert.equal(owner.topics.latency.running, false);
    first.open();
    assert.equal(launches.details, previous.details + 1, 'refresh on reopen');
    assert.deepEqual(owner.topics.details.data, fixtures.connected, 'cached data remains available');
}
{
    const {owner, launches, complete, screen} = harness();
    const panel = screen(); panel.open(); panel.close(); panel.open();
    complete('details', fixtures.blocked); // cancelled reader completing after reopen
    assert.equal(owner.topics.details.updatedAt, 0, 'discard cancelled result');
    assert.equal(launches.details, 2);
    complete('details', fixtures.connected);
    owner.refresh('details'); complete('details', fixtures.unavailable, 1);
    assert.equal(owner.topics.details.status, 'stale');
    assert.deepEqual(owner.topics.details.data, fixtures.connected);
    owner.refresh('details'); owner.finish('details', 'invalid', 1);
    assert.equal(owner.topics.details.status, 'stale');
    owner.refresh('details'); complete('details', fixtures.noAdapter);
    assert.equal(owner.topics.details.status, 'ready');
    assert.equal(owner.topics.details.error, '');
}
{
    const {owner, complete} = harness();
    owner.observe('panel'); complete('details', fixtures.unavailable, 1);
    assert.equal(owner.topics.details.status, 'unavailable');
    owner.refresh('details'); owner.finish('details', '{}', 0);
    assert.equal(owner.topics.details.status, 'error');
}
// Wiring guards: all screens share one service, consumer lifetimes release tokens.
const bar = path.resolve(__dirname, '..');
const shell = fs.readFileSync(path.join(bar, 'shell.qml'), 'utf8');
assert.equal((shell.match(/NetworkService\s*\{/g) || []).length, 1);
assert.ok(shell.indexOf('NetworkService {') < shell.indexOf('    Variants {'));
for (const name of ['WifiMenu', 'ControlCenter']) {
    const qml = fs.readFileSync(path.join(bar, 'panels', name + '.qml'), 'utf8');
    assert.ok(qml.includes('Component.onDestruction:'));
    assert.ok(qml.includes('.release('));
    assert.ok(qml.includes('.observe('));
    assert.ok(!qml.includes('wifi-popup.py'));
}
console.log('network contract, refresh, failure and multi-screen demand tests passed');
