import ".."
import QtQuick
import QtQuick.Controls.Basic

// The Handbook reading area's scroll bar for long chapters: always shown while
// the content is taller than its view, wide enough to grab and drag, stronger on hover.
ScrollBar {
    id: bar
    required property color foreground
    readonly property bool needed: size < 1
    policy: needed ? ScrollBar.AlwaysOn : ScrollBar.AlwaysOff
    width: 10
    padding: 2
    minimumSize: 0.08
    background: Rectangle {
        radius: width / 2
        color: Qt.alpha(bar.foreground, bar.hovered || bar.pressed ? 0.08 : 0.04)
    }
    contentItem: Rectangle {
        implicitWidth: 6
        radius: width / 2
        color: Qt.alpha(bar.foreground, bar.pressed ? 0.55 : bar.hovered ? 0.42 : 0.28)
    }
}
