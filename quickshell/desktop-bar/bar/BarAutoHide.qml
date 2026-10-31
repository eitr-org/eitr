import ".."
import QtQuick

Item {
    id: controller
    property bool autoHide: false
    property bool pointerInside: false
    property bool held: false
    property bool revealed: true
    readonly property bool shown: !autoHide || pointerInside || held || revealed
    property real progress: shown ? 1 : 0
    Behavior on progress { NumberAnimation { duration: DesktopStyle.motionDuration(320); easing.type: Easing.OutCubic } }
    function reconsider() {
        if (!autoHide || pointerInside || held) {
            hideDelay.stop();
            revealed = true;
        } else hideDelay.restart();
    }
    onAutoHideChanged: reconsider()
    onPointerInsideChanged: reconsider()
    onHeldChanged: reconsider()
    Component.onCompleted: reconsider()
    Timer {
        id: hideDelay
        interval: 350
        onTriggered: if (controller.autoHide && !controller.pointerInside && !controller.held) controller.revealed = false
    }
}
