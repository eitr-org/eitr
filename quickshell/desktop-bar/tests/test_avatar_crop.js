const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const path = require('path');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../AvatarCrop.js'), 'utf8').replace('.pragma library', ''), context);
for (const [width, height] of [[800, 400], [400, 800], [512, 512]]) {
    for (const zoom of [1, 2, 4]) {
        for (const offset of [-10000, 0, 10000]) {
            const crop = context.square(width, height, 200, zoom, offset, offset);
            assert(crop.x >= -0.0001 && crop.y >= -0.0001);
            assert(crop.x + crop.size <= width + 0.0001);
            assert(crop.y + crop.size <= height + 0.0001);
            assert(Math.abs(crop.size - Math.min(width, height) / zoom) < 0.0001);
        }
    }
}
const crop = context.square(800, 400, 200, 1, 0, 0);
assert.equal(crop.x, 200);
assert.equal(crop.y, 0);
assert.equal(crop.size, 400);
console.log('avatar crop maths passed');
