import ".."
import QtQuick

// Clock content overlays never resize the clock button or its anchored neighbours.
Item {
    id: placement
    required property var host
    required property var barHost
    required property var owner
    readonly property var clock: owner.clock
    readonly property bool vertical: host.verticalBar
    // Islands keeps its slot like Full: its neighbouring pills are anchored to the clock and
    // would run into the left group if the clock pill grew.
    readonly property bool growing: barHost.dropLayout || (barHost.centeredLayout && !barHost.expanded)
    readonly property real length: vertical ? barHost.height : barHost.width
    readonly property real clockExtent: clock ? (vertical ? clock.height : clock.width) : 0
    readonly property var mediaTarget: vertical ? barHost.verticalMedia : barHost.mediaStrip
    // Pills can grow into free screen space. Full, Tabs and expanded Centered use
    // their existing slot and the padding before the nearest neighbouring item.
    readonly property real room: growing ? Math.max(clockExtent, Math.min(320, length - 32))
        : Math.max(0, Math.min(clockExtent + 8, length - 32))
    Binding { target: placement.clock; property: "moment"; value: owner.clockMoment; when: !barHost.dynamicLayout && !!placement.clock && placement.clock.moment !== undefined }
    Binding { target: placement.clock; property: "momentRoom"; value: placement.room; when: !barHost.dynamicLayout && !!placement.clock && placement.clock.moment !== undefined }
    Connections {
        target: placement.clock
        ignoreUnknownSignals: true
        function onMomentActivated(entry) {
            if (!entry) return;
            if (entry.kind === "notification") {
                if (barHost.dropLayout) barHost.panel("dashboard").show("notifications");
                else barHost.toggleKind("notifications");
            } else if (entry.kind === "song") {
                if (barHost.dropLayout) barHost.panel("dashboard").show("media");
                else barHost.toggleKind("media");
            } else if (entry.kind === "audio") {
                if (barHost.dropLayout) barHost.panel("dashboard").show("controls");
                else if (barHost.showKind) barHost.showKind("volume");
            } else placement.clock.clicked();
        }
    }
    readonly property var clockSurface: barHost.dropLayout && barHost.dropSurfaces ? barHost.dropSurfaces.pillSurface
        : barHost.islandsLayout && barHost.islandSurfaces ? barHost.islandSurfaces.clockSurface
        : barHost.centeredLayout && !barHost.expanded ? barHost.stripItem : clock
    Item {
        parent: placement.clockSurface || placement
        anchors.fill: parent
        HoverHandler { id: clockSurfaceHover; enabled: !barHost.dynamicLayout }
    }
    Binding { target: owner; property: "surfaceHovered"; value: clockSurfaceHover.hovered }
    Item {
        id: songSlot
        parent: placement.mediaTarget ? placement.mediaTarget.parent : placement
        x: placement.mediaTarget ? placement.mediaTarget.x : 0
        y: placement.mediaTarget ? placement.mediaTarget.y : 0
        width: placement.mediaTarget ? placement.mediaTarget.width : 0
        height: placement.mediaTarget ? placement.mediaTarget.height : 0
        visible: !!placement.mediaTarget && placement.mediaTarget.visible && !barHost.dynamicLayout
            && !barHost.dropLayout && barHost.expanded
        HoverHandler { id: mediaHover }
        BarMoment {
            host: placement.host
            payload: !barHost.dynamicLayout ? owner.songMoment : null
            anchors.fill: parent
            onActivated: barHost.toggleKind("media")
        }
    }
    Binding { target: owner; property: "mediaHovered"; value: mediaHover.hovered }
    // MediaStrip owns its content fade; its footprint stays exactly the same.
    Binding { target: barHost.mediaStrip; property: "momentActive"; value: !!owner.songMoment && !barHost.dynamicLayout }
    Binding { target: barHost.verticalMedia; property: "opacity"; value: 0; when: vertical && !!owner.songMoment && !barHost.dynamicLayout }
}
