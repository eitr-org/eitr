import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Item {
    required property var host
    required property var barHost

    id: islandSurfaces
    visible: !FocusMode.enabled
    anchors.fill: parent
    IslandSurface { first: host.verticalBar ? barHost.verticalControlCenterLogo : barHost.leftGroup.controlCenterLogo }
    IslandSurface { first: host.verticalBar ? barHost.verticalOverviewIcon : barHost.leftGroup.overviewIcon; last: host.verticalBar ? barHost.verticalWorkspaces : barHost.leftGroup.workspaces }
    IslandSurface { first: host.verticalBar ? barHost.verticalHardware : barHost.leftGroup.hardwareStatus }
    IslandSurface { first: host.verticalBar ? barHost.verticalCalendarIcon : barHost.centerInfo }
    IslandSurface { first: host.verticalBar ? barHost.verticalWeatherIcon : barHost.barWeather }
    IslandSurface { first: host.verticalBar ? barHost.verticalMedia : barHost.mediaStrip; shown: host.verticalBar ? barHost.verticalMedia.visible : barHost.mediaStrip.visible }
    IslandSurface { first: host.verticalBar ? barHost.verticalCapture : barHost.barCapture; shown: host.verticalBar ? barHost.verticalCapture.shown : barHost.barCapture.shown }
    IslandSurface { first: host.verticalBar ? barHost.verticalEnd : barHost.rightSide; last: host.verticalBar ? barHost.verticalEnd : barHost.notificationIcon }
    component IslandSurface: Rectangle {
        required property Item first
        property Item last: first
        property bool shown: true
        visible: barHost.islandsLayout && shown
        readonly property point leading: itemPosition(first)
        readonly property point trailing: itemPosition(last)
        function itemPosition(item) {
            var horizontal = 0;
            var vertical = 0;
            while (item && item !== barHost.stripItem) {
                horizontal += item.x;
                vertical += item.y;
                item = item.parent;
            }
            return Qt.point(horizontal, vertical);
        }
        x: host.verticalBar ? 0 : leading.x - 4
        y: host.verticalBar ? leading.y - 4 : 0
        width: host.verticalBar ? barHost.normalThickness : trailing.x + last.width - leading.x + 8
        height: host.verticalBar ? trailing.y + last.height - leading.y + 8 : barHost.normalThickness
        radius: DesktopStyle.radius(PanelStyle.cornerRadius)
        color: host.barBackground()
        BarGestureArea {
            anchors.fill: parent
            hostWindow: barHost
            edge: host.barEdge
            onCandidateChanged: host.dragCandidate = candidate
            onPointerHeld: function(held) { host.barPointerHeld = held }
            onDoubleTapped: function(button) { host.barDoubleClick(button) }
            onDropped: function(edge) { host.updateBarSetting("edge", edge) }
        }
    }
}
