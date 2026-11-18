import ".."
import QtQuick
import Eitr as Eitr
import "../PanelStyle.js" as PanelStyle

// Full-screen Cleaning mode surface: blurred/tinted backdrop, Escape hold ring,
// and input blockers so clicks, scrolls, and keys cannot reach underlying windows.
Item {
    id: content
    required property color foreground
    required property color background
    required property color accent
    property real holdProgress: 0
    property bool holdingEsc: false
    property bool eatInput: true
    signal escPressed()
    signal escReleased()

    Rectangle {
        anchors.fill: parent
        color: Qt.rgba(content.background.r, content.background.g, content.background.b, 0.78)
        Rectangle {
            anchors.fill: parent
            color: Qt.alpha(content.accent, 0.06)
        }
    }

    Rectangle {
        objectName: "cleanOverlayCard"
        anchors.centerIn: parent
        width: Math.min(440, parent.width - 2 * PanelStyle.padding)
        height: cardLayout.implicitHeight + 2 * 28
        radius: DesktopStyle.radius(PanelStyle.cornerRadius * 2)
        color: Qt.rgba(content.background.r, content.background.g, content.background.b, 0.94)
        border.width: 1
        border.color: Qt.alpha(content.foreground, 0.16)

        Column {
            id: cardLayout
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            anchors.margins: 28
            spacing: 16

            Item {
                anchors.horizontalCenter: parent.horizontalCenter
                width: 96
                height: 96

                ProgressRing {
                    id: ring
                    objectName: "cleanOverlayRing"
                    anchors.fill: parent
                    progress: content.holdProgress
                    animateProgress: false
                    lineWidth: 6
                    trackColor: Qt.alpha(content.foreground, 0.18)
                    accentColor: content.accent
                }

                Text {
                    anchors.centerIn: parent
                    text: "󰃢"
                    color: content.holdingEsc ? content.accent : content.foreground
                    font.family: DesktopFonts.family
                    font.pixelSize: 34
                }
            }

            Text {
                objectName: "cleanOverlayTitle"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: Eitr.I18n.tr("Cleaning mode")
                color: content.foreground
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.headingSize
                font.bold: true
            }

            Text {
                objectName: "cleanOverlayBody"
                width: parent.width
                horizontalAlignment: Text.AlignHCenter
                wrapMode: Text.WordWrap
                text: Eitr.I18n.tr("Keyboard, mouse and touchpad are locked. Hold Esc for 3 seconds to exit.")
                color: content.foreground
                opacity: PanelStyle.secondaryTextOpacity
                font.family: DesktopFonts.family
                font.pixelSize: PanelStyle.bodySize
            }
        }
    }

    MouseArea {
        objectName: "cleanOverlayMouseBlocker"
        anchors.fill: parent
        enabled: content.eatInput
        acceptedButtons: Qt.AllButtons
        hoverEnabled: true
        cursorShape: Qt.BlankCursor
        onPressed: mouse => { mouse.accepted = true; }
        onReleased: mouse => { mouse.accepted = true; }
        onClicked: mouse => { mouse.accepted = true; }
        onDoubleClicked: mouse => { mouse.accepted = true; }
        onPositionChanged: mouse => { mouse.accepted = true; }
        onWheel: wheel => { wheel.accepted = true; }
    }

    Keys.onPressed: event => {
        if (event.key === Qt.Key_Escape && !event.isAutoRepeat)
            content.escPressed();
        event.accepted = true;
    }

    Keys.onReleased: event => {
        if (event.key === Qt.Key_Escape && !event.isAutoRepeat)
            content.escReleased();
        event.accepted = true;
    }
}
