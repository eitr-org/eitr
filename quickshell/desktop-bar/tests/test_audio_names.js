const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const names = {};
vm.createContext(names);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'AudioNames.js'), 'utf8').replace(/^\.pragma library\s*/, ''), names);

const cases = [
    ['GA104 High Definition Audio Controller Digital Stereo (HDMI) [34GL750]', '34GL750', '34GL750'],
    ['G522 LIGHTSPEED - Wireless Mode Analog Stereo', 'G522 LIGHTSPEED - Wireless Mode', 'G522 LIGHTSPEED - Wireless Mode'],
    ['G522 LIGHTSPEED - Wireless Mode Mono', '', 'G522 LIGHTSPEED - Wireless Mode'],
    ['Built-in Audio Digital Stereo (IEC958)', 'ALCS1200A Digital', 'Built-in Audio (Optical)'],
    ['Built-in Audio Analog Stereo', 'ALCS1200A Analog', 'Built-in Audio'],
    ['Built-in Audio Analog Surround 5.1', '', 'Built-in Audio'],
    ['Navi 21 HDMI/DP Audio Digital Stereo (HDMI 2)', '', 'Navi 21 HDMI/DP Audio (HDMI)'],
    ['Example Speakers', '', 'Example Speakers'],
    ['', 'Nick only', 'Nick only'],
];
for (const [description, nick, expected] of cases) {
    assert.equal(names.friendlyName(description, nick), expected, description);
}
assert.equal(names.friendlyName('', ''), '');

assert.equal(names.glyph({'device.bus': 'bluetooth'}, 'Earbuds', false), '\u{F02CB}');
assert.equal(names.glyph({'device.form-factor': 'headset'}, 'Headset', true), '\u{F02CB}');
assert.equal(names.glyph({'device.form-factor': 'webcam'}, 'Camera Mono', true), '\u{F0567}');
assert.equal(names.glyph({}, 'Controller Digital Stereo (HDMI) [Monitor]', false), '\u{F0379}');
assert.equal(names.glyph({}, 'Built-in Audio Digital Stereo (IEC958)', false), '\u{F0A17}');
assert.equal(names.glyph({}, 'Built-in Audio Analog Stereo', false), '\u{F04C3}');
assert.equal(names.glyph(null, 'Built-in Audio Analog Stereo', true), '\u{F036C}');
console.log('Audio device naming checks passed');
