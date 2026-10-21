const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const model = {};
vm.createContext(model);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'MediaModel.js'), 'utf8').replace(/^\.pragma library\s*/, ''), model);

const music = {identity: 'Chromium', dbusName: 'org.mpris.MediaPlayer2.chromium', trackTitle: 'Song', isPlaying: true};
assert(model.eligible(music));
assert(model.eligible({...music, isPlaying: false}));
assert(!model.eligible({...music, dbusName: 'org.mpris.MediaPlayer2.playerctld'}));
assert(!model.eligible({...music, trackTitle: '', isPlaying: false}));
for (const identity of ['Zoom', 'Microsoft Teams', 'Webex', 'Google Meet']) {
    assert(!model.eligible({...music, identity}), identity);
}
for (const url of ['https://meet.google.com/abc-defg-hij', 'https://company.zoom.us/j/123', 'https://teams.microsoft.com/meeting', 'https://meet.jit.si/call']) {
    assert(!model.eligible({...music, metadata: {'xesam:url': url}}), url);
}
assert(model.eligible({...music, metadata: {'xesam:url': 'https://www.youtube.com/watch?v=test'}}));
assert(model.eligible({...music, metadata: {'xesam:url': 'https://meet.google.com.example.org/song'}}));
console.log('Media eligibility and meeting exclusion checks passed');

const audio = {};
vm.createContext(audio);
vm.runInContext(fs.readFileSync(path.join(__dirname, '..', 'AudioLevels.js'), 'utf8').replace(/^\.pragma library\s*/, ''), audio);
assert.deepEqual(Array.from(audio.parseFrame('0;25;50;100;')), [0, .25, .5, 1]);
assert.deepEqual(Array.from(audio.parseFrame('0;25;50;101\r')), [0, .25, .5, 1]);
for (const line of ['', '1;2;3', '1;2;3;4;5', 'NaN;2;3;4', '-1;2;3;4', ';2;3;4']) {
    assert.equal(audio.parseFrame(line), null);
}
assert.equal(audio.height(0), 3);
assert.equal(audio.height(1), 14);
assert.equal(audio.height(2), 14);
