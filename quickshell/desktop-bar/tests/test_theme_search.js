const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../AppearancePicker.qml'), 'utf8');
const body = source.split('function search(value) {')[1].split('\n    }')[0];
const context = {
    allItems: [{name: 'Jade'}, {name: 'Afterglow'}, {name: 'Daylight'}],
    selectedIndex: 2,
};
vm.createContext(context);
function search(value) {
    context.value = value;
    vm.runInContext(body, context);
}
search('JA');
assert.equal(context.items.length, 1);
assert.equal(context.items[0].name, 'Jade');
assert.equal(context.selectedIndex, 0);
search('light');
assert.equal(context.items[0].name, 'Daylight');
search('missing');
assert.equal(context.items.length, 0);
search('');
assert.equal(context.items.length, 3);
assert.equal(context.allItems.length, 3);
assert.ok(source.includes('mode === "theme-dark" || mode === "theme-light"'));
assert.ok(source.includes('visible: picker.searchable && picker.searchText.length > 0'));
console.log('Theme carousel search checks passed');
