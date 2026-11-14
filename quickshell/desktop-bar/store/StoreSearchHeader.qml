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
    ChoiceSegmented {
        visible: catalog.getMore
        Layout.preferredWidth: Math.min(300, header.width * 0.46)
        foreground: catalog.foreground; background: catalog.background; gold: catalog.gold
        choices: [{id: "all", label: Eitr.I18n.tr("All")}, {id: "official", label: Eitr.I18n.tr("Official")}, {id: "community", label: Eitr.I18n.tr("Community")}]
        current: catalog.sourceFilter
        onChosen: value => { catalog.sourceFilter = value; catalog.cursor = -1; }
    }
    Item { Layout.fillWidth: true }
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
        ChoiceDropdown {
            id: toneFilter
            objectName: "catalog-tone-filter"
            visible: catalog.kind === "themes"
            anchors.right: parent.right; anchors.rightMargin: 4; anchors.verticalCenter: parent.verticalCenter
            width: 28; height: 28
            foreground: catalog.foreground; background: catalog.background; gold: catalog.gold
            accessibleName: Eitr.I18n.tr("Appearance")
            label: "\uf0b0"
            current: catalog.tone
            choices: [{id: "all", label: Eitr.I18n.tr("All")}, {id: "light", label: Eitr.I18n.tr("Light")}, {id: "dark", label: Eitr.I18n.tr("Dark")}]
            popupWidth: 160
            iconOnly: true
            onChosen: value => { catalog.tone = value; catalog.cursor = -1; }
            Rectangle { anchors.right: parent.right; anchors.top: parent.top; width: 6; height: 6; radius: 3; color: catalog.gold; visible: catalog.tone !== "all" }
        }
    }
    StoreActionButton {
        catalog: header.catalog
        objectName: "update-all"
        visible: catalog.tab === "installed" && catalog.pendingUpdates.length > 0
        Layout.preferredWidth: 36; Layout.preferredHeight: header.height; icon: true; text: "\u{F06B0}"
        Accessible.name: Eitr.I18n.tr("Update all (%1)").arg(catalog.pendingUpdates.length)
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
