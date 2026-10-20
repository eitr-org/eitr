import QtQuick
import QtTest
import ".." as DesktopBar

TestCase {
    id: testCase
    name: "BarGestures"
    when: windowShown
    width: 400
    height: 300
    visible: true

    DesktopBar.BarGestureArea {
        id: area
        readonly property bool vertical: edge === "left" || edge === "right"
        width: vertical ? 30 : parent.width
        height: vertical ? parent.height : 30
        x: edge === "right" ? parent.width - width : 0
        y: edge === "bottom" ? parent.height - height : 0
        edge: "bottom"
        hostWindow: ({contentItem: area, width: area.width, height: area.height, screen: {width: 400, height: 300}})
    }
    SignalSpy { id: dropSpy; target: area; signalName: "dropped" }
    SignalSpy { id: doubleSpy; target: area; signalName: "doubleTapped" }

    function init() { area.edge = "top"; dropSpy.clear(); doubleSpy.clear(); }

    function test_bottom_to_top() {
        area.edge = "bottom";
        mousePress(area, 200, 15, Qt.LeftButton);
        compare(area.pressed, true);
        mouseMove(area, 200, -250, 20);
        wait(20);
        compare(area.dragging, true);
        mouseRelease(area, 200, -250, Qt.LeftButton);
        compare(dropSpy.count, 1);
        compare(dropSpy.signalArguments[0][0], "top");
        compare(area.candidate, "");
    }

    function test_top_to_bottom() {
        area.edge = "top";
        mousePress(area, 200, 15, Qt.LeftButton);
        compare(area.pressed, true);
        mouseMove(area, 200, 270, 20);
        wait(20);
        compare(area.dragging, true);
        mouseRelease(area, 200, 270, Qt.LeftButton);
        compare(dropSpy.count, 1);
        compare(dropSpy.signalArguments[0][0], "bottom");
    }

    function test_small_move_keeps_edge() {
        mousePress(area, 200, 15, Qt.LeftButton);
        mouseMove(area, 202, 16);
        mouseRelease(area, 202, 16, Qt.LeftButton);
        compare(dropSpy.count, 0);
    }

    function test_right_to_left() {
        area.edge = "right";
        mousePress(area, 15, 150, Qt.LeftButton);
        mouseMove(area, -350, 150, 20);
        wait(20);
        mouseRelease(area, -350, 150, Qt.LeftButton);
        compare(dropSpy.count, 1);
        compare(dropSpy.signalArguments[0][0], "left");
    }

    function test_left_to_right() {
        area.edge = "left";
        mousePress(area, 15, 150, Qt.LeftButton);
        mouseMove(area, 380, 150, 20);
        wait(20);
        mouseRelease(area, 380, 150, Qt.LeftButton);
        compare(dropSpy.count, 1);
        compare(dropSpy.signalArguments[0][0], "right");
    }
}
