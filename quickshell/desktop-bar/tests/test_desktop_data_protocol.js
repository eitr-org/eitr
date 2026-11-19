const assert = require('assert');
const { createClient } = require('../DesktopDataProtocol.js');
const frames = [];
const client = createClient(frame => frames.push(frame), () => {});
client.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'first'}));
const token = client.observe('account.picture', 'sheet');
client.receive(JSON.stringify({v: 1, op: 'state', epoch: 'first', topic: 'account.picture', seq: 1, status: 'ready', data: {path: null, initial: 'A', name: 'Astrid'}, ageMs: 0}));
assert.strictEqual(client.states['account.picture'].data.path, null);
let error = '';
client.accountAction('save', {source: '/mock/image.png'}, 'sheet', message => { error = message; });
client.died();
assert.strictEqual(error, 'outcome-unknown');
const actions = frames.filter(frame => frame.op === 'action').length;
client.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'second'}));
assert.strictEqual(frames.filter(frame => frame.op === 'action').length, actions);
client.release(token);
assert.strictEqual(client.count('account.picture'), 0);
console.log('account actions never replay');

// Every query DesktopData.qml forwards must exist on the client it forwards to.
const forwarded = require('fs').readFileSync(require('path').join(__dirname, '../services/DesktopData.qml'), 'utf8')
    .match(/client\.(query\w+|accountAction|cancelQuery)\(/g).map(call => call.slice(7, -1));
for (const name of forwarded) assert.strictEqual(typeof client[name], 'function', `client.${name} is not exported`);
console.log('every forwarded query is exported');

// A reply on every query topic reaches its callback (window and speed were dropped once).
for (const [name, args] of [['queryWindow', ['info', {}]], ['querySpeed', ['disk', {}]], ['queryAudio', ['ports', {}]]]) {
    let replied = null;
    const replyClient = createClient(() => {}, () => {});
    replyClient.receive(JSON.stringify({v: 1, op: 'hello', epoch: 'reply'}));
    const id = replyClient[name](...args, 'owner', (error, data) => { replied = data; });
    replyClient.receive(JSON.stringify({v: 1, op: 'reply', epoch: 'reply', topic: id.split('-')[0], id: id, error: '', data: {ok: true}}));
    assert.deepStrictEqual(replied, {ok: true}, `${name} reply was dropped`);
}
console.log('every query topic receives its reply');
