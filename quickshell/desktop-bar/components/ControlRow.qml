import ".."
import QtQuick
import "../PanelStyle.js" as PanelStyle

Rectangle {
    id: row
    required property string text
    required property string description
    required property color foreground
    default property alias control: controlSlot.data
    property real controlWidth: Math.min(320, width * 0.46)
    width: parent ? parent.width : 0
    implicitHeight: Math.max(36, labels.implicitHeight + 8, controlSlot.childrenRect.height + 8)
    height: visible ? implicitHeight : 0
    radius: DesktopStyle.radius(4)
    color: Qt.alpha(foreground, hover.hovered ? 0.04 : 0)
    HoverHandler {
        id: hover
    }
    Column {
        id: labels
        x: 4
        width: Math.max(0, row.width - row.controlWidth - 20)
        anchors.verticalCenter: parent.verticalCenter
        spacing: PanelStyle.selectionDetailGap
        Text {
            width: parent.width
            text: row.text
            color: row.foreground
            font.family: DesktopFonts.family
            font.pixelSize: 11
            wrapMode: Text.WordWrap
        }
        Text {
            width: parent.width
            visible: text !== ""
            text: row.description
            color: row.foreground
            opacity: PanelStyle.secondaryTextOpacity
            font.family: DesktopFonts.family
            font.pixelSize: 13
            wrapMode: Text.WordWrap
        }
    }
    Item {
        id: controlSlot
        readonly property var settingTargetOwner: row
        width: row.controlWidth
        height: childrenRect.height
        anchors.right: parent.right
        anchors.verticalCenter: parent.verticalCenter
    }
}
