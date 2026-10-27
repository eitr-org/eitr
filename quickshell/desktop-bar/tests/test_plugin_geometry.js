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
