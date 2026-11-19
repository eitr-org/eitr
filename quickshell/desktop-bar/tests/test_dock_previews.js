const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const context = {};
vm.createContext(context);
vm.runInContext(
    fs.readFileSync(`${__dirname}/../DockModel.js`, 'utf8').replace(/^\.pragma.*$/m, ''),
    context,
);

test('normalizeAddress normalizes hex addresses consistently', () => {
    assert.equal(context.normalizeAddress('0x1A2b3C'), '1a2b3c');
    assert.equal(context.normalizeAddress(' 1a2b3c '), '1a2b3c');
    assert.equal(context.normalizeAddress(''), '');
    assert.equal(context.normalizeAddress(null), '');
});

test('previewWindows pairs dock windows with live Hyprland toplevels', () => {
    const entry = {
        id: 'browser',
        windows: [
            {address: '0xAb12', class: 'Browser', title: 'Stale Title', workspace: {id: 2}, focusHistoryID: 0},
            {address: '0xCd34', class: 'Browser', title: 'Second Tab', workspace: {id: 1}, focusHistoryID: 3, size: [1200, 800]},
        ],
    };
    const waylandHandle = {appId: 'browser'};
    const toplevels = [
        {address: 'ab12', title: 'Live Title', wayland: waylandHandle, lastIpcObject: {address: '0xab12', size: [1920, 1080]}},
        null,
    ];
    const items = context.previewWindows(entry, toplevels);
    assert.equal(items.length, 2);
    assert.equal(items[0].address, '0xAb12');
    assert.equal(items[0].title, 'Live Title');
    assert.equal(items[0].active, true);
    assert.equal(items[0].workspaceId, 2);
    assert.deepEqual(Array.from(items[0].size), [1920, 1080]);
    assert.equal(items[0].wayland, waylandHandle);

    assert.equal(items[1].address, '0xCd34');
    assert.equal(items[1].title, 'Second Tab');
    assert.equal(items[1].active, false);
    assert.equal(items[1].workspaceId, 1);
    assert.deepEqual(Array.from(items[1].size), [1200, 800]);
    assert.equal(items[1].wayland, null);

    assert.deepEqual(Array.from(context.previewWindows(null, toplevels)), []);
    assert.deepEqual(Array.from(context.previewWindows({windows: []}, toplevels)), []);
});

test('previewGridLayout arranges previews, wraps within maxWidth, and scrolls when tall', () => {
    const single = context.previewGridLayout(1, true, 1200, 800, 196, 144, 36, 8, 12, 24);
    assert.equal(single.columns, 1);
    assert.equal(single.rows, 1);
    assert.equal(single.cardWidth, 220);
    assert.equal(single.cardHeight, 192);
    assert.equal(single.scrollable, false);

    const row = context.previewGridLayout(3, true, 1200, 800, 196, 144, 36, 8, 12, 24);
    assert.equal(row.columns, 3);
    assert.equal(row.rows, 1);
    assert.equal(row.cardWidth, 3 * 196 + 2 * 8 + 24);
    assert.equal(row.scrollable, false);

    const wrapped = context.previewGridLayout(5, true, 460, 260, 196, 144, 36, 8, 12, 24);
    assert.equal(wrapped.columns, 2);
    assert.equal(wrapped.rows, 3);
    assert.equal(wrapped.scrollable, true);
    assert.ok(wrapped.cardWidth <= 460);
    assert.ok(wrapped.cardHeight <= 260);

    const titlesOnly = context.previewGridLayout(3, false, 1200, 800, 196, 144, 36, 6, 12, 24);
    assert.equal(titlesOnly.columns, 1);
    assert.equal(titlesOnly.rows, 3);
    assert.equal(titlesOnly.rowWidth, 280);
    assert.equal(titlesOnly.cardWidth, 304);
    assert.equal(titlesOnly.cardHeight, 3 * 36 + 2 * 6 + 24 + 24);
    assert.equal(titlesOnly.scrollable, false);

    const empty = context.previewGridLayout(0, true, 1200, 800, 196, 144, 36, 8, 12, 24);
    assert.equal(empty.cardWidth, 0);
    assert.equal(empty.cardHeight, 0);
});

test('previewCardGeometry follows each dock edge and clamps inside the screen', () => {
    const bottom = context.previewCardGeometry('bottom', {x: 480, y: 948, width: 36, height: 52}, 1000, 1000, 300, 180, 8, 8);
    assert.equal(bottom.x, 348);
    assert.equal(bottom.y, 948 - 180 - 8);

    const top = context.previewCardGeometry('top', {x: 10, y: 0, width: 36, height: 52}, 1000, 1000, 300, 180, 8, 8);
    assert.equal(top.x, 8);
    assert.equal(top.y, 60);

    const left = context.previewCardGeometry('left', {x: 0, y: 950, width: 52, height: 36}, 1000, 1000, 300, 180, 8, 8);
    assert.equal(left.x, 60);
    assert.equal(left.y, 1000 - 180 - 8);

    const right = context.previewCardGeometry('right', {x: 948, y: 400, width: 52, height: 36}, 1000, 1000, 300, 180, 8, 8);
    assert.equal(right.x, 948 - 300 - 8);
    assert.equal(right.y, 400 + 18 - 90);
});
