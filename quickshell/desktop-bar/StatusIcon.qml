import QtQuick
import QtQuick.Effects

Item {
    id: item
    property var host

    property string icon: ""
    // An SVG drawn instead of the glyph, tinted with the bar's foreground.
    property url iconSource: ""
    property string tooltip: ""
    property bool open: true
    property bool clickable: false
    property bool rightClickable: false
    property int iconSize: 15
    property int glyphOffsetY: 0
    property int slotWidth: host.workspaceItemSize
    property bool spinning: false

    signal clicked(int button)

    width: open ? slotWidth : 0
    height: 24
    opacity: open ? 1 : 0
    clip: true

    Row {
        id: content

        anchors.centerIn: parent
        spacing: 3
        leftPadding: 4
        rightPadding: 4

        Image {
            visible: item.iconSource != ""
            anchors.verticalCenter: parent.verticalCenter
            width: item.iconSize; height: item.iconSize
            source: item.iconSource
            // Drawn at its shown size: scaling a larger render down leaves jagged edges.
            sourceSize: Qt.size(Math.ceil(width * Screen.devicePixelRatio), Math.ceil(height * Screen.devicePixelRatio))
            smooth: true
            layer.enabled: visible
            layer.effect: MultiEffect { colorization: 1; colorizationColor: host.fg }
        }
        Text {
            id: glyph
            visible: item.iconSource == ""
            text: item.icon
            y: item.glyphOffsetY
            color: host.fg
            font.family: DesktopFonts.family
            font.pixelSize: item.iconSize
            font.bold: true

            // Spin around the glyph's drawn centre; the text box centre sits above it.
            transform: Rotation {
                id: spin
                origin.x: glyphInk.tightBoundingRect.x + glyphInk.tightBoundingRect.width / 2
                origin.y: glyph.baselineOffset + glyphInk.tightBoundingRect.y + glyphInk.tightBoundingRect.height / 2

                NumberAnimation on angle {
                    running: !DesktopStyle.reduceMotion && (item.spinning)
                    from: 0; to: 360
                    duration: 1200
                    loops: Animation.Infinite
                    onStopped: spin.angle = 0
                }
            }

            TextMetrics {
                id: glyphInk
                font: glyph.font
                text: glyph.text
            }
        }

    }

    MouseArea {
        id: iconMouse
        anchors.fill: parent
        enabled: item.open && item.clickable
        acceptedButtons: item.rightClickable ? Qt.LeftButton | Qt.RightButton : Qt.LeftButton
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: function(event) { item.clicked(event.button); }
    }

    BarTooltip {
        background: host.workspaceMenuBg
        foreground: host.fg
        target: item
        hovered: iconMouse.containsMouse && item.open
        text: item.tooltip
    }

    Behavior on width {
        NumberAnimation {
            duration: DesktopStyle.motionDuration(180)
            easing.type: Easing.InOutCubic
        }

    }

    Behavior on opacity {
        NumberAnimation {
            duration: DesktopStyle.motionDuration(120)
            easing.type: Easing.InOutCubic
        }

    }

}
