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
    // Hover, after a short delay so a passing pointer does not open it, grows the pill
    // into the glance strip: [left icons and workspaces] [media][capture] time+date
    // [weather] [status and notifications]. The middle stays centred as a group.
    readonly property bool glance: pill.expanded && reveal >= 1
    readonly property bool captureShown: vertical ? barHost.verticalCapture.shown : barHost.barCapture.shown
    readonly property real captureLength: captureShown ? (vertical ? barHost.verticalCapture.height + 3 : barHost.barCapture.width + 6) : 0
    readonly property bool mediaAvailable: barHost.mediaStrip.present
    readonly property real mediaLength: mediaAvailable ? (vertical ? barHost.verticalMedia.implicitHeight + 3 : barHost.mediaStrip.width + 12) : 0
    readonly property real weatherExtent: vertical ? barHost.verticalWeatherIcon.height : barHost.barWeather.width
    readonly property real weatherLength: host.workspaceItemSpacing + weatherExtent
    readonly property real middleExtent: clockExtent + 8 + captureLength + mediaLength + weatherLength
    readonly property real leadingExtent: vertical ? barHost.verticalStart.height : barHost.leftGroup.implicitWidth
    readonly property real trailingExtent: vertical ? barHost.verticalEnd.height : barHost.rightSide.width + host.workspaceItemSpacing + barHost.notificationIcon.width
    readonly property real sideExtent: Math.max(leadingExtent, trailingExtent) + 2 * host.workspaceItemSpacing + 4
    readonly property real glanceExtent: Math.min(length - 2 * barHost.islandGap, middleExtent + 2 * sideExtent)
    property real clockShift: glance ? (captureLength + mediaLength - weatherLength) / 2 : captureLength / 2
    Behavior on clockShift { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    property real weatherReveal: glance ? weatherLength : 0
    Behavior on weatherReveal { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    property real sideOpacity: glance ? 1 : 0
    Behavior on sideOpacity { NumberAnimation { duration: DesktopStyle.motionDuration(220) } }
    HoverHandler {
        id: pointer
        onHoveredChanged: Qt.callLater(drop.updateHover)
    }
    readonly property point pointerPosition: pointer.point.position
    onPointerPositionChanged: Qt.callLater(updateHover)
    function updateHover() {
        const inside = pointer.hovered && pointerPosition.x >= pill.x && pointerPosition.x < pill.x + pill.width
            && pointerPosition.y >= pill.y && pointerPosition.y < pill.y + pill.height;
        if (!inside) { hoverDelay.stop(); pill.hovered = false; }
        else if (!pill.hovered && !hoverDelay.running) hoverDelay.start();
    }
    Timer { id: hoverDelay; interval: 180; onTriggered: pill.hovered = drop.reveal >= 1 }
    DynamicIsland {
        id: pill
        host: drop.host; barHost: drop.barHost
        restingExtent: drop.dropAcross + (drop.pillExtent - drop.dropAcross) * drop.swell
        fullExtent: drop.glanceExtent
        restingDepth: drop.dropDepth + (thickness - drop.dropDepth) * drop.swell
        // The auto-hide fall follows the slide exactly; the glance strip eases on its own.
        eased: drop.reveal >= 1
        visible: drop.reveal > 0
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
    // At rest only the time (and the capture dot while recording) shows; the glance strip
    // brings the side groups, media, date and weather in. Plain parent changes, as in Dynamic.
    states: [
        State {
            name: "horizontal"; when: drop.holding && !drop.vertical
            PropertyChanges { target: barHost.barHorizontalCenter; parent: pill.content; opacity: drop.contentOpacity; enabled: drop.reveal >= 1 }
            PropertyChanges { target: barHost.centerInfo; timeOnly: !drop.glance; anchors.horizontalCenterOffset: drop.clockShift }
            PropertyChanges { target: barHost.leftGroup; parent: pill.content; x: 4 + host.workspaceItemSpacing; y: (pill.thickness - barHost.leftGroup.height) / 2 }
            PropertyChanges { target: barHost.leftGroup; width: barHost.leftGroup.implicitWidth; opacity: drop.sideOpacity; enabled: drop.glance }
            PropertyChanges { target: barHost.rightSide; parent: pill.content; opacity: drop.sideOpacity; enabled: drop.glance }
            PropertyChanges { target: barHost.notificationIcon; parent: pill.content }
            PropertyChanges { target: barHost.notificationIcon; anchors.rightMargin: 4 + host.workspaceItemSpacing; opacity: drop.sideOpacity; enabled: drop.glance }
            PropertyChanges { target: barHost.mediaStrip; availableWidth: 280; opacity: drop.glance ? 1 : 0; enabled: drop.glance }
        },
        State {
            name: "vertical"; when: drop.holding && drop.vertical
            PropertyChanges { target: barHost.verticalStart; parent: pill.content; y: 4; opacity: drop.sideOpacity; enabled: drop.glance }
            PropertyChanges { target: barHost.verticalMiddle; parent: pill.content; opacity: drop.contentOpacity; enabled: drop.reveal >= 1 }
            PropertyChanges { target: barHost.verticalCalendarIcon; timeOnly: !drop.glance; anchors.verticalCenterOffset: drop.clockShift }
            PropertyChanges { target: barHost.verticalEnd; parent: pill.content }
            PropertyChanges { target: barHost.verticalEnd; anchors.bottomMargin: 4; opacity: drop.sideOpacity; enabled: drop.glance }
            PropertyChanges { target: barHost.verticalMedia; visible: drop.mediaAvailable && drop.glance }
        }
    ]
}
