const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const source = fs.readFileSync(path.join(__dirname, '../panels/AppearancePicker.qml'), 'utf8');
const modelSource = fs.readFileSync(path.join(__dirname, '../settings/SettingsAppearanceModel.qml'), 'utf8');
const body = modelSource.split('function search(value) {')[1].split('\n    }')[0];
const context = {
    allItems: [{name: 'Asgard'}, {name: 'Afterglow'}, {name: 'Eitr Light'}],
    selectedIndex: 2,
};
vm.createContext(context);
function search(value) {
    context.value = value;
    vm.runInContext(body, context);
}
search('AS');
assert.equal(context.items.length, 1);
assert.equal(context.items[0].name, 'Asgard');
assert.equal(context.selectedIndex, 0);
search('light');
assert.equal(context.items[0].name, 'Eitr Light');
search('missing');
assert.equal(context.items.length, 0);
search('');
assert.equal(context.items.length, 3);
assert.equal(context.allItems.length, 3);
assert.ok(modelSource.includes('readonly property bool themeMode: mode.startsWith("theme")'));
assert.ok(modelSource.includes('readonly property bool searchable: themeMode || mode === "wallpaper"'));
// Wallpapers match by name or by the theme they come from.
context.allItems = [{name: 'Ember Vigil', theme: 'Afterglow'}, {name: 'Frost Queen', theme: 'Niflheim'}];
search('niflheim');
assert.deepEqual(context.items.map(item => item.name), ['Frost Queen']);
assert.ok(source.includes('visible: picker.searchable && picker.searchText.length > 0'));
console.log('Theme carousel search checks passed');
