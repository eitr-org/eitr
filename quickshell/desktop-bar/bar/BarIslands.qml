import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Item {
    required property var host
    required property var barHost

    id: islandSurfaces
    visible: !FocusMode.enabled
    anchors.fill: parent
    // grow: where a pill's card extends, toward the free space ("start", "end" or "center").
    IslandSurface { id: logoPill; first: host.verticalBar ? barHost.verticalControlCenterLogo : barHost.leftGroup.controlCenterLogo }
    IslandSurface { id: workspacesPill; first: host.verticalBar ? barHost.verticalOverviewIcon : barHost.leftGroup.overviewIcon; last: host.verticalBar ? barHost.verticalWorkspaces : barHost.leftGroup.workspaceButtonRow }
    IslandSurface { first: host.verticalBar ? barHost.verticalHardware : barHost.leftGroup.hardwareStatus }
    IslandSurface { id: clockPill; first: host.verticalBar ? barHost.verticalCalendarIcon : barHost.centerInfo; grow: "center" }
    IslandSurface { first: host.verticalBar ? barHost.verticalWeatherIcon : barHost.barWeather }
    IslandSurface { first: host.verticalBar ? barHost.verticalMedia : barHost.mediaStrip; shown: host.verticalBar ? barHost.verticalMedia.visible : barHost.mediaStrip.visible; grow: "end" }
    IslandSurface { first: host.verticalBar ? barHost.verticalCapture : barHost.barCapture; shown: host.verticalBar ? barHost.verticalCapture.shown : barHost.barCapture.shown; grow: "end" }
    IslandSurface { first: host.verticalBar ? barHost.verticalEnd : barHost.rightSide; last: host.verticalBar ? barHost.verticalEnd : barHost.notificationIcon; grow: "end" }
    // The pill that is currently grown into a card: it and its icons hide underneath,
    // since a Blur card is see-through.
    readonly property Item cardedPill: {
        // visible, not opened: the pill stays hidden until its card has shrunk back.
        var panel = (barHost.dockPanels || []).find(candidate => (candidate.visible || candidate === barHost.pendingPanel) && candidate.morphPill);
        return panel ? panel.morphPill : null;
    }
    // A card wider than its pill pushes the following pills aside by the overflow.
    function overflow(pill) {
        var panel = (barHost.dockPanels || []).find(candidate => (candidate.opened || candidate === barHost.pendingPanel) && candidate.morphPill === pill);
        if (!panel) return 0;
        return Math.max(0, host.verticalBar ? panel.height - pill.height : panel.width - pill.width);
    }
    property real afterLogo: overflow(logoPill)
    property real afterWorkspaces: overflow(workspacesPill)
    property real aroundClock: overflow(clockPill) / 2
    Behavior on afterLogo { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    Behavior on afterWorkspaces { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    Behavior on aroundClock { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    // The pill whose span holds a bar item; its panel grows out of that pill.
    function pillFor(item) {
        if (!item || !barHost.islandsLayout) return null;
        // Control Center is anchored to the whole strip; it opens from the logo.
        if (item === barHost.stripItem) return logoPill;
        for (var index = 0; index < children.length; index++) {
            var pill = children[index];
            // Not pill.visible: a carded pill hides itself but still owns its card.
            if (pill.itemPosition === undefined || !pill.shown) continue;
            var at = pill.itemPosition(item);
            var start = host.verticalBar ? pill.y : pill.x;
            var end = start + (host.verticalBar ? pill.height : pill.width);
            var along = host.verticalBar ? at.y + item.height / 2 : at.x + item.width / 2;
            if (along >= start && along <= end) return pill;
        }
        return null;
    }
    component IslandSurface: Rectangle {
        required property Item first
        property Item last: first
        property bool shown: true
        property string grow: "start"
        readonly property bool carded: islandSurfaces.cardedPill === this
        visible: barHost.islandsLayout && shown && !carded
        Binding { target: first; property: "opacity"; value: 0; when: carded }
        Binding { target: last; property: "opacity"; value: 0; when: carded && last !== first }
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
        // Pills are always fully rounded, whatever the corner preference.
        radius: Math.min(width, height) / 2
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
