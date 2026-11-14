import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

StoreState {
    id: catalog
    Keys.forwardTo: [keyboard]
    StoreKeyboard { id: keyboard; catalog: catalog }
    scroll: grid.scroll
    detailScroll: detailSheet.detailScroll
    videoPlayer: detailSheet.videoPlayer
    addressInput: review.addressInput
    removePackagesChoice: removeSheet.removePackagesChoice
    sidebar: navigationSidebar
    searchField: grid.searchField
    Rectangle { anchors.fill: parent; color: catalog.background; z: -1 }
    StoreSidebar { id: navigationSidebar; catalog: catalog }
    Rectangle { x: navigationSidebar.x + navigationSidebar.width + PanelStyle.padding; width: 1; height: parent.height; color: catalog.line }
    StoreGrid { id: grid; catalog: catalog; selectionHeight: selection.shown ? selection.height + 16 : 0 }
    StoreSelection { id: selection; catalog: catalog }
    StoreDetail { id: detailSheet; catalog: catalog }
CatalogPluginSheet {
        anchors.fill: parent
        plugin: catalog.kind === "plugins" ? catalog.managing : null
        foreground: catalog.foreground; background: catalog.background; accent: catalog.accent
        surface: catalog.surface; line: catalog.line
        updateAction: item => { catalog.managing = null; catalog.openDetail(item); catalog.prepareReview({id: item.id, updating: true}); }
        removeAction: item => { catalog.managing = null; catalog.removing = catalog.navigable.find(row => row.id === item.id) || item; catalog.forceActiveFocus(); }
        onClosed: { catalog.managing = null; catalog.forceActiveFocus(); }
    }
    StoreInstallReview { catalog: catalog }
    StoreRemove { id: removeSheet; catalog: catalog }
    StoreReview { id: review; catalog: catalog }
}
