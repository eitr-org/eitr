const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../shell.qml`, 'utf8');
const expression = source.match(/readonly property bool expanded: ([^\n]+)/)[1];
const context = {centeredLayout: true, shell: {barPinned: false, barPointerHeld: false},
    hoverExpanded: false, panelOpen: false, pendingPanel: null};
const expanded = () => vm.runInNewContext(expression, context);
assert.equal(expanded(), false);
for (const reason of ['hoverExpanded', 'panelOpen', 'pendingPanel']) {
    context[reason] = reason === 'pendingPanel' ? {} : true;
    assert.equal(expanded(), true);
    context[reason] = reason === 'pendingPanel' ? null : false;
}
for (const reason of ['barPinned', 'barPointerHeld']) {
    context.shell[reason] = true;
    assert.equal(expanded(), true);
    context.shell[reason] = false;
}
context.centeredLayout = false;
assert.equal(expanded(), true);
assert.ok(source.includes('interval: 350'));
assert.ok(source.includes('anchors.right: bar.centeredLayout ? barPin.left : barCapture.left'));
// The recording/dictation indicator sits between the pin (or media) and the clock.
assert.ok(source.includes('id: barCapture\n                        anchors.right: centerInfo.left'));
assert.ok(source.includes('id: barPin\n                        visible: bar.centeredLayout && bar.expanded\n                        anchors.right: barCapture.left'));
assert.ok(source.includes('id: barPin'));
assert.equal((source.match(/BarSection \{/g) || []).length, 2);
const corners = fs.readFileSync(`${__dirname}/../BarSection.qml`, 'utf8');
for (const edge of ['top', 'bottom', 'left', 'right']) {
    const radius = corner => vm.runInNewContext(corners.match(new RegExp(`${corner}: ([^\\n]+)`))[1], {edge, radius: 6});
    assert.equal(radius('topLeftRadius'), edge === 'top' || edge === 'left' ? 0 : 6);
    assert.equal(radius('topRightRadius'), edge === 'top' || edge === 'right' ? 0 : 6);
    assert.equal(radius('bottomLeftRadius'), edge === 'bottom' || edge === 'left' ? 0 : 6);
    assert.equal(radius('bottomRightRadius'), edge === 'bottom' || edge === 'right' ? 0 : 6);
}
console.log('Centered bar hover, pin, panel and drag checks passed');
