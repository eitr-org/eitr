import ".."
import QtQuick
import QtQuick.Shapes
import "../EdgeSlopes.js" as EdgeSlopes

Item {
    required property var host
    required property var barHost
    anchors.fill: parent
    readonly property alias tabStripItem: tabStrip
    readonly property alias leadingTabItem: leadingTab
    readonly property alias notchTabItem: notchTab
    readonly property alias trailingTabItem: trailingTab
    readonly property alias tabsOutlineItem: tabsOutline
    Item {
        id: tabStrip
        visible: host.notchLayout
        width: host.verticalBar ? host.tabStripThickness : parent.width
        height: host.verticalBar ? parent.height : host.tabStripThickness
        x: host.barEdge === "right" ? parent.width - width : 0
        y: host.barEdge === "bottom" ? parent.height - height : 0
    }
    TabSurface { id: leadingTab; start: 0; end: barHost.tabLeadingEnd }
    TabSurface { id: notchTab; start: barHost.tabCenterStart; end: barHost.tabCenterEnd }
    TabSurface { id: trailingTab; start: barHost.tabTrailingStart; end: host.verticalBar ? barHost.stripItem.height : barHost.stripItem.width }
    component TabSurface: Item {
        property real start
        property real end
        readonly property string barEdge: host.barEdge
        readonly property real revealProgress: 1
        readonly property bool detached: false
        visible: host.notchLayout
        width: host.verticalBar ? barHost.normalThickness - host.tabStripThickness : end - start
        height: host.verticalBar ? end - start : barHost.normalThickness - host.tabStripThickness
        x: host.verticalBar ? (host.barEdge === "right" ? 0 : host.tabStripThickness) : start
        y: host.verticalBar ? start : (host.barEdge === "bottom" ? 0 : host.tabStripThickness)

    }
    Shape {
        id: tabsOutline
        anchors.fill: parent
        visible: host.notchLayout
        antialiasing: true
        // One alpha silhouette also defines Hyprland's blur coverage.
        ShapePath {
            strokeWidth: -1
            fillColor: host.barBackground()
            PathSvg { path: {
                return EdgeSlopes.outline(host.barEdge,
                    host.verticalBar ? tabsOutline.height : tabsOutline.width,
                    barHost.normalThickness, host.tabStripThickness, host.tabBendRound,
                    [[0, barHost.tabLeadingEnd], [barHost.tabCenterStart, barHost.tabCenterEnd], [barHost.tabTrailingStart, host.verticalBar ? tabsOutline.height : tabsOutline.width]]);
            } }
        }
    }
}
