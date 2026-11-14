import ".."
import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Effects
import QtQuick.Layouts
import QtMultimedia
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

Rectangle {
    required property var catalog

    id: tile
    objectName: "card-" + (item.id || "")
    required property var item
    required property bool local
    readonly property string itemKind: item.storeKind || catalog.kind
    readonly property var capabilities: (catalog.kinds.find(entry => entry.id === itemKind) || catalog.definition).capabilities
    readonly property int updateCount: (catalog.updateCache[itemKind] || catalog.updates)[item.id] || 0
    readonly property bool picked: catalog.getMore && !local && catalog.selected.includes(item.id)
    readonly property bool focused: catalog.cursor >= 0 && !!catalog.navigable[catalog.cursor] && catalog.navigable[catalog.cursor].id === item.id && (catalog.navigable[catalog.cursor].storeKind || catalog.kind) === itemKind
    readonly property bool actionable: catalog.getMore || !(local && item.current)
    readonly property real viewportY: parent.parent.y + parent.y + y - catalog.scroll.contentY
    readonly property bool inViewport: viewportY + height > 0 && viewportY < catalog.scroll.height
    implicitHeight: details.y + details.height + 12
    radius: DesktopStyle.radius(10)
    color: catalog.surface
    border.width: 1
    border.color: picked || focused || item.current ? catalog.accent : tile.actionable && cardMouse.containsMouse ? catalog.gold : catalog.line
    RectangularShadow {
        anchors.fill: parent; z: -1
        // The current theme keeps the selected border and glow.
        visible: tile.picked || tile.focused || !!tile.item.current
        radius: tile.radius; blur: 18; spread: 2; color: catalog.glow
    }
    onFocusedChanged: {
        if (!focused) return;
        const top = mapToItem(catalog.scroll, 0, 0).y;
        if (top < 0) catalog.scroll.contentY = Math.max(0, catalog.scroll.contentY + top);
        else if (top + height > catalog.scroll.height) catalog.scroll.contentY = Math.min(catalog.scroll.contentHeight - catalog.scroll.height, catalog.scroll.contentY + top + height - catalog.scroll.height);
    }
    onInViewportChanged: if (inViewport && !local) catalog.preview(item)
    Component.onCompleted: if (inViewport && !local) catalog.preview(item)
    StorePreview { catalog: tile.catalog; id: art; x: 2; y: 2; width: parent.width - 4; height: width * 9 / 16; source: catalog.imageFor(tile.item); plugin: tile.itemKind === "plugins"; iconOnly: plugin && !tile.item.preview && !(tile.item.previewUrl && !tile.item.icon) }
    Column {
        id: details
        z: 1
        x: 12; y: art.y + art.height + 10; width: parent.width - 24; spacing: 5
        StoreLabel { catalog: tile.catalog; width: parent.width; text: tile.item.name || ""; font.family: SiteStyle.carved; font.weight: Font.Medium; font.letterSpacing: 0.7; maximumLineCount: 1; elide: Text.ElideRight }
        StoreLabel { catalog: tile.catalog; width: parent.width; text: tile.item.description || (tile.itemKind === "themes" ? Eitr.I18n.tr("Desktop theme") : ""); font.pixelSize: 13; color: catalog.muted; maximumLineCount: 1; elide: Text.ElideRight }
        Row { spacing: 4; visible: tile.itemKind === "themes"
            Repeater {
                model: tile.itemKind === "themes" && tile.item.palette ? ["background", "foreground", "accent", "color1", "color2", "color3", "color4", "color5", "color6"] : []
                Rectangle { required property string modelData; width: 14; height: 14; radius: 7; color: tile.item.palette[modelData]; border.width: 1; border.color: catalog.lineStrong }
            }
        }
        Flow { width: parent.width; spacing: 6
            StorePill { catalog: tile.catalog; text: catalog.badge(tile.item) }
            StorePill { catalog: tile.catalog; visible: tile.itemKind === "lockscreens" && !!tile.item.current; text: Eitr.I18n.tr("Current"); current: true }
            StorePill { catalog: tile.catalog; visible: tile.itemKind === "plugins" && tile.item.builtin === true; text: Eitr.I18n.tr("Official") }
            StorePill { catalog: tile.catalog; visible: tile.local && catalog.getMore; text: Eitr.I18n.tr("Installed") }
            StorePill { catalog: tile.catalog; visible: tile.itemKind === "plugins" && tile.item.enabled === false; text: Eitr.I18n.tr("Disabled") }
        }
        Item {
            width: parent.width
            height: 32
            visible: catalog.getMore && !tile.local || tile.updateCount > 0
            StoreActionButton { catalog: tile.catalog;
                objectName: "install-" + tile.item.id
                anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
                width: 110; visible: catalog.getMore && !tile.local
                text: tile.picked ? "\uF00C " + Eitr.I18n.tr("Selected") : Eitr.I18n.tr("Install")
                selected: tile.picked; available: !catalog.busy
                onClicked: { if (tile.item.storeKind) catalog.kind = tile.item.storeKind; if (tile.capabilities.needsAdministrator) catalog.act("install", {ids: [tile.item.id]}); else if (!tile.capabilities.useOnClick) { catalog.openDetail(tile.item); catalog.reviewDetail(); } else catalog.toggle(tile.item); catalog.cursor = catalog.navigable.findIndex(item => item.id === tile.item.id); catalog.sidebarFocus = false; catalog.forceActiveFocus(); }
            }
            StorePill { catalog: tile.catalog;
                anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
                visible: tile.updateCount > 0; text: Eitr.I18n.tr("Update"); current: true
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: { if (tile.capabilities.useOnClick) catalog.act("update", {id: tile.item.id}); else { catalog.openDetail(tile.item); catalog.prepareReview({id: tile.item.id, updating: true}); } } }
            }
        }
    }
    MouseArea { id: cardMouse; anchors.fill: parent; hoverEnabled: true; enabled: tile.actionable && !catalog.busy && !catalog.nativeReviewing && !catalog.addingAddress && !catalog.reviewing && !catalog.removing && !catalog.detail && !catalog.managing
        cursorShape: Qt.PointingHandCursor
        onClicked: { catalog.cursor = catalog.navigable.findIndex(theme => theme.id === tile.item.id); catalog.activate(tile.item, tile.local); }
    }
    Rectangle {
        visible: tile.picked; x: 10; y: 10; width: 30; height: 30; radius: 15; color: catalog.accent
        StoreLabel { catalog: tile.catalog; anchors.centerIn: parent; text: "\uF00C"; color: PanelStyle.readableInk(catalog.accent, catalog.foreground, catalog.background); font.pixelSize: 18 }
    }
    StoreActionButton { catalog: tile.catalog;
        id: removeButton
        objectName: "remove-" + tile.item.id
        anchors.right: parent.right; anchors.top: parent.top; anchors.margins: 8
        width: 28; height: 28; icon: true; text: "󰆴"; foreground: catalog.foreground
        color: catalog.background
        visible: catalog.tab === "installed" && tile.local && (tile.capabilities.remove && (tile.item.removable === undefined || tile.item.removable === true)) && !tile.item.current && (tile.item.kind !== "builtin" || tile.item.removable === true) && tile.item.kind !== "own"
        Accessible.name: Eitr.I18n.tr("Remove %1").arg(tile.item.name || "")
        onClicked: { if (tile.item.storeKind) catalog.kind = tile.item.storeKind; catalog.removing = tile.item; catalog.forceActiveFocus(); }
        BarTooltip { target: removeButton; hovered: removeButton.hovered; text: Eitr.I18n.tr("Delete"); foreground: catalog.foreground; background: catalog.raised }
    }

}
