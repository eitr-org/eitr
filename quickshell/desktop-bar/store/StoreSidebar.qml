import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

FamilySidebar {
    required property var catalog

    id: sidebar
    width: Math.min(260, catalog.width * 0.31)
    anchors.left: parent.left; anchors.top: parent.top; anchors.bottom: parent.bottom
    anchors.margins: PanelStyle.padding
    interactive: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
    foreground: catalog.foreground; background: catalog.background; accent: catalog.accent
    subtitle: "STORE"
    closeName: Eitr.I18n.tr("Close Store")
    placeholder: Eitr.I18n.tr("Search Store")
    query: catalog.query
    currentId: catalog.kind + "/" + catalog.tab
    entries: catalog.navigation
    onChosen: entry => { if (!catalog.busy) catalog.navigate(catalog.navigation.findIndex(row => row.id === entry.id)); }
    onCloseRequested: catalog.closeRequested()
    onSearchEdited: text => catalog.query = text
    onSearchAccepted: { catalog.forceActiveFocus(); if (catalog.navigable.length) catalog.cursor = 0; }
    onSearchKey: event => {
        if (event.key === Qt.Key_Escape) { if (catalog.query !== "") catalog.query = ""; else catalog.forceActiveFocus(); event.accepted = true; }
        else if (event.key === Qt.Key_Down) { catalog.forceActiveFocus(); if (catalog.navigable.length) catalog.cursor = 0; event.accepted = true; }
    }
    Component.onCompleted: searchField.objectName = "catalog-search"
}
