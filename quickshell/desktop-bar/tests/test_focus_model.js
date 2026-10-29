const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const context = vm.createContext({});
vm.runInContext(fs.readFileSync(path.join(__dirname, '../FocusModel.js'), 'utf8').replace('.pragma library', ''), context);
const tabs = clients => JSON.parse(JSON.stringify(context.tabsForMonitor(clients, 0)));
const windows = [
    {address: '0x1', monitor: 0, title: 'Terminal', mapped: true, hidden: false, focusHistoryID: 0},
    {address: '0x2', monitor: 0, title: '<script>literal</script>', mapped: true, hidden: true, focusHistoryID: 1},
    {address: '0x3', monitor: 1, class: 'Browser', mapped: true, hidden: false, focusHistoryID: 2},
    {address: '0x4', monitor: 0, title: 'Closed', mapped: false}
];
assert.deepEqual(tabs([]), []);
assert.deepEqual(tabs(windows).map(tab => tab.address), ['0x1', '0x2']);
assert.equal(tabs(windows)[0].active, true);
assert.equal(tabs(windows)[1].pane, false);
assert.equal(tabs(windows)[1].title, '<script>literal</script>');
windows[1].hidden = false;
windows[1].focusHistoryID = 0;
windows[0].focusHistoryID = 1;
assert.deepEqual(tabs(windows).map(tab => tab.active), [false, true]);
assert.equal(tabs(windows).filter(tab => tab.pane).length, 2);
windows.splice(1, 1);
assert.equal(tabs(windows).length, 1);
assert.equal(context.tabsForMonitor(windows, 1)[0].title, 'Browser');
console.log('Focus strip model: monitors, focus, split, close and literal titles passed');
