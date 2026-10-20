import QtQuick
import QtTest
import ".."

TestCase {
    name: "PanelResize"
    Item {
        id: panel
        property bool opened: false
        property real revealProgress: 1
        property int transitionDuration: 320
        property real desiredWidth: 200
        property real desiredHeight: 200
        width: desiredWidth; height: desiredHeight
        PanelSizeBehavior on width { ownerPanel: panel }
        PanelSizeBehavior on height { ownerPanel: panel }
    }
    function init() {
        panel.opened = false;
        panel.revealProgress = 1;
        panel.desiredWidth = 200;
        panel.desiredHeight = 200;
    }
    function test_grow_and_shrink() {
        panel.opened = true;
        panel.desiredHeight = 500;
        panel.desiredWidth = 400;
        wait(100);
        verify(panel.height > 200 && panel.height < 500);
        verify(panel.width > 200 && panel.width < 400);
        tryCompare(panel, "height", 500);
        tryCompare(panel, "width", 400);
        panel.desiredHeight = 200;
        wait(100);
        verify(panel.height > 200 && panel.height < 500);
        tryCompare(panel, "height", 200);
    }
    function test_no_resize_animation_while_closed_or_unfolding() {
        panel.desiredHeight = 500;
        compare(panel.height, 500);
        panel.opened = true;
        panel.revealProgress = 0.5;
        panel.desiredHeight = 200;
        compare(panel.height, 200);
    }
}
