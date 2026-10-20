import QtQuick
import QtQuick.Controls.Basic as Controls

// Shared themed slider track and handle for panel level controls.
Controls.Slider {
    id: slider
    required property color accent
    required property color foreground
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
