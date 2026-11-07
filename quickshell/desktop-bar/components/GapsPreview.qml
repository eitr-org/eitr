import ".."
import QtQuick
Rectangle {
    property color foreground: "#eeeeee"
    property color raised: Qt.alpha(foreground, 0.08)
    property color gold: foreground
    property color accent: foreground
    property color background: "#20242c"
    id: picture
    property var choice: ({inner: 6, outer: 12})
    readonly property real outer: Number(choice.outer ?? 12) * 0.6
    readonly property real inner: Number(choice.inner ?? 6) * 0.6
    color: Qt.tint(picture.background, Qt.alpha(picture.accent, 0.18))
    Repeater {
        model: 3
        Rectangle {
            required property int index
            x: index === 0 ? picture.outer : picture.width / 2 + picture.inner / 2
            y: index < 2 ? picture.outer : picture.height / 2 + picture.inner / 2
            width: (picture.width - 2 * picture.outer - picture.inner) / 2
            height: index === 0 ? picture.height - 2 * picture.outer : (picture.height - 2 * picture.outer - picture.inner) / 2
            radius: Math.min(8, DesktopStyle.radius(2))
            color: picture.raised
            border.color: picture.gold
            border.width: 1
        }
    }
}
