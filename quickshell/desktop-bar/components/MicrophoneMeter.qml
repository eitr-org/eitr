import ".."
import Eitr as Eitr
import QtQuick
import "../PanelStyle.js" as PanelStyle

Column {
    id: meter
    required property color foreground
    required property color accent
    property real peak: 0
    property bool muted: false
    spacing: 6
    Text {
        text: meter.muted ? Eitr.I18n.tr("Input level · muted") : Eitr.I18n.tr("Input level")
        color: meter.foreground
        opacity: 0.65
        font.family: DesktopFonts.family
        font.pixelSize: PanelStyle.secondarySize
    }
    Rectangle {
        width: parent.width; height: 8; radius: DesktopStyle.radius(4)
        color: Qt.alpha(meter.foreground, 0.10)
        Rectangle {
            height: parent.height; radius: parent.radius
            width: parent.width * (meter.muted ? 0 : Math.min(1, Math.max(0, meter.peak)))
            color: meter.accent
            Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(80); easing.type: Easing.OutCubic } }
        }
    }
}
