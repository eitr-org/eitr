import QtQuick
import Eitr as Eitr

Rectangle {
    id: picker
    required property var controller
    property real unit: 1
    property bool showHint: true
    property color ink: "#ffffff"
    property color surface: "#202126"
    visible: controller.canPickUser
    width: Math.min(parent.width - 48, 380)
    height: visible ? (showHint ? 56 : 38) * unit : 0
    property real cornerRadius: 12 * unit
    radius: cornerRadius
    color: surface
    border.color: Qt.alpha(ink, 0.3)
    objectName: "userPicker"
    Text {
        anchors.fill: parent; anchors.margins: 10 * picker.unit; anchors.bottomMargin: (picker.showHint ? 23 : 10) * picker.unit
        text: "‹   " + picker.controller.userName + "   ›"
        color: picker.ink; font.family: "JetBrainsMono Nerd Font"; font.pixelSize: 13 * picker.unit
        horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter
        elide: Text.ElideMiddle
    }
    MouseArea {
        anchors.fill: parent; cursorShape: Qt.PointingHandCursor
        onClicked: mouse => picker.controller.cycleUser(mouse.x < width / 2 ? -1 : 1)
    }
    Shortcut { sequence: "Ctrl+Right"; enabled: picker.visible; onActivated: picker.controller.cycleUser() }
    Shortcut { sequence: "Ctrl+Left"; enabled: picker.visible; onActivated: picker.controller.cycleUser(-1) }
    Text {
        visible: picker.showHint
        anchors.bottom: parent.bottom; anchors.bottomMargin: 7 * picker.unit; width: parent.width
        text: Eitr.I18n.tr("Choose user · Ctrl+Left / Ctrl+Right")
        color: picker.ink; font.pixelSize: 9 * picker.unit; horizontalAlignment: Text.AlignHCenter
        fontSizeMode: Text.HorizontalFit; minimumPixelSize: 7 * picker.unit
    }
}
