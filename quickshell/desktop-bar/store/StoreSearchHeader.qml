import ".."
import QtQuick
import QtQuick.Layouts
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

RowLayout {
    id: header
    required property var catalog
    property alias searchField: search
    spacing: 8
    height: PanelStyle.selectionRowHeight
    PanelTextField {
        id: search
        objectName: "catalog-search"
        Layout.fillWidth: true
        Layout.preferredWidth: 240
        Layout.minimumWidth: 100
        Layout.preferredHeight: header.height
        foreground: catalog.foreground; accent: catalog.gold
        placeholderText: Eitr.I18n.tr("Search Store")
        rightPadding: 8 + (clear.visible ? 28 : 0) + (toneFilter.visible ? 32 : 0)
        text: catalog.query
        onTextEdited: catalog.query = text
        onAccepted: { catalog.forceActiveFocus(); catalog.cursor = catalog.navigable.length ? 0 : -1; }
        Keys.onEscapePressed: event => { catalog.query = ""; event.accepted = true; }
        Keys.onDownPressed: { catalog.forceActiveFocus(); catalog.sidebarFocus = false; catalog.cursor = catalog.navigable.length ? 0 : -1; }
        PanelButton {
            id: clear
            objectName: "catalog-search-clear"
            anchors.right: toneFilter.visible ? toneFilter.left : parent.right; anchors.verticalCenter: parent.verticalCenter
            width: 28; height: 28; icon: true; text: "\uf00d"
            visible: catalog.query !== ""
            foreground: catalog.foreground; Accessible.name: Eitr.I18n.tr("Clear search")
            onClicked: { catalog.query = ""; search.forceActiveFocus(); }
        }
        StoreFilterMenu {
            id: toneFilter
            objectName: "catalog-tone-filter"
            catalog: header.catalog
            anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter
            width: 28; height: 28
        }
    }
    StoreActionButton {
        catalog: header.catalog
        objectName: "update-all"
        visible: catalog.tab === "updates" && catalog.updateItems.length > 0
        Layout.preferredWidth: 36; Layout.preferredHeight: header.height; icon: true; text: "\u{F06B0}"
        Accessible.name: Eitr.I18n.tr("Update all (%1)").arg(catalog.updateItems.length)
        available: !catalog.busy; onClicked: catalog.updateAll()
    }
    StoreActionButton {
        catalog: header.catalog
        visible: catalog.tab === "installed" && ["themes", "plugins"].includes(catalog.kind)
        Layout.preferredWidth: 80; Layout.preferredHeight: header.height; leadingIcon: "\uf067"; text: Eitr.I18n.tr("Add")
        Accessible.name: Eitr.I18n.tr("Add from a Git address")
        available: !catalog.busy
        onClicked: { catalog.addingAddress = true; catalog.error = ""; catalog.addressInput.forceActiveFocus(); }
    }
}
