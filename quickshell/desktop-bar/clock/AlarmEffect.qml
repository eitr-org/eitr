import ".."
import QtQuick

Item {
    id: effect
    required property color accent
    Rectangle {
        anchors.centerIn: parent
        width: Math.min(parent.width, parent.height) * 0.70
        height: width
        radius: width / 2
        color: Qt.alpha(effect.accent, 0.07)
        border.color: Qt.alpha(effect.accent, 0.17)
        opacity: 0.8
        SequentialAnimation on opacity {
            running: effect.visible && !DesktopStyle.reduceMotion
            loops: Animation.Infinite
            NumberAnimation { from: 0.55; to: 1; duration: 2200; easing.type: Easing.InOutSine }
            NumberAnimation { from: 1; to: 0.55; duration: 2200; easing.type: Easing.InOutSine }
        }
    }
}
