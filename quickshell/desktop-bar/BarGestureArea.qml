import QtQuick
import "BarGeometry.js" as Geometry

MouseArea {
    id: gestures
    required property var hostWindow
    required property string edge
    property point pressPoint: Qt.point(0, 0)
    property bool dragging: false
    property string candidate: ""
    signal doubleTapped(int button)
    signal dropped(string edge)
    signal pointerHeld(bool held)

    acceptedButtons: Qt.LeftButton | Qt.RightButton
    cursorShape: dragging ? Qt.ClosedHandCursor : Qt.ArrowCursor
    preventStealing: true
    // Expand the host input region immediately on press, before movement can
    // leave the narrow bar and be routed to an empty workspace underneath.
    onPressedChanged: pointerHeld(pressed && (pressedButtons & Qt.LeftButton))

    function updateCandidate(x, y) {
        var point = mapToItem(hostWindow.contentItem, x, y);
        var screen = hostWindow.screen;
        var local = Geometry.screenPoint(point, edge, screen.width, screen.height, hostWindow.width, hostWindow.height);
        candidate = Geometry.nearestEdge(local, screen.width, screen.height);
    }

    onPressed: function(mouse) {
        pressPoint = Qt.point(mouse.x, mouse.y);
        dragging = false;
        candidate = "";
    }
    onPositionChanged: function(mouse) {
        if (!(mouse.buttons & Qt.LeftButton)) return;
        if (!dragging && Math.hypot(mouse.x - pressPoint.x, mouse.y - pressPoint.y) < 24) return;
        dragging = true;
        updateCandidate(mouse.x, mouse.y);
    }
    onReleased: function(mouse) {
        if (!dragging) return;
        updateCandidate(mouse.x, mouse.y);
        var selected = candidate;
        candidate = "";
        dragging = false;
        dropped(selected);
    }
    onCanceled: { candidate = ""; dragging = false; }
    onDoubleClicked: function(mouse) { if (!dragging) doubleTapped(mouse.button); }
}
