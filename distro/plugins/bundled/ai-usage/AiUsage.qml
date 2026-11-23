import QtQuick

Item {
    required property var api
    implicitWidth: 24
    implicitHeight: 24
    TapHandler { onTapped: parent.api.openPanel("limits") }
    Text {
        anchors.centerIn: parent
        text: parent.api.icon
        color: parent.api.foreground
        font.family: parent.api.fontFamily
        font.pixelSize: 16
    }
}
