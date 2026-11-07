import ".."
import QtQuick
Rectangle {
    property color accent: foreground
    property color foreground: "#eeeeee"
    property color muted: Qt.alpha(foreground, 0.72)
    property color raised: Qt.alpha(foreground, 0.08)
    property color gold: foreground
    property color background: "#20242c"
    id: picture
    property string value: "rounded"
    color: picture.background
    Rectangle {
        anchors.fill: parent
        anchors.margins: 12
        radius: (DesktopStyle.styles[picture.value] || {}).windowRounding || 0
        color: picture.raised
        border.width: 1
        border.color: picture.gold
        Rectangle { x: 12; y: 12; width: parent.width - 24; height: 2; color: picture.muted }
    }
}
