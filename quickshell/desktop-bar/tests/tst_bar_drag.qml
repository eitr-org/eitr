import QtQuick
import QtTest
import ".."

TestCase {
    name: "BarDragInputCapture"
    width: 900
    height: 600
    visible: true
    when: windowShown
    Item {
        id: host
        anchors.fill: parent
        property var contentItem: host
        property var screen: ({width: 900, height: 600})
        BarGestureArea {
            id: gestures
            width: 900
            height: 30
            hostWindow: host
            edge: "top"
        }
    }
    SignalSpy { id: held; target: gestures; signalName: "pointerHeld" }
    SignalSpy { id: drop; target: gestures; signalName: "dropped" }
    function test_capture_begins_before_leaving_bar() {
        held.clear(); drop.clear();
        mousePress(gestures, 450, 15, Qt.LeftButton);
        compare(held.signalArguments[0][0], true);
        mouseMove(host, 450, 580);
        mouseRelease(host, 450, 580, Qt.LeftButton);
        compare(drop.signalArguments[0][0], "bottom");
        compare(held.signalArguments[held.count - 1][0], false);
        compare(gestures.dragging, false);
    }
    function test_right_press_does_not_capture_desktop() {
        held.clear();
        mousePress(gestures, 450, 15, Qt.RightButton);
        compare(held.signalArguments[0][0], false);
        mouseRelease(gestures, 450, 15, Qt.RightButton);
    }
}
