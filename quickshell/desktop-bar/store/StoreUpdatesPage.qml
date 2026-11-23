import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

ColumnLayout {
    id: page
    required property var catalog
    property var excluded: ({})
    property var expanded: ({})
    property var changes: ({})
    property int previewGeneration: 0
    property bool previewPending: false
    property string returnKind: ""
    property real returnScroll: 0
    readonly property bool pageActive: catalog.tab === "updates"
    readonly property var items: catalog.updateItems
    readonly property var selected: items.filter(item => !excluded[key(item)])
    readonly property bool canUpdate: !catalog.busy && !catalog.updateCheck.pending && !catalog.nativeReviewing
    objectName: "store-updates-page"
    x: catalog.sidebarWidth; y: PanelStyle.padding
    width: catalog.width - x - PanelStyle.padding
    height: catalog.height - 2 * y
    spacing: 12
    visible: pageActive
    enabled: !catalog.nativeReviewing

    function key(item) { return item.storeKind + ":" + item.id; }
    function focusRow(index) {
        if (!pageActive || !catalog.opened || catalog.nativeReviewing) return;
        const row = rows.itemAt(Math.max(0, Math.min(index, rows.count - 1)));
        if (row) row.forceActiveFocus();
        else back.forceActiveFocus();
    }
    function resetPreviews() {
        previewGeneration++;
        previewPending = false;
        changes = ({});
        Qt.callLater(loadNext);
    }
    function loadNext() {
        if (!visible || !catalog.opened || catalog.updateCheck.pending || previewPending || !canUpdate) return;
        const item = items.find(entry => !changes[key(entry)]);
        if (!item) return;
        const generation = previewGeneration;
        previewPending = true;
        catalog.request("changes", {kind: item.storeKind, id: item.id}, function(failure, data) {
            if (generation !== previewGeneration) return;
            previewPending = false;
            changes = Object.assign({}, changes, {[key(item)]: failure ? {error: failure} : data});
            Qt.callLater(loadNext);
        });
    }
    onPageActiveChanged: {
        if (pageActive) {
            returnKind = catalog.kind;
            returnScroll = catalog.scroll ? catalog.scroll.contentY : 0;
            excluded = ({}); expanded = ({});
            resetPreviews();
            Qt.callLater(focusRow, 0);
        }
    }
    function startUpdates(items) {
        // A completed update can remove its focused row or disable the batch button.
        catalog.forceActiveFocus();
        catalog.updateSelected(items);
    }
    function leave() {
        if (catalog.busy) return;
        const tab = catalog.previousTab;
        const kind = returnKind || catalog.kind;
        const position = returnScroll;
        catalog.kind = kind;
        catalog.tab = tab;
        catalog.forceActiveFocus();
        Qt.callLater(function() {
            if (!catalog.opened || catalog.tab !== tab || catalog.kind !== kind) return;
            const grid = catalog.scroll;
            grid.contentY = Math.min(position, Math.max(0, grid.contentHeight - grid.height));
        });
    }
    onItemsChanged: Qt.callLater(loadNext)
    onCanUpdateChanged: if (canUpdate) {
        Qt.callLater(loadNext);
        if (pageActive && catalog.activeFocus) Qt.callLater(focusRow, 0);
    }
    Connections {
        target: page.catalog
        function onOpenedChanged() {
            page.excluded = ({}); page.expanded = ({});
            if (catalog.opened && page.pageActive) {
                page.returnKind = catalog.kind;
                page.returnScroll = 0;
            }
            page.resetPreviews();
        }
        function onUpdateCheckChanged() { if (!catalog.updateCheck.pending) page.resetPreviews(); }
    }

    FamilyPageHeader {
        Layout.fillWidth: true
        foreground: catalog.foreground
        rune: "ᛃ"
        group: "STORE"
        title: Eitr.I18n.tr("Updates")
    }
    Flow {
        Layout.fillWidth: true
        spacing: 8
        StoreActionButton {
            id: back
            catalog: page.catalog
            width: backLabel.advanceWidth + 24
            text: Eitr.I18n.tr("Back")
            available: !catalog.busy
            onClicked: page.leave()
            TextMetrics { id: backLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: back.text }
        }
        StoreActionButton {
            id: recheck
            catalog: page.catalog
            width: recheckLabel.advanceWidth + 24
            text: Eitr.I18n.tr("Check for updates")
            available: page.canUpdate && catalog.live
            onClicked: catalog.checkUpdates()
            TextMetrics { id: recheckLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: recheck.text }
        }
        StoreActionButton {
            id: select
            catalog: page.catalog
            width: selectLabel.advanceWidth + 24
            text: page.selected.length === page.items.length ? Eitr.I18n.tr("Select none") : Eitr.I18n.tr("Select all")
            available: page.canUpdate && page.items.length > 0
            onClicked: page.excluded = page.selected.length === page.items.length
                ? Object.fromEntries(page.items.map(item => [page.key(item), true])) : ({})
            TextMetrics { id: selectLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: select.text }
        }
        StoreActionButton {
            id: apply
            catalog: page.catalog
            objectName: "update-selected"
            width: applyLabel.advanceWidth + 24
            text: Eitr.I18n.tr("Update selected (%1)").arg(page.selected.length)
            primary: true
            available: page.canUpdate && page.selected.length > 0
            onClicked: page.startUpdates(page.selected)
            TextMetrics { id: applyLabel; font.family: DesktopFonts.family; font.pixelSize: PanelStyle.controlSize; text: apply.text }
        }
    }
    StoreLabel {
        catalog: page.catalog
        Layout.fillWidth: true
        visible: text !== ""
        text: catalog.error || catalog.progress || catalog.updateCheck.error
            || (catalog.updateCheck.pending ? Eitr.I18n.tr("Checking for updates…")
                : page.items.length === 0 ? Eitr.I18n.tr("Up to date") : "")
        Accessible.role: Accessible.AlertMessage
    }
    Flickable {
        id: scroll
        Layout.fillWidth: true; Layout.fillHeight: true
        clip: true
        contentHeight: list.height
        boundsBehavior: Flickable.StopAtBounds
        ScrollBar.vertical: ScrollBar {}
        Column {
            id: list
            width: scroll.width - 12
            spacing: PanelStyle.selectionRowGap
            Repeater {
                id: rows
                model: page.items.map(item => page.key(item))
                StoreUpdateRow {
                    required property string modelData
                    required property int index
                    catalog: page.catalog
                    width: list.width
                    item: page.items[index] || ({})
                    change: page.changes[modelData] || null
                    checked: !page.excluded[modelData]
                    expanded: !!page.expanded[modelData]
                    canUpdate: page.canUpdate
                    onToggleChecked: page.excluded = Object.assign({}, page.excluded, {[modelData]: checked})
                    onToggleExpanded: page.expanded = Object.assign({}, page.expanded, {[modelData]: !expanded})
                    onMoveFocus: delta => page.focusRow(index + delta)
                    onUpdateRequested: page.startUpdates([item])
                    onActiveFocusChanged: {
                        if (!activeFocus) return;
                        if (y < scroll.contentY) scroll.contentY = y;
                        else if (y + PanelStyle.selectionRowHeight > scroll.contentY + scroll.height)
                            scroll.contentY = y + PanelStyle.selectionRowHeight - scroll.height;
                    }
                }
            }
        }
    }
}
