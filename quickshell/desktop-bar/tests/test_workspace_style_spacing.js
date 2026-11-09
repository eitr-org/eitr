const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const menu = fs.readFileSync(`${__dirname}/../panels/WorkspaceStyleMenu.qml`, 'utf8');
const popup = fs.readFileSync(`${__dirname}/../components/ThemedPopup.qml`, 'utf8');
const row = menu.match(/readonly property real rowWidth: (.*)\n/)[1];
const width = menu.match(/implicitWidth: ([\s\S]*?)\n    implicitHeight:/)[1];
const inset = popup.match(/readonly property real horizontalContentInset: ([\s\S]*?)\n    property Item/)[1];
assert.match(menu, /showLabels: false/, 'The popup shows the examples without their names');
for (const vertical of [false, true]) {
    for (const detached of [false, true]) {
        const panelSurface = {leftPadding: 24, rightPadding: 24, vertical,
            leadingBodyInset: 0, trailingBodyInset: detached ? 0 : 14};
        const horizontalContentInset = vm.runInNewContext(inset, {panelSurface, verticalAttachment: vertical, navigationBand: 0});
        const rowWidth = vm.runInNewContext(row, {workspaceNumbers: [1, 2, 3, 4, 5]});
        const contentWidth = vm.runInNewContext(width, {horizontalContentInset, rowWidth}) - horizontalContentInset;
        // Two cards per row (8 px apart); each card's picture keeps 16 px of padding.
        const card = Math.floor((contentWidth - 8) / 2);
        const marker = Math.min(23, (card - 32) / 5);
        assert.ok(marker >= 20, `Five workspace markers fit each card in every layout (marker ${marker} px)`);
    }
}
console.log('Workspace style cards fit five markers in attached and centered panels');
