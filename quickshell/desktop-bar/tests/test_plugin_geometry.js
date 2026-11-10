const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../PluginGeometry.js'), 'utf8').replace(/^\.pragma library\s*/, ''), context);
for (const bounds of [
    {x: 0, y: 30, width: 1920, height: 1050},
    {x: 60, y: 0, width: 1860, height: 1080},
    {x: 0, y: 0, width: 1920, height: 1050},
    {x: 0, y: 0, width: 1860, height: 1080}
]) {
    const fitted = context.fit({x: -200, y: 3000, width: 317, height: 209}, bounds, 96, 96, 6);
    assert.ok(fitted.x >= bounds.x && fitted.y >= bounds.y);
    assert.ok(fitted.x + fitted.width <= bounds.x + bounds.width);
    assert.ok(fitted.y + fitted.height <= bounds.y + bounds.height);
    assert.equal(fitted.width % 6, 0);
    assert.equal(fitted.height % 6, 0);
}
const tiny = context.fit({x: 200, y: 200, width: 50, height: 50}, {x: 0, y: 0, width: 800, height: 600}, 144, 96, 6);
assert.equal(tiny.width, 144);
assert.equal(tiny.height, 96);
console.log('Plugin widget geometry passed');

const spectrum = {};
vm.createContext(spectrum);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../Spectrum.js'), 'utf8').replace(/^\.pragma library\s*/, ''), spectrum);
for (const count of [8, 16, 31, 48, 128]) {
    const values = spectrum.resample([0, .25, .5, 1], count);
    assert.equal(values.length, count);
    assert.ok(values.every(value => value >= 0 && value <= 1));
    assert.ok(Math.abs(values.reduce((sum, level) => sum + level, 0) / count - .4375) < 1e-10);
    assert.ok(spectrum.resample([], count).every(value => value === 0));
}
assert.deepEqual(Array.from(spectrum.resample([0, 0, 1, 1], 2)), [0, 1]);
assert.deepEqual(Array.from(spectrum.resample([.25, .75], 4)), [.25, .25, .75, .75]);
assert.equal(spectrum.frame('bad;data'), null);
assert.equal(spectrum.frame('1;2;3;'), null);
assert.equal(spectrum.count(1000, 1, 60), 60);
assert.equal(spectrum.count(-1, 8, 128), 8);
assert.equal(spectrum.count(NaN, 1, 60), 1);
console.log('Spectrum resampling and limits passed');

const media = {bars: 4, frameRate: 30, plugin: false, smoothing: false};
const plugin = {bars: 96, frameRate: 60, plugin: true, smoothing: true};
assert.equal(JSON.stringify(spectrum.configuration([media])), JSON.stringify({bars: 4, fps: 30, smoothing: false}));
assert.equal(JSON.stringify(spectrum.configuration([media, plugin])), JSON.stringify({bars: 96, fps: 60, smoothing: false}));
assert.equal(JSON.stringify(spectrum.configuration([media])), JSON.stringify({bars: 4, fps: 30, smoothing: false}));
assert.equal(spectrum.configuration([plugin]).smoothing, true);
assert.deepEqual(Array.from(spectrum.smooth([1, 0], [0, 1])), [.5, .5]);

// Sub-grid pointer events must accumulate into smooth, visible motion before save.
const usable = {x: 0, y: 30, width: 1920, height: 1050};
let drag = {x: 24, y: 30, width: 900, height: 180};
for (let pixel = 0; pixel < 19; pixel++) {
    drag = context.fit(context.delta(drag, 1, 1, false), usable, 96, 96, 1);
}
assert.equal(drag.x, 43);
assert.equal(drag.y, 49);
const saved = context.fit(drag, usable, 96, 96, 6);
assert.equal(saved.x, 42);
assert.equal(saved.y, 48);
assert.equal(context.delta(saved, 90, 18, true).width, 990);
for (const factor of [0.9, 1.1, 0, 100, 0.001]) {
    const sized = context.scale(saved, usable, 96, 96, factor);
    assert.ok(Math.abs(sized.width / sized.height - 5) < .03);
    assert.ok(sized.x >= usable.x && sized.y >= usable.y);
    assert.ok(sized.x + sized.width <= usable.width);
    assert.ok(sized.y + sized.height <= usable.y + usable.height);
}
const larger = context.scale({x: 400, y: 300, width: 400, height: 200}, usable, 96, 96, 1.1);
assert.equal(larger.width, 440);
assert.equal(larger.height, 220);
assert.equal(larger.x + larger.width / 2, 600);
assert.equal(larger.y + larger.height / 2, 400);

// A gesture always starts from the press geometry, including reversals at a boundary.
const pressGeometry = {x: 120, y: 60, width: 240, height: 120};
for (const offset of [1, 2, 19, 8000, 18, -8000, 0]) {
    const result = context.fit(context.delta(pressGeometry, offset, 0, false), usable, 96, 96, 1);
    assert.equal(result.x, Math.max(usable.x, Math.min(usable.width - 240, 120 + offset)));
    assert.equal(pressGeometry.x, 120);
}

// A rotated widget's surface is the bounding box of the turned rectangle, kept on screen.
const screen = {x: 0, y: 30, width: 1920, height: 1050};
const upright = {x: 400, y: 300, width: 300, height: 100};
assert.equal(JSON.stringify(context.rotatedBox(upright, 0, screen)), JSON.stringify(upright));
assert.equal(JSON.stringify(context.rotatedBox(upright, 90, screen)), JSON.stringify({x: 500, y: 200, width: 100, height: 300}));
assert.equal(JSON.stringify(context.rotatedBox(upright, 180, screen)), JSON.stringify(upright));
const diagonal = context.rotatedBox(upright, 45, screen);
assert.equal(diagonal.width, Math.ceil(400 * Math.SQRT1_2));
assert.equal(diagonal.width, diagonal.height);
assert.ok(Math.abs(diagonal.x + diagonal.width / 2 - 550) <= 1 && Math.abs(diagonal.y + diagonal.height / 2 - 350) <= 1);
const cornered = context.rotatedBox({x: 0, y: 30, width: 400, height: 100}, 90, screen);
assert.ok(cornered.x >= screen.x && cornered.y >= screen.y);
for (const [angle, snapped] of [[0, 0], [2, 0], [3, 0], [4, 4], [87, 90], [93, 90], [94, 94], [183, 180], [268, 270], [357, 0], [359, 0], [360, 0], [-90, 270], [45.4, 45]])
    assert.equal(context.snapRotation(angle), snapped);
assert.equal(JSON.stringify(context.clampToScreen({x: 1800, y: 900, width: 300, height: 200}, 1280, 720)), JSON.stringify({x: 980, y: 520, width: 300, height: 200}));
assert.equal(JSON.stringify(context.clampToScreen({x: 10, y: 10, width: 4000, height: 200}, 1280, 720)), JSON.stringify({x: 0, y: 10, width: 1280, height: 200}));
assert.equal(JSON.stringify(context.beside({x: 24, y: 24, width: 300, height: 200}, 1920, 1080, 24)), JSON.stringify({x: 48, y: 48, width: 300, height: 200}));
assert.equal(JSON.stringify(context.beside({x: 1620, y: 880, width: 300, height: 200}, 1920, 1080, 24)), JSON.stringify({x: 1596, y: 856, width: 300, height: 200}));
console.log('Plugin widget rotation, snapping and copies passed');
