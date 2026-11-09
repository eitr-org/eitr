import ".."
import QtQuick
import QtQuick.Controls.Basic as Controls

// Shared themed slider track and handle for panel level controls. A stepped slider with a
// few positions sets ticks to their count, marking each stop where the handle can rest.
Controls.Slider {
    id: slider
    required property color accent
    required property color foreground
    property int ticks: 0
    height: 30
    HoverHandler {
        cursorShape: slider.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    background: Rectangle {
        x: slider.leftPadding
        y: (slider.height - height) / 2
        width: slider.availableWidth
        height: 5
        radius: 3
        color: Qt.rgba(slider.foreground.r, slider.foreground.g, slider.foreground.b, 0.16)
        Rectangle {
            width: slider.visualPosition * parent.width
            height: parent.height
            radius: 3
            color: slider.accent
        }
        Repeater {
            model: slider.ticks > 1 ? slider.ticks : 0
            Rectangle {
                required property int index
                readonly property real position: index / (slider.ticks - 1)
                // Centred under the handle at this stop (the handle is 12 px wide).
                x: position * (parent.width - 12) + 6 - width / 2
                anchors.verticalCenter: parent.verticalCenter
                width: 2
                height: 11
                radius: 1
                color: position <= slider.visualPosition + 0.0001 ? slider.accent : Qt.alpha(slider.foreground, 0.35)
            }
        }
    }
    handle: Rectangle {
        x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
        y: (slider.height - height) / 2
        width: 12
        height: 12
        radius: DesktopStyle.radius(6)
        color: slider.foreground
    }
}
