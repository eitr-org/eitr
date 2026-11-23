import ".."
import QtQuick

// The picker moves its one content loader into the selected bar's card.
Item {
    id: card
    required property var barHost
    required property var picker
    readonly property bool requested: picker.opened && picker.docked && picker.targetScreen === barHost.screen
    readonly property var island: barHost.dropSurfaces ? barHost.dropSurfaces.pillSurface : null
    readonly property bool opened: requested && !!island && barHost.autoHideRef.progress >= 1
        && !barHost.dockPanels.some(panel => panel.visible) && !barHost.overviewOpen
    // DynamicIsland eases into this size. There is no panel reveal animation to follow.
    readonly property real revealProgress: 0
    readonly property real availableWidth: barHost.width - barHost.edgeGap * 2
    width: Math.max(0, Math.min(640, availableWidth))
    height: Math.max(0, Math.min(260, barHost.height - barHost.edgeGap * 2))
    readonly property alias content: body
    // The card sits on the bar's surface whatever creates it, at its own size.
    parent: barHost.contentItem
    anchors.centerIn: parent
    // The card dimensions are also the morph target, independent of the animated island.
    anchors.horizontalCenterOffset: island ? islandOrigin.x + (island.width - parent.width) / 2 : 0
    anchors.verticalCenterOffset: island ? islandOrigin.y + (island.height - parent.height) / 2 : 0
    readonly property point islandOrigin: {
        if (!island) return Qt.point(0, 0);
        const geometry = island.x + island.y + barHost.stripItem.x + barHost.stripItem.y;
        return island.mapToItem(parent, 0, 0);
    }
    z: 20
    visible: requested
    function attach() {
        if (requested) {
            barHost.closePanels();
            picker.dockedContent = body;
        } else detach();
    }
    function detach() {
        if (picker && picker.dockedContent === body) picker.dockedContent = null;
    }
    onRequestedChanged: attach()
    Component.onCompleted: attach()
    Component.onDestruction: detach()

    MouseArea {
        parent: card.parent
        anchors.fill: parent
        visible: card.requested
        z: card.z - 1
        onClicked: picker.opened = false
        onWheel: event => picker.navigate(event.angleDelta.y > 0 ? -1 : 1)
    }
    Item {
        anchors.centerIn: parent
        width: card.island ? Math.min(card.width, card.island.width) : 0
        height: card.island ? Math.min(card.height, card.island.height) : 0
        clip: true
        Item {
            id: body
            width: card.width
            height: card.height
            anchors.centerIn: parent
            opacity: card.opened && card.island
                ? Math.max(0, Math.min(1, (Math.min(parent.width / width, parent.height / height) - 0.9) / 0.1)) : 0
            // Keep the content focusable during the morph, including Escape.
            MouseArea {
                anchors.fill: parent
                enabled: body.opacity > 0
                onWheel: event => picker.navigate(event.angleDelta.y > 0 ? -1 : 1)
            }
        }
    }
}
