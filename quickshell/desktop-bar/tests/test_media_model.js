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
