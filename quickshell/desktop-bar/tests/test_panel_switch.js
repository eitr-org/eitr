const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const source = fs.readFileSync(`${__dirname}/../shell.qml`, 'utf8');
const context = {pendingPanel: null, pendingOverview: false, overview: {opened: false, visible: false}, dockPanels: []};
vm.createContext(context);
for (const name of ['closePanels', 'showPanel', 'togglePanel', 'toggleOverview', 'finishPanelSwitch']) {
    const match = source.match(new RegExp(`function ${name}\\([^)]*\\) \\{[\\s\\S]*?\\n                \\}`));
    assert.ok(match, name);
    vm.runInContext(match[0], context);
}
const first = {opened: true, visible: true};
const second = {opened: false, visible: false};
const third = {opened: false, visible: false};
context.dockPanels = [first, second, third];
context.showPanel(second);
assert.equal(first.opened, false);
assert.equal(second.opened, false); // First is still animating closed.
context.finishPanelSwitch();
assert.equal(second.opened, false);
context.showPanel(third); // Latest click wins during the close animation.
first.visible = false;
context.finishPanelSwitch();
assert.equal(third.opened, true);
assert.equal(second.opened, false);
third.visible = true;
context.togglePanel(third);
assert.equal(third.opened, false);
context.togglePanel(second);
context.togglePanel(second); // Clicking a queued panel again cancels it.
third.visible = false;
context.finishPanelSwitch();
assert.equal(second.opened, false);
assert.equal(context.pendingPanel, null);
first.visible = true;
context.toggleOverview();
assert.equal(context.pendingOverview, true);
assert.equal(context.overview.opened, false);
first.visible = false;
context.finishPanelSwitch();
assert.equal(context.overview.opened, true);
context.overview.visible = true;
context.showPanel(second);
assert.equal(context.overview.opened, false);
assert.equal(second.opened, false);
context.overview.visible = false;
context.finishPanelSwitch();
assert.equal(second.opened, true);
console.log('Panel switching: waits for dismissal, latest click wins, cancellation passed');
