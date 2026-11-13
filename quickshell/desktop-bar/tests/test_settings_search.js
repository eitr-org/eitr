const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const root = path.resolve(__dirname, '..');
const context = vm.createContext({});
const catalog = fs.readFileSync(path.join(root, 'settings/SettingsCatalog.js'), 'utf8').replace('.pragma library', '');
vm.runInContext(catalog, context);
context.Catalog = {settings: context.settings};
vm.runInContext(fs.readFileSync(path.join(root, 'settings/SettingsIndex.js'), 'utf8')
    .replace('.pragma library', '').replace('.import "SettingsCatalog.js" as Catalog', ''), context);
const translate = text => text;
assert.equal(context.filter('Cursor size', translate)[0].settingId, 'appearance-cursor-size');
assert.equal(context.filter('Cursor size', translate)[0].location, 'Appearance › Fonts & Cursor');
assert.equal(context.resolve('appearance/fonts#appearance-cursor-size').setting, 'appearance-cursor-size');
assert.equal(context.resolve('network/bluetooth').tab, 'bluetooth');
const cursorResults = context.filter('cursor', translate);
assert(cursorResults.some(result => result.settingId));
assert(cursorResults.some(result => !result.settingId && result.id === 'appearance'));
assert(cursorResults.every((result, index) => index === 0 || cursorResults[index - 1].score >= result.score));
assert.equal(context.filter(' ', translate).length, 21);
assert.equal(context.filter('unmatched words', translate).length, 0);
assert(context.score('Cursor size', '', 'cursor size') > context.score('Cursor size', '', 'cursor'));
assert(context.score('Cursor size', '', 'cursor') > context.score('Large cursor size', '', 'cursor'));
assert(context.score('Large cursor size', '', 'cursor') > context.score('Pointer', 'cursor', 'cursor'));
assert.equal(context.filter('Zeigergröße', text => text === 'Cursor size' ? 'Zeigergröße' : text)[0].settingId, 'appearance-cursor-size');
const ids = context.settings.map(setting => setting.id);
assert.equal(new Set(ids).size, ids.length);
function qmlFiles(directory) {
    return fs.readdirSync(directory, {withFileTypes: true}).flatMap(entry => entry.isDirectory()
        ? (entry.name === 'tests' ? [] : qmlFiles(path.join(directory, entry.name)))
        : entry.name.endsWith('.qml') ? [path.join(directory, entry.name)] : []);
}
const sources = qmlFiles(root).map(filename => fs.readFileSync(filename, 'utf8')).join('\n');
const literalIds = [...sources.matchAll(/objectName:\s*(?:[^\n?]+\?\s*)?"setting-([a-z0-9-]+)"/g)]
    .map(match => match[1]).filter(identifier => !identifier.endsWith('-'));
for (const identifier of literalIds) assert(ids.includes(identifier), `Missing catalog entry: ${identifier}`);
for (const setting of context.settings) {
    const literal = sources.includes('"setting-' + setting.id + '"');
    const defaultApp = setting.page === 'default-apps' && sources.includes('"setting-default-apps-" + appCard.modelData.kind');
    const eventSound = ['sound-notifications', 'sound-charger', 'notifications-notifications', 'notifications-charger'].includes(setting.id) && sources.includes('"setting-" + sounds.searchPage + "-" + modelData.setting');
    const helperCard = ['security', 'about', 'assistant'].includes(setting.page) && sources.includes('"setting-" + setting.id');
    const streaming = setting.page === "streaming" && sources.includes("content.settingTarget(modelData.source)");
    assert(literal || defaultApp || eventSound || helperCard || streaming, `Missing QML target: ${setting.id}`);
    assert(context.pages.some(page => page.id === setting.page));
    if (setting.tab) assert(context.tabs[setting.page].some(tab => tab.id === setting.tab));
}
console.log(`Settings search: ${ids.length} catalog targets and ranking passed`);
