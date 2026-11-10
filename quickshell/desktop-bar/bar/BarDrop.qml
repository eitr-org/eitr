// qmllint disable Quick.property-changes-parsed
import ".."
import QtQuick

// Drop: one full pill with only the time, centred on the bar's edge. With auto-hide nothing
// stays on screen; revealing drops a small drop in the bar's colour out of the edge, which falls into
// place and swells into the time island (hiding plays it backwards). The glance strip
// and the dashboard card come later.
Item {
    id: drop
    required property var host
    required property var barHost
    anchors.fill: parent
    z: 1
    visible: barHost.dropLayout && !FocusMode.enabled
    // Takes the bar's pieces one beat after becoming visible, so a layout switching away
    // (Dynamic and Drop move the same clock) has always given them back first.
    property bool holding: false
    onVisibleChanged: if (!visible) holding = false; else Qt.callLater(() => { drop.holding = drop.visible; })
    Component.onCompleted: holding = visible
    readonly property var surfaces: [pill, dotReach]
    readonly property alias pillSurface: pill
    readonly property bool vertical: host.verticalBar
    readonly property real length: vertical ? height : width
    // The auto-hide slide drives the morph: 0 is the dot, 1 the pill. Its animation
    // already follows Reduce motion, so the pill follows it without easing of its own.
    readonly property real reveal: barHost.autoHideRef.progress
    readonly property real dotSize: 10
    readonly property real clockExtent: vertical ? barHost.verticalCalendarIcon.height : barHost.centerInfo.width
    readonly property real pillExtent: clockExtent + 8
    // The first 40% of the reveal is the fall out of the edge, the rest the swell.
    readonly property real fall: Math.min(1, reveal / 0.4)
    readonly property real swell: Math.max(0, (reveal - 0.4) / 0.6)
    // Falling, the drop is a little longer than wide; swelling, it becomes the pill.
    readonly property real dropAcross: dotSize * 0.8
    readonly property real dropDepth: dotSize * 1.4
    // The time fades in over the second half of the swell, once the pill can hold it.
    readonly property real contentOpacity: Math.max(0, swell * 2 - 1)
    // Like Dynamic's islands, the pill grows into its dashboard card while it is open.
    function islandFor(panel) { return panel === barHost.dropDashboard ? pill : null; }
    function openPanel() {
        const dashboard = barHost.dropDashboard;
        return dashboard && (dashboard.opened || dashboard === barHost.pendingPanel) ? dashboard : null;
    }
    function panelOrigin(panel, stripX, stripY) {
        if (!islandFor(panel) || !panel.parent) return Qt.point(stripX, stripY);
        const origin = drop.mapToItem(panel.parent, 0, 0);
        const start = (drop.length - pill.targetExtent) / 2;
        const offset = pill.farEdge ? pill.thickness - pill.targetDepth : 0;
        return vertical ? Qt.point(origin.x + offset, origin.y + start) : Qt.point(origin.x + start, origin.y + offset);
    }
    DynamicIsland {
        id: pill
        host: drop.host; barHost: drop.barHost
        restingExtent: drop.dropAcross + (drop.pillExtent - drop.dropAcross) * drop.swell
        fullExtent: restingExtent
        restingDepth: drop.dropDepth + (thickness - drop.dropDepth) * drop.swell
        // The auto-hide fall follows the slide exactly; growing into the dashboard eases.
        eased: drop.reveal >= 1
        visible: drop.reveal > 0
        panel: drop.openPanel()
        x: vertical ? depthOffset : (drop.length - width) / 2
        y: vertical ? (drop.length - height) / 2 : depthOffset
        // Falls out of the bar's edge: before the fall it sits just beyond the screen.
        readonly property real travel: (1 - drop.fall) * (thickness + drop.dropDepth) * (farEdge ? 1 : -1)
        transform: Translate { x: drop.vertical ? pill.travel : 0; y: drop.vertical ? 0 : pill.travel }
        // The drop: the bar's colour with a soft halo, becoming the pill as it swells.
        Item {
            id: dot
            objectName: "dropDot"
            anchors.fill: parent
            opacity: Math.max(0, 1 - drop.swell * 1.6)
            visible: opacity > 0
            Canvas {
                id: halo
                readonly property color accent: pill.color
                anchors.centerIn: parent
                width: drop.dotSize * 2.6; height: width
                onAccentChanged: requestPaint()
                onPaint: {
                    const context = getContext("2d");
                    context.reset();
                    const middle = width / 2;
                    const glow = context.createRadialGradient(middle, middle, 0, middle, middle, middle);
                    glow.addColorStop(0, Qt.alpha(accent, 0.55));
                    glow.addColorStop(0.45, Qt.alpha(accent, 0.3));
                    glow.addColorStop(1, Qt.alpha(accent, 0));
                    context.fillStyle = glow;
                    context.fillRect(0, 0, width, height);
                }
            }
            Rectangle { anchors.fill: parent; radius: pill.radius; color: pill.color }
        }
    }
    // A slightly larger target around the dot, from the bar's edge, so the pointer finds
    // it easily; reaching it reveals the bar like the edge sensor does.
    Item {
        id: dotReach
        visible: drop.visible && host.barAutoHide && drop.reveal < 1
        readonly property real along: 28
        readonly property real across: drop.dotSize + 8
        width: vertical ? across : along
        height: vertical ? along : across
        x: vertical ? (pill.farEdge ? drop.width - width : 0) : (drop.width - width) / 2
        y: vertical ? (drop.height - height) / 2 : (pill.farEdge ? drop.height - height : 0)
    }
    // Only the time shows: workspaces, status, media, capture and weather stay hidden
    // until the glance strip brings them back.
    states: [
        State {
            name: "horizontal"; when: drop.holding && !drop.vertical
            PropertyChanges { target: barHost.barHorizontalCenter; parent: pill.content; opacity: drop.contentOpacity; enabled: drop.reveal >= 1 }
            PropertyChanges { target: barHost.centerInfo; timeOnly: true }
            PropertyChanges { target: barHost.leftGroup; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.rightSide; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.notificationIcon; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.barCapture; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.mediaStrip; opacity: 0; enabled: false; audioEnabled: false }
        },
        State {
            name: "vertical"; when: drop.holding && drop.vertical
            PropertyChanges { target: barHost.verticalMiddle; parent: pill.content; opacity: drop.contentOpacity; enabled: drop.reveal >= 1 }
            PropertyChanges { target: barHost.verticalCalendarIcon; timeOnly: true }
            PropertyChanges { target: barHost.verticalStart; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.verticalEnd; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.verticalCapture; opacity: 0; enabled: false }
            PropertyChanges { target: barHost.verticalMedia; visible: false }
        }
    ]
}
