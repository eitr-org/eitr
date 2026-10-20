const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const menu = fs.readFileSync(`${__dirname}/../WorkspaceStyleMenu.qml`, 'utf8');
const popup = fs.readFileSync(`${__dirname}/../ThemedPopup.qml`, 'utf8');
const width = menu.match(/implicitWidth: ([\s\S]*?)\n    implicitHeight:/)[1];
const inset = popup.match(/readonly property real horizontalContentInset: ([\s\S]*?)\n    property Item/)[1];
for (const vertical of [false, true]) {
    for (const detached of [false, true]) {
        for (const advanceWidth of [59, 84, 110]) {
            const panelSurface = {leftPadding: 24, rightPadding: 24, vertical,
                leadingBodyInset: 0, trailingBodyInset: detached ? 0 : 14};
            const horizontalContentInset = vm.runInNewContext(inset, {panelSurface});
            const actual = vm.runInNewContext(width, {horizontalContentInset,
                PanelStyle: {selectionTextInset: 36}, labelMetrics: {advanceWidth}});
            const contentWidth = actual - horizontalContentInset;
            const examplesLeft = contentWidth - 10 - (5 * 23 + 4 * 4);
            assert.ok(examplesLeft - (36 + advanceWidth) >= 12,
                'Workspace labels need a 12 px gap before examples in every layout');
        }
    }
}
console.log('Workspace style label spacing passed for attached and centered panels');
