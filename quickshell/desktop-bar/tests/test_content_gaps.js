const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../PanelSurface.qml`, 'utf8');
const style = fs.readFileSync(`${__dirname}/../PanelStyle.js`, 'utf8');
const multiplier = Number(style.match(/var contentGapMultiplier = (\d+);/)[1]);
assert.equal(multiplier, 2);
for (const [name, index] of [['top', 0], ['right', 1], ['bottom', 2], ['left', 3]]) {
    const code = source.match(new RegExp(`readonly property real ${name}Padding: ([^\\n]+)`))[1];
    for (const gap of [0, 4, 12, 20]) {
        const gaps = [7, 9, 11, 13]; gaps[index] = gap;
        assert.equal(vm.runInNewContext(code, {outerGaps: gaps, PanelStyle: {contentGapMultiplier: multiplier}}), gap * 2);
    }
}
const contents = source.split('objectName: "panelContentFrame"')[1];
const expression = key => contents.match(new RegExp(`\\n            ${key}: ([^\\n]+)`))[1];
for (const edge of ['top', 'bottom', 'left', 'right']) {
    for (const detached of [false, true]) {
        const vertical = edge === 'left' || edge === 'right';
        const surface = {width: 500, height: 600, edge, vertical,
            leftPadding: 13, rightPadding: 11, topPadding: 10, bottomPadding: 12,
            leadingBodyInset: detached ? 0 : 14, trailingBodyInset: detached ? 0 : 14};
        const context = {surface, reveal: {width: 500, height: 600}};
        const evaluate = key => vm.runInNewContext(expression(key), context);
        const x = evaluate('x'), y = evaluate('y');
        assert.equal(x - (vertical ? 0 : surface.leadingBodyInset), 13);
        assert.equal(y - (vertical ? surface.leadingBodyInset : 0), 10);
        assert.equal(surface.width - x - evaluate('width') - (vertical ? 0 : surface.trailingBodyInset), 11);
        assert.equal(surface.height - y - evaluate('height') - (vertical ? surface.trailingBodyInset : 0), 12);
    }
}
console.log('Panel content doubles all four outer gaps without moving the background');
