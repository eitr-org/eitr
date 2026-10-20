import QtQuick
import QtQuick.Controls.Basic

Switch {
    id: control
    required property color foreground
    required property color accent
    width: 52
    height: 40
    padding: 0
    indicator: Rectangle {
        x: 2
        y: (control.height - height) / 2
        width: 46
        height: 22
        radius: 11
        color: control.checked ? control.accent : Qt.rgba(control.foreground.r, control.foreground.g, control.foreground.b, 0.2)
        opacity: control.enabled ? 1 : 0.45
        Rectangle {
            x: control.checked ? 26 : 2
            y: 2
            width: 18
            height: 18
            radius: 9
            color: control.checked ? (control.accent.r * 0.299 + control.accent.g * 0.587 + control.accent.b * 0.114 > 0.55 ? "#161616" : "#ffffff") : control.foreground
        }
    }
    HoverHandler { cursorShape: Qt.PointingHandCursor }
}
