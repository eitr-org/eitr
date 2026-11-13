import ".."
import QtQuick

// A soft halo that slowly grows and fades around a recording dot. Place it behind the dot,
// centred on it; it stays still while paused and with Reduce motion.
Item {
    id: glow
    property real dotSize: 6
    property color color: "#e05c68"
    property bool active: true
    readonly property bool animating: active && visible && DesktopStyle.motionDuration(1) > 0
    width: dotSize; height: dotSize

    Rectangle {
        id: halo
        anchors.centerIn: parent
        width: glow.dotSize; height: glow.dotSize
        radius: width / 2
        color: glow.color
        opacity: 0
        scale: 1
    }
    SequentialAnimation {
        running: glow.animating
        loops: Animation.Infinite
        onRunningChanged: if (!running) { halo.scale = 1; halo.opacity = 0; }
        ParallelAnimation {
            NumberAnimation { target: halo; property: "scale"; from: 1; to: 2.4; duration: 1400; easing.type: Easing.OutSine }
            NumberAnimation { target: halo; property: "opacity"; from: 0.45; to: 0; duration: 1400; easing.type: Easing.OutSine }
        }
        PauseAnimation { duration: 300 }
    }
}
