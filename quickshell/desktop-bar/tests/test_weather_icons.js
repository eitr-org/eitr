const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const icons = {};
vm.createContext(icons);
vm.runInContext(fs.readFileSync(path.join(root, 'WeatherIcons.js'), 'utf8').replace(/^\.pragma library\s*/, ''), icons);

// Every WMO group in weather-status.sh's weather_icon() maps to one forecast glyph.
const script = fs.readFileSync(path.join(root, 'scripts', 'weather-status.sh'), 'utf8');
const body = script.slice(script.indexOf('weather_icon() {'), script.indexOf('condition_text() {'));
const scriptGroups = [...body.matchAll(/^\s*([0-9|]+)\)/gm)].map(match => match[1].split('|').map(Number));
assert(scriptGroups.length >= 8, 'weather_icon groups not found');
const libraryGroups = JSON.parse(JSON.stringify(icons.groups.map(group => group.codes)));
assert.deepEqual(libraryGroups, scriptGroups);

const seen = new Set();
for (const group of icons.groups) {
    assert(!seen.has(group.icon), 'each WMO group has a distinct glyph');
    seen.add(group.icon);
    for (const code of group.codes) {
        assert.equal(icons.forecastIcon(String(code)), group.icon, `code ${code}`);
        assert.equal(icons.forecastIcon(code), group.icon, `numeric code ${code}`);
    }
}

assert.equal(icons.forecastIcon('0'), '\u{F0599}', 'clear sky uses the sunny glyph');
assert.equal(icons.forecastIcon('95'), '\u{F067E}', 'thunderstorm uses the lightning glyph');
// Former wttr.in codes and junk fall back instead of matching a WMO group.
for (const code of ['113', '116', '', 'abc', undefined, null, '2.5']) {
    assert.equal(icons.forecastIcon(code), icons.fallbackIcon, String(code));
}
console.log('Weather forecast icon mapping checks passed');
