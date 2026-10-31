const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../panels/ControlCenter.qml`, 'utf8');
const clearance = source.match(/readonly property real edgeClearance: ([^\n]+)/)[1];
const height = source.match(/\n    implicitHeight: ([^\n]+)/)[1];
const offset = source.match(/\n    leadingOffset: ([^\n]+)/)[1];
for (const barPosition of ['top', 'bottom', 'left', 'right']) {
    const context = {barPosition, screenMargins: [10, 11, 12, 13], detached: false,
        hostWindow: {height: 1080}, strip: {height: 30}};
    context.edgeClearance = vm.runInNewContext(clearance, context);
    const h = vm.runInNewContext(height, context);
    const y = vm.runInNewContext(offset, context);
    if (barPosition === 'top') assert.equal(1080 - 30 - h, 12);
    else if (barPosition === 'bottom') assert.equal(1080 - 30 - h, 10);
    else { assert.equal(y, 10); assert.equal(1080 - y - h, 12); }
    context.detached = true;
    assert.equal(vm.runInNewContext(height, context), barPosition === 'top' || barPosition === 'bottom' ? 1050 : 1080);
    assert.equal(vm.runInNewContext(offset, context), 0);
}
console.log('Control Center outer-gap checks passed on every edge; centered sizing unchanged');
