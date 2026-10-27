import QtQuick

Item {
    required property var api
    implicitWidth: 24; implicitHeight: 24
    Rectangle {
        anchors.centerIn: parent; width: 8; height: 8; radius: 4
        color: api.accent
    }
}
