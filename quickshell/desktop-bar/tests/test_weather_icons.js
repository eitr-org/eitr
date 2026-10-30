const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.join(__dirname, '..');
const icons = {};
vm.createContext(icons);
vm.runInContext(fs.readFileSync(path.join(root, 'WeatherIcons.js'), 'utf8').replace(/^\.pragma library\s*/, ''), icons);

// Forecast groups cover the same WMO codes as the shared collector.
const script = fs.readFileSync(path.join(root, 'scripts', 'weather-domain.py'), 'utf8');
const body = script.slice(script.indexOf('def icon('), script.indexOf('def number('));
const codes = [...body.matchAll(/code == (\d+)|code in \(([^)]+)\)/g)].flatMap(match =>
    match[1] ? [Number(match[1])] : match[2].split(',').map(Number));
const libraryCodes = icons.groups.flatMap(group => group.codes);
assert.deepEqual([...libraryCodes].sort((left, right) => left - right),
    [...codes, 3].sort((left, right) => left - right));

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
