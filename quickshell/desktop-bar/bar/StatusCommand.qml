import ".."
import QtQuick

Item {
    id: item
    property var host

    property string hoverLabel: ""
    property bool clickable: false
    signal clicked()
    property bool open: true
    property string text: ""
    property int slotWidth: 44
    property int fixedWidth: 0
    property int fontSize: 13

    width: open ? (fixedWidth > 0 ? fixedWidth : Math.max(slotWidth, label.implicitWidth + 8)) : 0
    height: 24
    opacity: open ? 1 : 0
    clip: true

    Text {
        id: label

        anchors.centerIn: parent
        text: item.text
        textFormat: Text.RichText
        color: host.fg
        font.family: DesktopFonts.family
        font.pixelSize: item.fontSize
        font.bold: true
    }

    MouseArea {
        id: commandMouse
        anchors.fill: parent
        enabled: item.open && item.clickable
        hoverEnabled: true
        cursorShape: enabled ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: item.clicked()
    }

    BarTooltip {
        background: host.workspaceMenuBg
        foreground: host.fg
        target: item
        hovered: commandMouse.containsMouse && item.open
        text: item.hoverLabel
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
