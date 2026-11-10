import ".."
import QtQuick
import QtQuick.Controls.Basic as Controls

// Shared themed slider in the Material style: a thin rail, the filled part in the accent and a
// round thumb with a soft halo on hover and while dragging. A stepped slider with a few
// positions sets ticks to their count, marking each stop with a small dot. With valueText,
// a bubble above the thumb shows the value while dragging.
Controls.Slider {
    id: slider
    required property color accent
    required property color foreground
    property int ticks: 0
    property string valueText: ""
    readonly property real thumbSize: 16
    readonly property bool engaged: pressed || hover.hovered || visualFocus
    height: 30
    HoverHandler {
        id: hover
        cursorShape: slider.enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
    }
    background: Item {
        x: slider.leftPadding
        y: (slider.height - height) / 2
        width: slider.availableWidth
        height: 4
        Rectangle {
            anchors.fill: parent
            radius: 2
            color: Qt.alpha(slider.accent, 0.38)
        }
        Rectangle {
            width: slider.thumbSize / 2 + slider.visualPosition * (parent.width - slider.thumbSize)
            height: parent.height
            radius: 2
            color: slider.accent
        }
        Repeater {
            model: slider.ticks > 1 ? slider.ticks : 0
            Rectangle {
                required property int index
                readonly property real position: index / (slider.ticks - 1)
                // Centred under the thumb at this stop.
                x: slider.thumbSize / 2 + position * (parent.width - slider.thumbSize) - width / 2
                anchors.verticalCenter: parent.verticalCenter
                // Contrast with the part of the track each dot sits on.
                readonly property bool filled: position <= slider.visualPosition + 0.0001
                width: 3
                height: 3
                radius: 1.5
                color: filled ? (slider.accent.hslLightness > 0.55 ? Qt.rgba(0, 0, 0, 0.55) : Qt.rgba(1, 1, 1, 0.8)) : Qt.alpha(slider.foreground, 0.75)
            }
        }
    }
    handle: Item {
        x: slider.leftPadding + slider.visualPosition * (slider.availableWidth - width)
        y: (slider.height - height) / 2
        width: slider.thumbSize
        height: slider.thumbSize
        Rectangle {
            anchors.centerIn: parent
            width: 32; height: 32; radius: 16
            color: Qt.alpha(slider.accent, slider.pressed ? 0.24 : 0.14)
            opacity: slider.engaged && slider.enabled ? 1 : 0
            Behavior on opacity { NumberAnimation { duration: DesktopStyle.motionDuration(120) } }
        }
        Rectangle {
            anchors.fill: parent
            radius: width / 2
            color: slider.accent
        }
        Rectangle {
            id: bubble
            visible: slider.valueText !== "" && slider.pressed
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.top
            anchors.bottomMargin: 10
            width: Math.max(28, bubbleText.implicitWidth + 14)
            height: 24
            radius: DesktopStyle.radius(4)
            color: Qt.rgba(slider.foreground.r * 0.35, slider.foreground.g * 0.35, slider.foreground.b * 0.35, 0.92)
            Text {
                id: bubbleText
                anchors.centerIn: parent
                text: slider.valueText
                color: "white"
                font.family: DesktopFonts.family
                font.pixelSize: 12
            }
        }
    }
}
