const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const context = {};
vm.createContext(context);
vm.runInContext(fs.readFileSync(path.join(__dirname, '../BarGeometry.js'), 'utf8').replace(/^\.pragma library\s*/, ''), context);

// Bottom bars must add their window offset before interpreting an upward drag.
const fromBottom = context.screenPoint({x: 1280, y: -1020}, 'bottom', 2560, 1080, 2560, 30);
assert.equal(context.nearestEdge(fromBottom, 2560, 1080), 'top');
const fromTop = context.screenPoint({x: 1280, y: 1040}, 'top', 2560, 1080, 2560, 30);
assert.equal(context.nearestEdge(fromTop, 2560, 1080), 'bottom');
const fromRight = context.screenPoint({x: -2460, y: 540}, 'right', 2560, 1080, 60, 1080);
assert.equal(context.nearestEdge(fromRight, 2560, 1080), 'left');
assert.equal(context.nearestEdge({x: 2500, y: 540}, 2560, 1080), 'right');
assert.equal(context.nearestEdge({x: 1280, y: 150}, 2560, 1080), 'top');
console.log('Bar geometry checks passed');

const shell = (fs.readFileSync(path.join(__dirname, '../shell.qml'), 'utf8') + fs.readFileSync(path.join(__dirname, '../BarWindow.qml'), 'utf8')).replace(/\bhost\b/g, 'shell');
const cycle = shell.match(/else if \(button === Qt.RightButton\) updateBarSetting\("layout", ([^;]+)\);/)[1];
for (const [barLayout, expected] of [['unified', 'centered'], ['centered', 'notch'], ['notch', 'islands'], ['islands', 'unified']]) {
    assert.equal(vm.runInNewContext(cycle, {barLayout}), expected);
}

assert.match(shell, /tabStripThickness: 7/);
assert.match(shell, /id: leadingTab/);
assert.match(shell, /id: trailingTab/);
