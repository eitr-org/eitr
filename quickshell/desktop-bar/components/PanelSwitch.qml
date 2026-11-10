import ".."
import QtQuick
import QtQuick.Controls.Basic
import "../PanelStyle.js" as PanelStyle

// A Material-style switch: a pill track and a round thumb carrying a check when on and a
// cross when off. The thumb swells while pressed, slides across with a slight overshoot and
// its icon changes with a short fade, with a soft halo on hover.
Switch {
    id: control
    required property color foreground
    required property color accent
    readonly property bool accentIsLight: accent.r * 0.299 + accent.g * 0.587 + accent.b * 0.114 > 0.55
    width: 42
    height: 32
    padding: 0
    // The track ends 4 px inside the control, where rows align their other controls.
    indicator: Item {
        x: 0
        y: (control.height - height) / 2
        width: 38
        height: 24
        opacity: control.enabled ? 1 : 0.45
        Rectangle {
            id: track
            anchors.fill: parent
            radius: height / 2
            color: control.checked ? control.accent : Qt.alpha(control.foreground, 0.12)
            border.width: control.checked ? 0 : 1
            border.color: Qt.alpha(control.foreground, 0.4)
            Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(160) } }
        }
        Item {
            id: thumbSlot
            readonly property real size: control.pressed ? 22 : control.checked ? 20 : 16
            width: 24; height: 24
            x: control.checked ? parent.width - width : 0
            Behavior on x { NumberAnimation { duration: DesktopStyle.motionDuration(220); easing.type: Easing.OutBack; easing.overshoot: 1.4 } }
            Rectangle {
                anchors.centerIn: parent
                width: 34; height: 34; radius: 17
                color: Qt.alpha(control.checked ? control.accent : control.foreground, control.pressed ? 0.2 : 0.1)
                opacity: (hover.hovered || control.pressed || control.visualFocus) && control.enabled ? 1 : 0
                Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
            }
            Rectangle {
                id: thumb
                anchors.centerIn: parent
                width: thumbSlot.size; height: width; radius: width / 2
                color: control.checked ? (control.accentIsLight ? "#1d1d1d" : "#ffffff") : Qt.alpha(control.foreground, 0.62)
                Behavior on width { NumberAnimation { duration: DesktopStyle.motionDuration(140); easing.type: Easing.OutCubic } }
                Behavior on color { ColorAnimation { duration: DesktopStyle.motionDuration(160) } }
                Text {
                    id: glyph
                    anchors.centerIn: parent
                    // md-check and md-close from the Nerd Font icon set.
                    text: control.checked ? "\u{F012C}" : "\u{F0156}"
                    color: control.checked ? control.accent : (control.foreground.hslLightness > 0.5 ? "#1d1d1d" : "#ffffff")
                    font.family: PanelStyle.fontFamily
                    font.pixelSize: control.checked ? 13 : 11
                    onTextChanged: pop.restart()
                    SequentialAnimation {
                        id: pop
                        NumberAnimation { target: glyph; property: "opacity"; to: 0; duration: 0 }
                        ParallelAnimation {
                            NumberAnimation { target: glyph; property: "opacity"; to: 1; duration: DesktopStyle.motionDuration(160) }
                            NumberAnimation { target: glyph; property: "scale"; from: 0.4; to: 1; duration: DesktopStyle.motionDuration(200); easing.type: Easing.OutBack }
                        }
                    }
                }
            }
        }
    }
    HoverHandler { id: hover; cursorShape: Qt.PointingHandCursor }
}
