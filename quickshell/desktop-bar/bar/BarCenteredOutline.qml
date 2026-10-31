import ".."
import QtQuick
import QtQuick.Shapes
import "../EdgeSlopes.js" as EdgeSlopes

Shape {
    required property var host
    required property var barHost
    readonly property alias centeredHoverItem: centeredHover
    id: centeredOutline
    visible: host.centeredLayout && !FocusMode.enabled
    readonly property real slope: barHost.normalThickness + host.tabBendRound
    x: barHost.stripItem.x - (host.verticalBar ? 0 : slope) + (host.verticalBar ? (host.barEdge === "left" ? -1 : 1) * barHost.normalThickness * (1 - barHost.autoHideRef.progress) : 0)
    y: barHost.stripItem.y - (host.verticalBar ? slope : 0) + (!host.verticalBar ? (host.barEdge === "top" ? -1 : 1) * barHost.normalThickness * (1 - barHost.autoHideRef.progress) : 0)
    width: barHost.stripItem.width + (host.verticalBar ? 0 : 2 * slope)
    height: barHost.stripItem.height + (host.verticalBar ? 2 * slope : 0)
    HoverHandler { id: centeredHover }
    BarGestureArea {
        anchors.fill: parent
        hostWindow: barHost
        edge: host.barEdge
        onCandidateChanged: host.dragCandidate = candidate
        onPointerHeld: function(held) { host.barPointerHeld = held }
        onDoubleTapped: function(button) { host.barDoubleClick(button) }
        onDropped: function(edge) { host.updateBarSetting("edge", edge) }
    }
    antialiasing: true
    ShapePath {
        strokeWidth: -1
        fillColor: host.barBackground()
        PathSvg { path: EdgeSlopes.outline(host.barEdge,
            host.verticalBar ? centeredOutline.height : centeredOutline.width,
            barHost.normalThickness, 0, host.tabBendRound,
            [[centeredOutline.slope, (host.verticalBar ? centeredOutline.height : centeredOutline.width) - centeredOutline.slope]]) }
    }
}
