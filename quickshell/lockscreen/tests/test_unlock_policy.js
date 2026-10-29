const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const policy = {};
vm.createContext(policy);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'UnlockPolicy.js'), 'utf8').replace(/^\.pragma library\s*/, ''), policy);
for (let bits = 0; bits < 64; bits++) {
    const [authenticated, locked, secure, reduced, snapshotReady, expired] = Array.from({length: 6}, (unusedValue, index) => Boolean(bits & (1 << index)));
    const expected = authenticated && !locked && !secure && !reduced && snapshotReady && !expired;
    assert.equal(policy.eligible(authenticated, locked, secure, reduced, snapshotReady, expired), expected);
}
console.log('All 64 authentication, lock, snapshot, accessibility and deadline combinations passed.');

const palette = {};
vm.createContext(palette);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'themes/eitr/Spectrum.js'), 'utf8').replace(/^\.pragma library\s*/, ''), palette);
for (const [light, filename] of [[false, 'global.css'], [true, 'appearance.css']]) {
    const css = fs.readFileSync(path.join(__dirname, '../../../website/src/styles', filename), 'utf8');
    const stops = css.match(/--bifrost-spectrum:linear-gradient\(([^)]+)\)/)[1].match(/#[a-f0-9]{6}/g);
    assert.deepEqual(Array.from(palette.colors(light)), stops);
}
console.log('Dark and light spectra match the website exactly.');
