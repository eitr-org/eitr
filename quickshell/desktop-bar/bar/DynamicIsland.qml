import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: island
    required property var host
    required property var barHost
    required property real restingExtent
    required property real fullExtent
    property real contentExtent: extent
    property bool trailingAnchor: false
    property bool held: false
    property bool hoverExpanded: false
    readonly property bool expanded: hoverExpanded || held || host.barPointerHeld
    // An open panel owned by this island: the island itself grows into the panel's
    // size (along the bar and away from the edge) and the panel draws no surface.
    property var panel: null
    readonly property bool morphed: !!panel
    readonly property real thickness: barHost.normalThickness
    readonly property real targetExtent: morphed ? Math.max(restingExtent, host.verticalBar ? panel.height : panel.width)
        : expanded ? fullExtent : restingExtent
    readonly property real targetDepth: morphed ? Math.max(thickness, host.verticalBar ? panel.width : panel.height) : thickness
    property real extent: targetExtent
    property real depth: targetDepth
    Behavior on depth { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    // Bottom and right bars grow the card back toward the screen centre.
    readonly property bool farEdge: host.barEdge === "bottom" || host.barEdge === "right"
    readonly property real depthOffset: farEdge ? thickness - depth : 0
    readonly property alias content: contents
    property bool hovered: false
    width: host.verticalBar ? depth : extent
    height: host.verticalBar ? extent : depth
    // Islands are always full pills, whatever the corner preference; a card keeps 20 px corners.
    radius: Math.min(width, height, depth > thickness + 0.5 ? 40 : Infinity) / 2
    color: host.barBackground()
    Behavior on extent { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    onExpandedChanged: {
        if (expanded) return;
        viewport.cancelFlick();
        viewport.contentX = Qt.binding(function() {
            return !host.verticalBar && island.trailingAnchor ? viewport.contentWidth - viewport.width : 0;
        });
        viewport.contentY = Qt.binding(function() {
            return host.verticalBar && island.trailingAnchor ? viewport.contentHeight - viewport.height : 0;
        });
    }
    onHoveredChanged: {
        if (hovered) { collapse.stop(); hoverExpanded = true; }
        else collapse.restart();
    }
    Timer { id: collapse; interval: 350; onTriggered: island.hoverExpanded = false }
    BarGestureArea {
        anchors.fill: parent
        hostWindow: barHost
        edge: host.barEdge
        onCandidateChanged: host.dragCandidate = candidate
        onPointerHeld: function(held) { host.barPointerHeld = held }
        onDoubleTapped: function(button) { host.barDoubleClick(button) }
        onDropped: function(edge) { host.updateBarSetting("edge", edge) }
    }
    Flickable {
        id: viewport
        // The bar row keeps its place at the screen edge while the island grows into a card.
        width: host.verticalBar ? island.thickness : parent.width
        height: host.verticalBar ? parent.height : island.thickness
        x: host.verticalBar && island.farEdge ? parent.width - width : 0
        y: !host.verticalBar && island.farEdge ? parent.height - height : 0
        // Faded and disabled, not hidden: the island's panels follow its icons' visibility.
        opacity: island.morphed ? 0 : 1
        enabled: !island.morphed
        Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
        clip: true
        interactive: island.expanded && island.contentExtent > island.extent
        boundsBehavior: Flickable.StopAtBounds
        contentWidth: host.verticalBar ? width : Math.max(width, island.contentExtent)
        contentHeight: host.verticalBar ? Math.max(height, island.contentExtent) : height
        contentX: !host.verticalBar && island.trailingAnchor ? contentWidth - width : 0
        contentY: host.verticalBar && island.trailingAnchor ? contentHeight - height : 0
        Item { id: contents; width: viewport.contentWidth; height: viewport.contentHeight }
    }
}
