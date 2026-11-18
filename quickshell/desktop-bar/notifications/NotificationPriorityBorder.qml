import ".."
import QtQuick

// A 1 px outline in the theme accent for normal notifications and in the theme's
// critical colour for critical ones; low-priority notifications have none.
Rectangle {
    property int urgency: 1
    property color accent: "white"
    property bool shown: true
    property real cornerRadius: 6
    readonly property bool active: shown && urgency >= 1
    radius: cornerRadius
    color: "transparent"
    antialiasing: true
    border.width: active ? 1 : 0
    border.color: urgency === 2 ? DesktopStyle.criticalColor : accent
}
