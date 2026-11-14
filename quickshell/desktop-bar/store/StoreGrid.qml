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
    ChoiceSegmented {
        visible: catalog.getMore
        width: Math.min(360, parent.width)
        foreground: catalog.foreground; background: catalog.background; gold: catalog.gold
        choices: [{id: "all", label: Eitr.I18n.tr("All")}, {id: "official", label: Eitr.I18n.tr("Official")}, {id: "community", label: Eitr.I18n.tr("Community")}]
        current: catalog.sourceFilter
        onChosen: value => { catalog.sourceFilter = value; catalog.cursor = -1; }
    }
    Item {
        width: parent.width
        height: visible ? PanelStyle.selectionRowHeight : 0
        visible: (catalog.kind === "themes" && !catalog.communityEmpty) || (catalog.tab === "installed" && ["themes", "plugins"].includes(catalog.kind))
        // All themes by default, or only the light or the dark ones.
        ChoiceSegmented {
            visible: catalog.kind === "themes" && !catalog.communityEmpty
            width: Math.min(300, parent.width - (addButton.visible ? addButton.width + 12 : 0) - (updateAllButton.visible ? updateAllButton.width + 12 : 0))
            foreground: catalog.foreground; background: catalog.background; gold: catalog.gold
            available: !catalog.busy
            choices: [{id: "all", label: Eitr.I18n.tr("All")}, {id: "light", label: Eitr.I18n.tr("Light")}, {id: "dark", label: Eitr.I18n.tr("Dark")}]
            current: catalog.tone
            onChosen: value => { catalog.tone = value; catalog.cursor = -1; catalog.forceActiveFocus(); }
        }
        // Narrow windows keep the filter readable and show Update all as its icon.
        StoreActionButton { catalog: contentLayout.catalog; id: updateAllButton; objectName: "update-all"; anchors.right: addButton.left; anchors.rightMargin: 12; height: PanelStyle.selectionRowHeight
            readonly property bool compact: parent.width < 300 + addButton.width + updateAllLabel.advanceWidth + 32 + 24
            width: compact ? height : Math.max(130, updateAllLabel.advanceWidth + 32); icon: compact; text: compact ? "\u{F06B0}" : updateAllLabel.text
            Accessible.name: updateAllLabel.text
            visible: catalog.tab === "installed" && catalog.pendingUpdates.length > 0; available: !catalog.busy; onClicked: catalog.updateAll()
            BarTooltip { target: updateAllButton; hovered: updateAllButton.compact && updateAllButton.hovered; text: updateAllLabel.text; foreground: catalog.foreground; background: catalog.raised } }
        TextMetrics { id: updateAllLabel; font.family: DesktopFonts.family; font.pixelSize: 13; text: Eitr.I18n.tr("Update all (%1)").arg(catalog.pendingUpdates.length) }
        StoreActionButton { catalog: contentLayout.catalog; id: addButton; anchors.right: parent.right; width: 110; height: PanelStyle.selectionRowHeight; visible: catalog.tab === "installed" && ["themes", "plugins"].includes(catalog.kind); available: !catalog.busy; leadingIcon: ""; text: Eitr.I18n.tr("Add"); Accessible.name: Eitr.I18n.tr("Add from a Git address"); onClicked: { catalog.addingAddress = true; catalog.error = ""; catalog.addressInput.forceActiveFocus(); } }
    }
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
