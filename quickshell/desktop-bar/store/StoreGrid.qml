import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Column {
    required property var catalog
    property alias scroll: scroll
    property alias searchField: searchHeader.searchField
    property real selectionHeight: 0

    id: contentLayout
    enabled: !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail
    x: catalog.sidebarWidth; y: PanelStyle.padding
    width: catalog.width - x - PanelStyle.padding; spacing: 14
    FamilyPageHeader {
        foreground: catalog.foreground
        rune: catalog.currentPage.groupRune
        group: catalog.currentPage.group
        title: catalog.currentPage.title
        description: catalog.currentPage.description
    }
    StoreSearchHeader { id: searchHeader; width: parent.width; catalog: contentLayout.catalog }
    StoreLabel { catalog: contentLayout.catalog; width: parent.width; visible: text !== ""; text: (!catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing ? catalog.error || catalog.progress : "") || (catalog.loading ? Eitr.I18n.tr("Loading…") : ""); Accessible.role: Accessible.AlertMessage }
    Flickable {
        id: scroll
        objectName: "catalog-scroll"
        width: parent.width; height: Math.max(1, catalog.height - contentLayout.y - y - PanelStyle.padding - selectionHeight)
        contentWidth: width; contentHeight: sections.height; clip: true; boundsBehavior: Flickable.StopAtBounds
        function more() { if (contentY + height > contentHeight - 600 && catalog.shown < catalog.navigable.length) catalog.shown += catalog.pageSize; }
        onContentYChanged: more()
        onContentHeightChanged: Qt.callLater(more)
        onHeightChanged: Qt.callLater(more)
        ScrollBar.vertical: ScrollBar {}
        Column {
            id: sections; width: catalog.scroll.width - 12; spacing: 14
            Repeater {
                model: [{local: !catalog.getMore}]
                Column {
                    id: section
                    required property var modelData
                    readonly property string pageError: modelData.local ? catalog.installedError : catalog.getMore && catalog.discoveries.length ? "" : catalog.repositoryError
                    readonly property var items: pageError ? [] : catalog.navigable
                    width: sections.width; spacing: 12
                    GridLayout {
                        columns: catalog.columns; columnSpacing: 14; rowSpacing: 14
                        Repeater { model: section.items.slice(0, catalog.shown)
                            StoreCatalogCard { catalog: contentLayout.catalog; required property var modelData; item: modelData; local: catalog.isInstalled(modelData); Layout.preferredWidth: (section.width - 14 * (catalog.columns - 1)) / catalog.columns; Layout.fillHeight: true }
                        }
                    }
                    CatalogEmptyState { catalogContext: catalog; sectionContext: section; viewportHeight: catalog.scroll.height }
                }
            }
        }
    }
}
// Chosen themes float in a pop-up below the cards (which end above it) until reviewed or cleared.
