const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const geometry = {};
vm.runInNewContext(fs.readFileSync(path.join(__dirname, '../MonitorGeometry.js'), 'utf8').replace('.pragma library', ''), geometry);
const monitors = [{name: 'DP-1', width: 2560, height: 1440, x: -2560, y: 0, scale: 1},
    {name: 'HDMI-A-1', width: 1920, height: 1080, x: 0, y: 0, scale: 1, disabled: true}];
const screens = geometry.screens(monitors, [], null);
assert.equal(screens[1].disabled, true);
const fitted = geometry.fit(screens, 400, 180, 16);
for (const screen of fitted) {
    assert(screen.x >= 16 && screen.y >= 16);
    assert(screen.x + screen.width <= 384.001 && screen.y + screen.height <= 164.001);
}
assert(Math.abs(fitted[0].x + fitted[0].width - fitted[1].x) < 0.001);
const single = geometry.fit([screens[0]], 400, 180, 16)[0];
assert(Math.abs(single.x + single.width / 2 - 200) < 0.001);
assert(Math.abs(single.y + single.height / 2 - 90) < 0.001);
for (const transform of [1, 3, 5, 7]) {
    const rotated = geometry.screens(monitors, [], {name: 'DP-1', transform, scale: 2, mode: '3840x2160@60', position: '-1080x-1920'})[0];
    assert.equal(rotated.width, 1080);
    assert.equal(rotated.height, 1920);
    assert.equal(rotated.x, -1080);
    assert.equal(rotated.y, -1920);
    assert.equal(rotated.pending, true);
}
const applied = geometry.screens(monitors, [{name: 'DP-1', mode: '1920x1080@60', scale: 1.5, transform: 0, position: '0x40'}], null)[0];
assert.equal(applied.width, 1280);
assert.equal(applied.y, 40);
assert.equal(applied.pending, false);
assert.equal(geometry.fit([], 400, 180, 16).length, 0);
console.log('Monitor geometry: topology, scaling, rotation, trial, negative offsets and bounds passed');
